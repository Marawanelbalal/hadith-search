"""
Full evaluation orchestration: baseline + 3 fine-tuned modes.

Loads existing evaluation results and generates:
- Cross-config significance tests (baseline vs each fine-tuned mode)
- Comparison LaTeX table (E5-dependent systems x all modes)
- Delta table (relative improvement %)
- Unified comparison JSON

Prerequisites:
    1. Baseline:   python -m scripts.evaluation
    2. Fine-tune:  python -m scripts.finetune --mode {triplet,kv_pairs,combined}
    3. FT eval:    python -m scripts.finetune_eval --mode {triplet,kv_pairs,combined}

Usage:
    python -m scripts.full_evaluation
    python -m scripts.full_evaluation --baseline BM25 --k 20
"""

import os
import json
import argparse
from datetime import datetime

from scripts.stats_tests import (
    METRICS,
    E5_DEPENDENT_SYSTEMS,
    FINETUNE_MODES,
    run_cross_config_tests,
    generate_comparison_latex_table,
    generate_delta_table,
    generate_delta_latex_table,
    filter_graded_queries,
    run_analysis,
    generate_latex_table,
)

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPTS_DIR, "..", "data")


def load_results(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Full evaluation: baseline + fine-tuned comparison"
    )
    parser.add_argument("--k", type=int, default=20)
    parser.add_argument(
        "--baseline", default="BM25",
        help="Baseline system for significance tests",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("FULL EVALUATION: Baseline + Fine-tuned Comparison")
    print("=" * 60)

    baseline_path = os.path.join(DATA_DIR, "qrels_results.json")
    baseline_results = load_results(baseline_path)
    if baseline_results is None:
        print(f"ERROR: Baseline results not found at {baseline_path}")
        print("Run: python -m scripts.evaluation")
        return

    print(f"\nBaseline loaded: {len(baseline_results)} systems")
    print(f"  Systems: {list(baseline_results.keys())}")

    finetuned_results = {}
    for mode in FINETUNE_MODES:
        path = os.path.join(DATA_DIR, f"finetuned_results_{mode}.json")
        results = load_results(path)
        if results is not None:
            finetuned_results[mode] = results
            print(f"Fine-tuned loaded: {mode} ({len(results)} systems)")
        else:
            print(f"WARNING: Fine-tuned results not found for '{mode}'")
            print(f"  Expected: {path}")
            print(f"  Run: python -m scripts.finetune_eval --mode {mode}")

    qrels_path = os.path.join(DATA_DIR, "qrels_graded.json")
    if not os.path.exists(qrels_path):
        print(f"ERROR: Graded qrels not found at {qrels_path}")
        return
    with open(qrels_path, encoding="utf-8") as f:
        qrels_graded = json.load(f)

    graded_qids = {qid for qid, data in qrels_graded.items() if data.get("grades")}
    print(f"\nGraded queries: {len(graded_qids)}")

    baseline_filtered = filter_graded_queries(baseline_results, graded_qids)
    finetuned_filtered = {}
    for mode, results in finetuned_results.items():
        finetuned_filtered[mode] = filter_graded_queries(results, graded_qids)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n--- Baseline Analysis ---")
    baseline_stats = run_analysis(baseline_filtered, baseline=args.baseline, k=args.k)
    baseline_latex = generate_latex_table(
        baseline_filtered,
        baseline_stats["pairwise_tests"],
        baseline=args.baseline,
        k=args.k,
    )

    stats_path = os.path.join(DATA_DIR, "stats_results.json")
    latex_path = os.path.join(DATA_DIR, "results_table.tex")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(baseline_stats, f, indent=2, ensure_ascii=False)
    with open(latex_path, "w", encoding="utf-8") as f:
        f.write(baseline_latex)
    print(f"  Stats  -> {stats_path}")
    print(f"  LaTeX  -> {latex_path}")

    if not finetuned_filtered:
        print("\nNo fine-tuned results found. Done.")
        return

    print("\n--- Cross-Config Significance Tests ---")
    cross_config = run_cross_config_tests(
        baseline_filtered,
        finetuned_filtered,
        e5_systems=E5_DEPENDENT_SYSTEMS,
    )
    n_tests = sum(
        1 for sys_data in cross_config.values()
        for metric_data in sys_data.values()
        for _ in metric_data
    )
    print(f"  {n_tests} comparisons across {len(cross_config)} systems")

    print("\n--- Comparison LaTeX Table ---")
    comparison_latex = generate_comparison_latex_table(
        baseline_filtered,
        finetuned_filtered,
        cross_config,
        e5_systems=E5_DEPENDENT_SYSTEMS,
    )
    comparison_path = os.path.join(DATA_DIR, "comparison_table.tex")
    with open(comparison_path, "w", encoding="utf-8") as f:
        f.write(comparison_latex)
    print(f"  -> {comparison_path}")

    print("\n--- Delta Table ---")
    delta_data = generate_delta_table(
        baseline_filtered,
        finetuned_filtered,
        e5_systems=E5_DEPENDENT_SYSTEMS,
    )
    delta_latex = generate_delta_latex_table(delta_data)
    delta_path = os.path.join(DATA_DIR, "delta_table.tex")
    with open(delta_path, "w", encoding="utf-8") as f:
        f.write(delta_latex)
    print(f"  -> {delta_path}")

    comparison_json = {
        "metadata": {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "n_graded_queries": len(graded_qids),
            "graded_qids": sorted(graded_qids),
            "baseline_system": args.baseline,
            "k": args.k,
            "modes": list(finetuned_filtered.keys()),
            "e5_systems": E5_DEPENDENT_SYSTEMS,
            "metrics": METRICS,
        },
        "baseline_stats": baseline_stats,
        "cross_config_tests": cross_config,
        "delta": delta_data,
    }
    comparison_json_path = os.path.join(DATA_DIR, "comparison_results.json")
    with open(comparison_json_path, "w", encoding="utf-8") as f:
        json.dump(comparison_json, f, indent=2, ensure_ascii=False)
    print(f"\n  Comparison JSON -> {comparison_json_path}")

    for path in [comparison_path, delta_path, comparison_json_path]:
        stamped = path.replace(".", f"_{timestamp}.")
        with open(stamped, "w", encoding="utf-8") as f:
            if path.endswith(".json"):
                json.dump(comparison_json, f, indent=2, ensure_ascii=False)
            elif path == comparison_path:
                f.write(comparison_latex)
            else:
                f.write(delta_latex)
        print(f"  Archived        -> {stamped}")

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Baseline systems:    {len(baseline_filtered)}")
    print(f"Fine-tuned modes:    {list(finetuned_filtered.keys())}")
    available_e5 = [s for s in E5_DEPENDENT_SYSTEMS if s in baseline_filtered]
    print(f"E5 systems analyzed: {len(available_e5)}")
    print(f"  {available_e5}")

    print(f"\nBest fine-tuning mode per system (avg delta %):")
    for system_name in E5_DEPENDENT_SYSTEMS:
        if system_name not in delta_data["per_system"]:
            continue
        mode_deltas = {}
        for mode in FINETUNE_MODES:
            if mode not in delta_data["averages"].get(METRICS[0], {}):
                continue
            pct_vals = []
            for metric in METRICS:
                sys_data = delta_data["per_system"].get(system_name, {}).get(metric, {}).get(mode)
                if sys_data:
                    pct_vals.append(sys_data["delta_pct"])
            if pct_vals:
                mode_deltas[mode] = sum(pct_vals) / len(pct_vals)
        if mode_deltas:
            best_mode = max(mode_deltas, key=mode_deltas.get)
            best_val = mode_deltas[best_mode]
            sign = "+" if best_val >= 0 else ""
            all_deltas = "  ".join(
                f"{m}: {'+' if v >= 0 else ''}{v:.1f}%"
                for m, v in sorted(mode_deltas.items(), key=lambda x: x[1], reverse=True)
            )
            print(f"  {system_name:30s}  {all_deltas}")


if __name__ == "__main__":
    main()
