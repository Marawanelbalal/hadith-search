# Hadith Search Engine

A full-stack hadith search engine supporting both English and Arabic queries with multiple ranking algorithms.

## Prerequisites

- Python 3.10+
- Node.js 18+
- CUDA-capable GPU (recommended for embedding generation — CPU fallback available but very slow)

## Setup

```bash
# Backend
python -m venv venv
# On Windows: venv\Scripts\activate
# On Linux/Mac: source venv/bin/activate
cd backend
pip install -r ..\requirements.txt
mkdir data
```

### External Data Downloads

These must be run **after** `pip install`:

```bash
# NLTK data (tokenization, stopwords, lemmatization, POS tagging)
python -m nltk.downloader punkt_tab stopwords wordnet averaged_perceptron_tagger averaged_perceptron_tagger_eng

# CAMeL Tools data (calima-msa-r13 MLE disambiguator + morphology DB)
camel_data -i disambig-mle-calima-msa-r13
```

### Environment Variables

| Variable | Required For | Description |
|----------|-------------|-------------|
| `JINA_API_KEY` | Cross-encoder reranker & final pipeline | Jina AI API key for `jina-reranker-v3`. Not needed for the build pipeline or basic search. |

Create a `.env` file in the project root:
```
JINA_API_KEY="your_key_here"
```

### Frontend

```bash
cd frontend
npm install
```

## Build Pipeline

Run all steps in sequence with a single command:

```bash
cd backend
python scripts\build_all.py
```

The script will:
1. Check if each step's output already exists and prompt you to overwrite, skip, or quit
2. Run each step with timing and error reporting
3. Stop on the first failure

### Individual Steps

You can also run steps individually:

| Step | Command | Description | Output |
|------|---------|-------------|--------|
| 1 | `python scripts\data_creation.py` | Downloads the hadith dataset from HuggingFace and creates the SQLite database | `backend/data/hadiths.db` |
| 2 | `python scripts\preprocess.py` | Tokenizes, lemmatizes, and removes stopwords for English and Arabic text | Adds `Preprocessed_English` and `Preprocessed_Arabic` columns to the DB |
| 3 | `python scripts\build_inverted_index.py` | Builds BM25 inverted indices and computes document lengths | `english_inverted_index.pkl`, `arabic_inverted_index.pkl`, `document_lengths.pkl` |
| 4 | `python scripts\build_embeddings.py` | Generates dense embeddings using `intfloat/multilingual-e5-large` | `english_embeddings.npy`, `arabic_embeddings.npy`, `hadith_ids.npy` |

> **Note:** Step 4 requires significant VRAM (~12GB recommended). If you don't have a GPU, the script will prompt you before falling back to CPU (extremely slow).

### Download Pre-built Embeddings

If you want to skip the embedding generation step, download the pre-built files from [this link](PLACEHOLDER_URL) and extract them into `backend/data/`.

## Running the Project

### Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm run dev
```

The frontend runs at `http://localhost:5173` by default.

## Project Structure

```
hadith-search/
├── backend/
│   ├── data/                 # Preprocessed data (embeddings, indices, DB)
│   ├── routers/              # FastAPI endpoints
│   ├── scripts/              # Data processing & indexing scripts
│   │   ├── build_all.py          # Combined build orchestrator
│   │   ├── data_creation.py      # Download dataset & create DB
│   │   ├── preprocess.py         # Text preprocessing
│   │   ├── build_inverted_index.py  # BM25 inverted index builder
│   │   ├── build_embeddings.py   # Dense embedding generator
│   │   ├── search.py             # Search algorithms
│   │   ├── loading.py            # Data loading utilities
│   │   ├── pooling.py            # Relevance judgment pooling
│   │   ├── evaluation.py         # IR evaluation metrics
│   │   └── ...
│   └── main.py               # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── api/              # API client
│   │   └── i18n/             # Internationalization
│   └── package.json
├── requirements.txt
└── README.md
```

## Available Scripts

### Data Processing
- `build_all.py` - Run the full build pipeline (recommended)
- `build_embeddings.py` - Generate dense embeddings (requires CUDA, with CPU fallback prompt)
- `build_inverted_index.py` - Build BM25 inverted index
- `preprocess.py` - Preprocess hadith text
- `pooling.py` - Pool candidate documents for relevance judgment
- `evaluation.py` - Compute IR evaluation metrics

## Retrieval Architecture

| Algorithm | Description |
|-----------|-------------|
| **Term Overlap** | Exact matches ranked by term frequency |
| **TF-IDF** | Classic term frequency-inverse document frequency ranking |
| **BM25** | Okapi BM25 with optimized k1 and b parameters |
| **BM25 + TF-IDF (Hybrid)** | Combines BM25 and TF-IDF scores with weighted fusion |
| **BM25 + PRF** | BM25 with pseudo-relevance feedback (query expansion) |
| **Cosine Similarity** | Dense retrieval using vector embeddings and cosine similarity |
| **Semantic Rerank** | Cosine similarity results reranked by cross-encoder |
| **Semantic RRF** | Reciprocal Rank Fusion combining sparse (BM25) and dense (cosine) results |
| **Cross-Encoder Rerank** | Direct reranking of BM25 results using Jina AI's reranker API |
| **Final Pipeline** | Full pipeline: BM25 → Semantic Reranking → Cross Encoding |

### Search Architecture
- **Sparse Retrieval**: BM25, TF-IDF, Term Overlap — Fast, interpretable, language-independent
- **Dense Retrieval**: Cosine Similarity using `intfloat/multilingual-e5-large` embeddings
- **Reranking**: Jina AI `jina-reranker-v3` API for precision improvement (requires `JINA_API_KEY`)
- **Fusion**: Reciprocal Rank Fusion (RRF) for combining multiple retrieval methods

## Tech Stack

- **Backend**: FastAPI, SQLite, NLTK, CAMeL Tools, Sentence Transformers
- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Retrieval**: BM25, BM25+PRF, Dense retrieval (multilingual-e5-large), Hybrid
