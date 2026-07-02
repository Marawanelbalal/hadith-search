import json
import os
import numpy as np
from scipy import stats as scipy_stats
from datetime import datetime
from itertools import combinations
from typing import Optional

METRICS = ["AP", "RR", "P@20", "R@20", "F1@20", "nDCG@20"]
DEFAULT_BASELINE = "BM25"
DEFAULT_N_BOOTSTRAP = 10000
DEFAULT_CONFIDENCE = 0.95

METRIC_DISPLAY = {
    "AP": "MAP",
    "RR": "MRR",
    "P@20": "P@20",
    "R@20": "R@20",
    "F1@20": "F1@20",
    "nDCG@20": "nDCG@20",
}


def extract_per_query_metrics(
    results: dict,
    metric_name: str,
    exclude_keys: Optional[set] = None,
) -> dict:
    if exclude_keys is None:
        exclude_keys = {"MEAN"}
    per_system = {}
    for system_name, system_data in results.items():
        values = []
        for qid, qdata in system_data.items():
            if qid in exclude_keys:
                continue
            if "Metrics" in qdata and metric_name in qdata["Metrics"]:
                values.append(float(qdata["Metrics"][metric_name]))
        per_system[system_name] = values
    return per_system


def filter_graded_queries(results: dict, graded_qids: set) -> dict:
    filtered = {}
    for sys_name, sys_data in results.items():
        filtered[sys_name] = {}
        metrics_sum = {}
        count = 0
        for qid, qdata in sys_data.items():
            if qid == "MEAN":
                continue
            if qid in graded_qids:
                filtered[sys_name][qid] = qdata
                if "Metrics" in qdata:
                    for m, v in qdata["Metrics"].items():
                        metrics_sum[m] = metrics_sum.get(m, 0.0) + float(v)
                    count += 1
        if count > 0:
            filtered[sys_name]["MEAN"] = {
                "Metrics": {m: v / count for m, v in metrics_sum.items()}
            }
        else:
            filtered[sys_name]["MEAN"] = {"Metrics": {}}
    return filtered


def paired_t_test(system_a: list, system_b: list) -> dict:
    if len(system_a) != len(system_b) or len(system_a) < 2:
        return {
            "test": "paired_t",
            "t_statistic": None,
            "p_value": None,
            "significant_at_0.05": False,
            "significant_at_0.01": False,
            "note": "insufficient data",
        }
    t_stat, p_value = scipy_stats.ttest_rel(system_a, system_b)
    p_valid = not np.isnan(p_value)
    return {
        "test": "paired_t",
        "t_statistic": float(t_stat) if not np.isnan(t_stat) else None,
        "p_value": float(p_value) if p_valid else None,
        "significant_at_0.05": bool(p_value < 0.05) if p_valid else False,
        "significant_at_0.01": bool(p_value < 0.01) if p_valid else False,
    }


def wilcoxon_signed_rank(system_a: list, system_b: list) -> dict:
    if len(system_a) != len(system_b) or len(system_a) < 2:
        return {
            "test": "wilcoxon",
            "statistic": None,
            "p_value": None,
            "significant_at_0.05": False,
            "significant_at_0.01": False,
            "note": "insufficient data",
        }
    diff = [a - b for a, b in zip(system_a, system_b)]
    if all(d == 0 for d in diff):
        return {
            "test": "wilcoxon",
            "statistic": None,
            "p_value": 1.0,
            "significant_at_0.05": False,
            "significant_at_0.01": False,
            "note": "all differences are zero",
        }
    try:
        stat, p_value = scipy_stats.wilcoxon(system_a, system_b)
    except ValueError:
        return {
            "test": "wilcoxon",
            "statistic": None,
            "p_value": None,
            "significant_at_0.05": False,
            "significant_at_0.01": False,
            "note": "test failed",
        }
    p_valid = not np.isnan(p_value)
    return {
        "test": "wilcoxon",
        "statistic": float(stat) if not np.isnan(stat) else None,
        "p_value": float(p_value) if p_valid else None,
        "significant_at_0.05": bool(p_value < 0.05) if p_valid else False,
        "significant_at_0.01": bool(p_value < 0.01) if p_valid else False,
    }


def bootstrap_ci(
    values: list,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    confidence: float = DEFAULT_CONFIDENCE,
    seed: int = 42,
) -> dict:
    if not values or len(values) < 2:
        mean_val = float(np.mean(values)) if values else 0.0
        return {
            "mean": mean_val,
            "ci_lower": mean_val,
            "ci_upper": mean_val,
            "std": 0.0,
        }
    rng = np.random.default_rng(seed)
    arr = np.array(values)
    n = len(arr)
    boot_means = np.array([
        rng.choice(arr, size=n, replace=True).mean()
        for _ in range(n_bootstrap)
    ])
    alpha = (1 - confidence) / 2
    return {
        "mean": float(np.mean(arr)),
        "ci_lower": float(np.percentile(boot_means, alpha * 100)),
        "ci_upper": float(np.percentile(boot_means, (1 - alpha) * 100)),
        "std": float(np.std(arr, ddof=1)),
    }


def run_pairwise_tests(
    results: dict,
    metrics: Optional[list] = None,
    baseline: str = DEFAULT_BASELINE,
) -> dict:
    if metrics is None:
        metrics = METRICS
    system_names = list(results.keys())

    if baseline not in system_names:
        comparisons = list(combinations(system_names, 2))
    else:
        comparisons = [(s, baseline) for s in system_names if s != baseline]

    pairwise = {}
    for metric in metrics:
        per_system = extract_per_query_metrics(results, metric)
        pairwise[metric] = {}
        for sys_a, sys_b in comparisons:
            vals_a = per_system.get(sys_a, [])
            vals_b = per_system.get(sys_b, [])
            if not vals_a or not vals_b or len(vals_a) != len(vals_b):
                continue
            key = f"{sys_a} vs {sys_b}"
            mean_diff = float(np.mean(vals_a) - np.mean(vals_b))
            direction = "better" if mean_diff > 0 else ("worse" if mean_diff < 0 else "same")
            pairwise[metric][key] = {
                "t_test": paired_t_test(vals_a, vals_b),
                "wilcoxon": wilcoxon_signed_rank(vals_a, vals_b),
                "mean_diff": mean_diff,
                "direction": direction,
                "n_queries": len(vals_a),
            }
    return pairwise


def compute_bootstrap_cis(
    results: dict,
    metrics: Optional[list] = None,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    confidence: float = DEFAULT_CONFIDENCE,
) -> dict:
    if metrics is None:
        metrics = METRICS
    cis = {}
    for system_name, system_data in results.items():
        cis[system_name] = {}
        for metric in metrics:
            per_system = extract_per_query_metrics({system_name: system_data}, metric)
            values = per_system.get(system_name, [])
            cis[system_name][metric] = bootstrap_ci(
                values, n_bootstrap, confidence
            )
    return cis


def generate_latex_table(
    results: dict,
    pairwise_results: dict,
    metrics: Optional[list] = None,
    baseline: str = DEFAULT_BASELINE,
    k: int = 20,
) -> str:
    if metrics is None:
        metrics = METRICS

    system_names = list(results.keys())

    mean_metrics = {}
    best_per_metric = {}
    for metric in metrics:
        mean_metrics[metric] = {}
        for sys_name in system_names:
            mean_data = results[sys_name].get("MEAN", {}).get("Metrics", {})
            val = float(mean_data.get(metric, 0.0))
            mean_metrics[metric][sys_name] = val
        if mean_metrics[metric]:
            best_per_metric[metric] = max(
                mean_metrics[metric], key=mean_metrics[metric].get
            )
        else:
            best_per_metric[metric] = None

    n_sys = len(system_names)
    n_met = len(metrics)
    lines = []
    lines.append(r"\begin{table*}[t]")
    lines.append(r"\centering")
    lines.append(
        rf"\caption{{Retrieval performance comparison across {n_sys} systems. "
        rf"Best scores are in \textbf{{bold}}. "
        rf"* and ** denote statistically significant improvement "
        rf"over {baseline} at $p<0.05$ and $p<0.01$ (paired t-test).}}"
    )
    lines.append(r"\label{tab:results}")
    lines.append(r"\small")
    col_spec = "l" + "c" * n_met
    lines.append(rf"\begin{{tabular}}{{{col_spec}}}")
    lines.append(r"\toprule")

    header_parts = [r"\textbf{Method}"]
    for metric in metrics:
        display = METRIC_DISPLAY.get(metric, metric)
        header_parts.append(rf"\textbf{{{display}}}")
    lines.append(" & ".join(header_parts) + r" \\")
    lines.append(r"\midrule")

    for sys_name in system_names:
        display_name = sys_name.replace("_", r"\_")
        row_parts = [display_name]
        for metric in metrics:
            val = mean_metrics[metric][sys_name]
            cell = f"{val:.3f}"
            if sys_name == best_per_metric.get(metric):
                cell = r"\textbf{" + cell + "}"
            if sys_name != baseline:
                key = f"{sys_name} vs {baseline}"
                test_data = pairwise_results.get(metric, {}).get(key, {})
                t_test = test_data.get("t_test", {})
                direction = test_data.get("direction", "same")
                p_val = t_test.get("p_value")
                if p_val is not None and direction == "better":
                    if t_test.get("significant_at_0.01"):
                        cell += "**"
                    elif t_test.get("significant_at_0.05"):
                        cell += "*"
            row_parts.append(cell)
        lines.append(" & ".join(row_parts) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table*}")

    return "\n".join(lines)


def run_analysis(
    results: dict,
    metrics: Optional[list] = None,
    baseline: str = DEFAULT_BASELINE,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    confidence: float = DEFAULT_CONFIDENCE,
    k: int = 20,
) -> dict:
    if metrics is None:
        metrics = METRICS

    system_names = list(results.keys())

    per_system = extract_per_query_metrics(results, metrics[0])
    n_queries = len(per_system.get(system_names[0], [])) if system_names else 0

    pairwise = run_pairwise_tests(results, metrics, baseline)
    cis = compute_bootstrap_cis(results, metrics, n_bootstrap, confidence)

    best_systems = {}
    for metric in metrics:
        mean_data = {}
        for sys_name in system_names:
            mean_val = results[sys_name].get("MEAN", {}).get("Metrics", {}).get(metric, 0.0)
            mean_data[sys_name] = float(mean_val)
        if mean_data:
            best_systems[metric] = max(mean_data, key=mean_data.get)

    return {
        "metadata": {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "n_queries": n_queries,
            "k": k,
            "baseline": baseline,
            "n_bootstrap": n_bootstrap,
            "confidence_level": confidence,
            "systems": system_names,
        },
        "bootstrap_cis": cis,
        "pairwise_tests": pairwise,
        "summary": {
            "best_systems": best_systems,
        },
    }


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    RESULTS_PATH = os.path.join(DATA_DIR, "qrels_results.json")
    STATS_PATH = os.path.join(DATA_DIR, "stats_results.json")
    LATEX_PATH = os.path.join(DATA_DIR, "results_table.tex")

    with open(RESULTS_PATH, encoding="utf-8") as f:
        results = json.load(f)

    print(f"Loaded results from {RESULTS_PATH}")
    print(f"Systems: {list(results.keys())}")

    stats_output = run_analysis(results, baseline="BM25")
    latex_table = generate_latex_table(
        results,
        stats_output["pairwise_tests"],
        baseline="BM25",
    )

    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats_output, f, indent=2, ensure_ascii=False)
    with open(LATEX_PATH, "w", encoding="utf-8") as f:
        f.write(latex_table)

    print(f"\nStats saved -> {STATS_PATH}")
    print(f"LaTeX table -> {LATEX_PATH}")
    print(f"\nBest systems per metric:")
    for metric, best_sys in stats_output["summary"]["best_systems"].items():
        mean_val = results[best_sys].get("MEAN", {}).get("Metrics", {}).get(metric, 0.0)
        print(f"  {metric}: {best_sys} ({float(mean_val):.4f})")
