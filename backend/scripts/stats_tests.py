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


E5_DEPENDENT_SYSTEMS = [
    "COSINE_SIMILARITY",
    "BM25_SEMANTIC_RERANK",
    "BM25_RRF",
    "FINAL_PIPELINE",
]

FINETUNE_MODES = ["triplet", "kv_pairs", "combined"]

FINETUNE_MODE_LABELS = {
    "triplet": r"FT(triplet)",
    "kv_pairs": r"FT(kv)",
    "combined": r"FT(combined)",
}


def run_cross_config_tests(
    baseline_results: dict,
    finetuned_results: dict,
    metrics: Optional[list] = None,
    e5_systems: Optional[list] = None,
) -> dict:
    if metrics is None:
        metrics = METRICS
    if e5_systems is None:
        e5_systems = E5_DEPENDENT_SYSTEMS

    tests = {}
    for system_name in e5_systems:
        if system_name not in baseline_results:
            continue
        tests[system_name] = {}
        for metric in metrics:
            baseline_vals = extract_per_query_metrics(
                {system_name: baseline_results[system_name]}, metric
            ).get(system_name, [])
            if not baseline_vals:
                continue

            tests[system_name][metric] = {}
            for mode, ft_results in finetuned_results.items():
                if system_name not in ft_results:
                    continue
                ft_vals = extract_per_query_metrics(
                    {system_name: ft_results[system_name]}, metric
                ).get(system_name, [])
                if not ft_vals or len(baseline_vals) != len(ft_vals):
                    continue

                key = f"{mode} vs baseline"
                mean_diff = float(np.mean(ft_vals) - np.mean(baseline_vals))
                direction = "better" if mean_diff > 0 else ("worse" if mean_diff < 0 else "same")
                tests[system_name][metric][key] = {
                    "t_test": paired_t_test(ft_vals, baseline_vals),
                    "wilcoxon": wilcoxon_signed_rank(ft_vals, baseline_vals),
                    "mean_diff": mean_diff,
                    "direction": direction,
                    "n_queries": len(baseline_vals),
                    "baseline_mean": float(np.mean(baseline_vals)),
                    "finetuned_mean": float(np.mean(ft_vals)),
                }
    return tests


def generate_comparison_latex_table(
    baseline_results: dict,
    finetuned_results: dict,
    cross_config: dict,
    metrics: Optional[list] = None,
    e5_systems: Optional[list] = None,
) -> str:
    if metrics is None:
        metrics = METRICS
    if e5_systems is None:
        e5_systems = E5_DEPENDENT_SYSTEMS

    n_met = len(metrics)
    lines = []
    lines.append(r"\begin{table*}[t]")
    lines.append(r"\centering")
    lines.append(
        r"\caption{Impact of LoRA fine-tuning on E5-dependent retrieval systems. "
        r"Baseline uses pretrained \mbox{multilingual-e5-large}. "
        r"FT(triplet), FT(kv), and FT(combined) use LoRA adapters trained with "
        r"contrastive, cross-concept alignment, and combined objectives. "
        r"Best per system per metric in \textbf{bold}. "
        r"* and ** denote significant improvement over baseline "
        r"at $p<0.05$ and $p<0.01$ (paired t-test).}"
    )
    lines.append(r"\label{tab:finetune-comparison}")
    lines.append(r"\small")
    col_spec = "ll" + "c" * n_met
    lines.append(rf"\begin{{tabular}}{{{col_spec}}}")
    lines.append(r"\toprule")

    header_parts = [r"\textbf{System}", r"\textbf{Mode}"]
    for metric in metrics:
        display = METRIC_DISPLAY.get(metric, metric)
        header_parts.append(rf"\textbf{{{display}}}")
    lines.append(" & ".join(header_parts) + r" \\")
    lines.append(r"\midrule")

    for system_name in e5_systems:
        if system_name not in baseline_results:
            continue

        all_vals = {}
        for metric in metrics:
            all_vals[metric] = {}
            mean_data = baseline_results[system_name].get("MEAN", {}).get("Metrics", {})
            all_vals[metric]["baseline"] = float(mean_data.get(metric, 0.0))
            for mode, ft_results in finetuned_results.items():
                if system_name in ft_results:
                    ft_mean = ft_results[system_name].get("MEAN", {}).get("Metrics", {})
                    all_vals[metric][mode] = float(ft_mean.get(metric, 0.0))

        best_mode = {}
        for metric in metrics:
            vals = all_vals[metric]
            if vals:
                best_mode[metric] = max(vals, key=vals.get)
            else:
                best_mode[metric] = None

        display_name = system_name.replace("_", r"\_")

        row_parts = [display_name, "Baseline"]
        for metric in metrics:
            val = all_vals[metric].get("baseline", 0.0)
            cell = f"{val:.3f}"
            if best_mode[metric] == "baseline":
                cell = r"\textbf{" + cell + "}"
            row_parts.append(cell)
        lines.append(" & ".join(row_parts) + r" \\")

        for mode in FINETUNE_MODES:
            if mode not in finetuned_results:
                continue
            if system_name not in finetuned_results[mode]:
                continue

            row_parts = ["", FINETUNE_MODE_LABELS[mode]]
            for metric in metrics:
                val = all_vals[metric].get(mode, 0.0)
                cell = f"{val:.3f}"
                if best_mode[metric] == mode:
                    cell = r"\textbf{" + cell + "}"
                test_data = cross_config.get(system_name, {}).get(metric, {}).get(f"{mode} vs baseline", {})
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

        lines.append(r"\midrule")

    if lines[-1] == r"\midrule":
        lines.pop()
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table*}")

    return "\n".join(lines)


def generate_delta_table(
    baseline_results: dict,
    finetuned_results: dict,
    metrics: Optional[list] = None,
    e5_systems: Optional[list] = None,
) -> dict:
    if metrics is None:
        metrics = METRICS
    if e5_systems is None:
        e5_systems = E5_DEPENDENT_SYSTEMS

    deltas = {}
    for system_name in e5_systems:
        if system_name not in baseline_results:
            continue
        deltas[system_name] = {}
        for metric in metrics:
            baseline_val = baseline_results[system_name].get("MEAN", {}).get("Metrics", {}).get(metric, 0.0)
            deltas[system_name][metric] = {}
            for mode, ft_results in finetuned_results.items():
                if system_name not in ft_results:
                    continue
                ft_val = ft_results[system_name].get("MEAN", {}).get("Metrics", {}).get(metric, 0.0)
                if baseline_val > 0:
                    delta_pct = ((ft_val - baseline_val) / baseline_val) * 100
                else:
                    delta_pct = 0.0
                deltas[system_name][metric][mode] = {
                    "baseline": float(baseline_val),
                    "finetuned": float(ft_val),
                    "delta": float(ft_val - baseline_val),
                    "delta_pct": round(delta_pct, 2),
                }

    averages = {}
    for metric in metrics:
        averages[metric] = {}
        for mode in FINETUNE_MODES:
            if mode not in finetuned_results:
                continue
            pct_vals = []
            for system_name in e5_systems:
                if system_name in deltas and metric in deltas[system_name] and mode in deltas[system_name][metric]:
                    pct_vals.append(deltas[system_name][metric][mode]["delta_pct"])
            if pct_vals:
                averages[metric][mode] = round(sum(pct_vals) / len(pct_vals), 2)

    return {"per_system": deltas, "averages": averages}


def generate_delta_latex_table(delta_data: dict, metrics: Optional[list] = None) -> str:
    if metrics is None:
        metrics = METRICS

    available_modes = [
        m for m in FINETUNE_MODES
        if m in delta_data.get("averages", {}).get(metrics[0], {})
    ]
    if not available_modes:
        return ""

    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(
        r"\caption{Relative improvement (\%) from LoRA fine-tuning "
        r"averaged across 6 IR metrics. Positive values indicate "
        r"improvement over baseline.}"
    )
    lines.append(r"\label{tab:finetune-delta}")
    lines.append(r"\small")
    col_spec = "l" + "c" * len(available_modes)
    lines.append(rf"\begin{{tabular}}{{{col_spec}}}")
    lines.append(r"\toprule")

    header_parts = [r"\textbf{System}"]
    for mode in available_modes:
        header_parts.append(rf"\textbf{{{FINETUNE_MODE_LABELS[mode]}}}")
    lines.append(" & ".join(header_parts) + r" \\")
    lines.append(r"\midrule")

    e5_systems = list(delta_data.get("per_system", {}).keys())

    for system_name in e5_systems:
        display_name = system_name.replace("_", r"\_")
        row_parts = [display_name]
        for mode in available_modes:
            pct_vals = []
            for metric in metrics:
                sys_data = delta_data["per_system"].get(system_name, {}).get(metric, {}).get(mode)
                if sys_data:
                    pct_vals.append(sys_data["delta_pct"])
            if pct_vals:
                avg = sum(pct_vals) / len(pct_vals)
                sign = "+" if avg >= 0 else ""
                row_parts.append(f"{sign}{avg:.1f}\\%")
            else:
                row_parts.append("--")
        lines.append(" & ".join(row_parts) + r" \\")

    lines.append(r"\midrule")

    row_parts = [r"\textbf{Average}"]
    for mode in available_modes:
        pct_vals = []
        for metric in metrics:
            val = delta_data["averages"].get(metric, {}).get(mode)
            if val is not None:
                pct_vals.append(val)
        if pct_vals:
            avg = sum(pct_vals) / len(pct_vals)
            sign = "+" if avg >= 0 else ""
            row_parts.append(rf"\textbf{{{sign}{avg:.1f}\%}}")
        else:
            row_parts.append("--")
    lines.append(" & ".join(row_parts) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    return "\n".join(lines)


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
