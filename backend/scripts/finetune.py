"""
Fine-tune intfloat/multilingual-e5-large with LoRA for hadith retrieval.

Modes:
  triplet  — LLM-graded qrels -> (query, positive hadith) pairs
  kv_pairs — verified KV pairs -> (concept, hadith) pairs for cross-concept alignment
  combined — both datasets merged

Loss: Multiple Negative Ranking Loss (MNRL) with in-batch negatives
Split: 85/15 train/val with early stopping
"""

import os
import json
import sqlite3
import random
import argparse
import math
from datetime import datetime

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from peft import LoraConfig, get_peft_model

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPTS_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

MODEL_NAME = "intfloat/multilingual-e5-large"
MAX_LENGTH = 512

LORA_R = int(os.getenv("LORA_R", "16"))
LORA_ALPHA = int(os.getenv("LORA_ALPHA", "32"))
LORA_DROPOUT = float(os.getenv("LORA_DROPOUT", "0.1"))

BATCH_SIZE = int(os.getenv("FINETUNE_BATCH_SIZE", "16"))
LEARNING_RATE = float(os.getenv("FINETUNE_LR", "2e-5"))
EPOCHS = int(os.getenv("FINETUNE_EPOCHS", "20"))
PATIENCE = int(os.getenv("FINETUNE_PATIENCE", "3"))
VAL_SPLIT = float(os.getenv("FINETUNE_VAL_SPLIT", "0.15"))
TEMPERATURE = float(os.getenv("MNRL_TEMPERATURE", "0.05"))
SEED = int(os.getenv("FINETUNE_SEED", "42"))

OUTPUT_DIR = os.path.join(DATA_DIR, "finetuned")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_hadith_texts(language, hadith_ids):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    col = "Arabic_Text" if language == "AR" else "English_Text"
    placeholders = ",".join("?" * len(hadith_ids))
    cursor.execute(
        f"SELECT id, {col} FROM hadiths WHERE id IN ({placeholders})",
        hadith_ids,
    )
    texts = {row[0]: row[1] for row in cursor.fetchall() if row[1]}
    conn.close()
    return texts


def load_triplet_data():
    """Load (query, positive hadith) pairs from LLM-graded training qrels."""
    qrels_path = os.path.join(DATA_DIR, "training_qrels_graded.json")
    queries_path = os.path.join(DATA_DIR, "training_queries.json")

    if not os.path.exists(qrels_path):
        raise FileNotFoundError(f"Training qrels not found: {qrels_path}")
    if not os.path.exists(queries_path):
        raise FileNotFoundError(f"Training queries not found: {queries_path}")

    with open(qrels_path, encoding="utf-8") as f:
        qrels = json.load(f)
    with open(queries_path, encoding="utf-8") as f:
        queries = json.load(f)

    pairs = []
    for qid, grades in qrels.items():
        if qid not in queries:
            continue
        query_text = queries[qid]
        language = "AR" if qid.startswith("AR") else "EN"

        hadith_ids = [int(hid) for hid in grades.keys()]
        texts = _load_hadith_texts(language, hadith_ids)

        for hid_str, grade in grades.items():
            hid = int(hid_str)
            if hid not in texts:
                continue
            if grade >= 1:
                prefix = "query: "
                if language == "AR":
                    from scripts.preprocess import normalize_arabic_text
                    from camel_tools.utils.dediac import dediac_ar
                    anchor = f"query: {normalize_arabic_text(dediac_ar(query_text))}"
                else:
                    anchor = f"query: {query_text}"
                positive = f"passage: {texts[hid]}"
                pairs.append((anchor, positive, qid))

    return pairs


def load_kv_data():
    """Load (concept, hadith) pairs from verified KV pairs."""
    kv_path = os.path.join(DATA_DIR, "kv_pairs_verified.json")

    if not os.path.exists(kv_path):
        raise FileNotFoundError(f"Verified KV pairs not found: {kv_path}")

    with open(kv_path, encoding="utf-8") as f:
        kv_pairs = json.load(f)

    pairs = []
    for kv in kv_pairs:
        concept_en = kv.get("concept_en", "").strip()
        concept_ar = kv.get("concept_ar", "").strip()
        hadith_en = kv.get("hadith_en", "").strip()
        hadith_ar = kv.get("hadith_ar", "").strip()

        if concept_en and hadith_en:
            pairs.append((
                f"query: {concept_en}",
                f"passage: {hadith_en}",
                f"kv_{kv.get('id', 0)}_en",
            ))
        if concept_ar and hadith_ar:
            from scripts.preprocess import normalize_arabic_text
            from camel_tools.utils.dediac import dediac_ar
            normalized_ar = normalize_arabic_text(dediac_ar(concept_ar))
            pairs.append((
                f"query: {normalized_ar}",
                f"passage: {hadith_ar}",
                f"kv_{kv.get('id', 0)}_ar",
            ))

    return pairs


def load_combined_data():
    """Load both triplet and KV pair data."""
    triplet = load_triplet_data()
    kv = load_kv_data()
    return triplet + kv


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def mean_pool(last_hidden_state, attention_mask):
    mask = attention_mask.unsqueeze(-1).float()
    sum_embeddings = (last_hidden_state * mask).sum(1)
    sum_mask = mask.sum(1).clamp(min=1e-9)
    return sum_embeddings / sum_mask


def encode_texts(model, tokenizer, texts, device, max_length=MAX_LENGTH):
    batch = tokenizer(
        texts,
        max_length=max_length,
        padding=True,
        truncation=True,
        return_tensors="pt",
    ).to(device)
    outputs = model(**batch)
    embeddings = mean_pool(outputs.last_hidden_state, batch["attention_mask"])
    embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings


def mnrl_loss(anchor_embs, positive_embs, temperature=TEMPERATURE):
    """Multiple Negative Ranking Loss with in-batch negatives."""
    sim = anchor_embs @ positive_embs.T / temperature
    labels = torch.arange(sim.size(0), device=sim.device)
    return F.cross_entropy(sim, labels)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class PairDataset(Dataset):
    def __init__(self, pairs):
        self.anchors = [p[0] for p in pairs]
        self.positives = [p[1] for p in pairs]

    def __len__(self):
        return len(self.anchors)

    def __getitem__(self, idx):
        return self.anchors[idx], self.positives[idx]


def collate_fn(batch):
    anchors = [item[0] for item in batch]
    positives = [item[1] for item in batch]
    return anchors, positives


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(mode, output_dir=OUTPUT_DIR, epochs=EPOCHS, batch_size=BATCH_SIZE,
          lr=LEARNING_RATE, patience=PATIENCE, seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    print(f"=== LoRA Fine-tuning ({mode}) ===")
    print(f"Model: {MODEL_NAME}")
    print(f"LoRA: r={LORA_R}, alpha={LORA_ALPHA}, dropout={LORA_DROPOUT}")
    print(f"Batch size: {batch_size}, LR: {lr}, Epochs: {epochs}")
    print(f"Temperature: {TEMPERATURE}, Patience: {patience}")
    print(f"Seed: {seed}")
    print()

    # Load data
    print("Loading training data...")
    if mode == "triplet":
        pairs = load_triplet_data()
    elif mode == "kv_pairs":
        pairs = load_kv_data()
    elif mode == "combined":
        pairs = load_combined_data()
    else:
        raise ValueError(f"Unknown mode: {mode}")

    print(f"Total pairs: {len(pairs)}")

    random.shuffle(pairs)
    val_size = max(1, int(len(pairs) * VAL_SPLIT))
    val_pairs = pairs[:val_size]
    train_pairs = pairs[val_size:]
    print(f"Train: {len(train_pairs)}, Val: {len(val_pairs)}")

    train_dataset = PairDataset(train_pairs)
    val_dataset = PairDataset(val_pairs)

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        collate_fn=collate_fn, drop_last=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        collate_fn=collate_fn, drop_last=False,
    )

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == "cpu":
        print("WARNING: Training on CPU will be very slow.")

    # Load model
    print("Loading base model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    base_model = AutoModel.from_pretrained(MODEL_NAME)

    # Apply LoRA
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=["query", "value"],
        bias="none",
        task_type="FEATURE_EXTRACTION",
    )
    model = get_peft_model(base_model, lora_config)
    model.to(device)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"Trainable params: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=lr,
    )

    # Output dir
    mode_dir = os.path.join(output_dir, mode)
    os.makedirs(mode_dir, exist_ok=True)

    # Training loop
    best_val_loss = float("inf")
    patience_counter = 0
    history = []

    for epoch in range(1, epochs + 1):
        # Train
        model.train()
        train_loss_sum = 0.0
        train_batches = 0

        for batch_idx, (anchors, positives) in enumerate(train_loader):
            optimizer.zero_grad()

            anchor_embs = encode_texts(model, tokenizer, anchors, device)
            positive_embs = encode_texts(model, tokenizer, positives, device)

            loss = mnrl_loss(anchor_embs, positive_embs)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad], 1.0,
            )
            optimizer.step()

            train_loss_sum += loss.item()
            train_batches += 1

            if (batch_idx + 1) % 10 == 0:
                print(f"  Epoch {epoch} [{batch_idx+1}/{len(train_loader)}] "
                      f"loss={loss.item():.4f}")

        avg_train_loss = train_loss_sum / max(train_batches, 1)

        # Validate
        model.eval()
        val_loss_sum = 0.0
        val_batches = 0

        with torch.no_grad():
            for anchors, positives in val_loader:
                anchor_embs = encode_texts(model, tokenizer, anchors, device)
                positive_embs = encode_texts(model, tokenizer, positives, device)
                loss = mnrl_loss(anchor_embs, positive_embs)
                val_loss_sum += loss.item()
                val_batches += 1

        avg_val_loss = val_loss_sum / max(val_batches, 1)

        print(f"Epoch {epoch}/{epochs} — "
              f"train_loss={avg_train_loss:.4f}, val_loss={avg_val_loss:.4f}")

        history.append({
            "epoch": epoch,
            "train_loss": avg_train_loss,
            "val_loss": avg_val_loss,
        })

        # Early stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            print(f"  New best val loss: {best_val_loss:.4f} — saving adapter")
            model.save_pretrained(mode_dir)
            tokenizer.save_pretrained(mode_dir)
        else:
            patience_counter += 1
            print(f"  No improvement ({patience_counter}/{patience})")
            if patience_counter >= patience:
                print(f"  Early stopping at epoch {epoch}")
                break

    # Save training history
    history_path = os.path.join(mode_dir, "training_history.json")
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump({
            "mode": mode,
            "model": MODEL_NAME,
            "lora_r": LORA_R,
            "lora_alpha": LORA_ALPHA,
            "lora_dropout": LORA_DROPOUT,
            "batch_size": batch_size,
            "learning_rate": lr,
            "temperature": TEMPERATURE,
            "train_pairs": len(train_pairs),
            "val_pairs": len(val_pairs),
            "best_val_loss": best_val_loss,
            "epochs_run": len(history),
            "history": history,
        }, f, indent=2)

    print(f"\nDone. Best val loss: {best_val_loss:.4f}")
    print(f"Adapter saved to: {mode_dir}")
    print(f"History saved to: {history_path}")

    return mode_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LoRA fine-tuning for multilingual-e5-large"
    )
    parser.add_argument(
        "--mode", choices=["triplet", "kv_pairs", "combined"],
        default="combined",
        help="Training mode (default: combined)",
    )
    parser.add_argument(
        "--output-dir", default=OUTPUT_DIR,
        help="Output directory for adapter weights",
    )
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=LEARNING_RATE)
    parser.add_argument("--patience", type=int, default=PATIENCE)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    train(
        mode=args.mode,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        patience=args.patience,
        seed=args.seed,
    )
