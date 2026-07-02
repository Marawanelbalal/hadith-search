import os
import json
import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPTS_DIR, "..", "data")

HUMAN_QRELS_PATH = os.path.join(DATA_DIR, "qrels_graded.json")
LLM_GRADES_PATH = os.path.join(DATA_DIR, "llm_eval_grades.json")
QUERIES_PATH = os.path.join(DATA_DIR, "queries.json")


def extract_pairs(human_qrels, llm_grades):
    pairs = []
    per_query = {}

    for qid in human_qrels:
        human_grades = human_qrels[qid].get("grades", {})
        llm_grades_q = llm_grades.get(qid, {})

        if not human_grades or not llm_grades_q:
            continue

        query_pairs = []
        for hid, h_grade in human_grades.items():
            if str(hid) in llm_grades_q:
                l_grade = llm_grades_q[str(hid)]
                query_pairs.append((int(h_grade), int(l_grade)))
                pairs.append((int(h_grade), int(l_grade)))

        if query_pairs:
            per_query[qid] = query_pairs

    return pairs, per_query


def compute_cohens_kappa(pairs):
    if not pairs:
        return None
    human = [p[0] for p in pairs]
    llm = [p[1] for p in pairs]
    return cohen_kappa_score(human, llm)


def compute_spearman(pairs):
    if len(pairs) < 2:
        return None, None
    human = [p[0] for p in pairs]
    llm = [p[1] for p in pairs]
    rho, p_value = spearmanr(human, llm)
    return float(rho), float(p_value)


def compute_grade_distribution(grades_list):
    dist = {0: 0, 1: 0, 2: 0}
    for g in grades_list:
        if g in dist:
            dist[g] += 1
    total = sum(dist.values())
    if total > 0:
        dist = {k: f"{v} ({v/total*100:.1f}%)" for k, v in dist.items()}
    return dist


def compute_per_query_stats(per_query):
    results = {}
    for qid, pairs in per_query.items():
        human = [p[0] for p in pairs]
        llm = [p[1] for p in pairs]
        kappa = cohen_kappa_score(human, llm) if len(set(human)) > 1 or len(set(llm)) > 1 else None
        if len(pairs) >= 2:
            rho, p_val = spearmanr(human, llm)
            rho = float(rho) if not np.isnan(rho) else None
            p_val = float(p_val) if not np.isnan(p_val) else None
        else:
            rho, p_val = None, None
        agreement = sum(1 for h, l in pairs if h == l) / len(pairs) if pairs else 0
        results[qid] = {
            "n_docs": len(pairs),
            "kappa": kappa,
            "spearman_rho": rho,
            "spearman_p": p_val,
            "agreement_rate": round(agreement, 4),
            "human_dist": compute_grade_distribution(human),
            "llm_dist": compute_grade_distribution(llm),
        }
    return results


def validate(human_qrels_path=None, llm_grades_path=None):
    h_path = human_qrels_path or HUMAN_QRELS_PATH
    l_path = llm_grades_path or LLM_GRADES_PATH

    with open(h_path, encoding="utf-8") as f:
        human_qrels = json.load(f)
    with open(l_path, encoding="utf-8") as f:
        llm_grades = json.load(f)

    with open(QUERIES_PATH, encoding="utf-8") as f:
        queries = json.load(f)

    pairs, per_query = extract_pairs(human_qrels, llm_grades)

    if not pairs:
        return {
            "error": "No overlapping grades found between human and LLM qrels",
            "human_queries_with_grades": sum(1 for v in human_qrels.values() if v.get("grades")),
            "llm_queries_with_grades": sum(1 for v in llm_grades.values() if v),
        }

    kappa = compute_cohens_kappa(pairs)
    rho, p_value = compute_spearman(pairs)

    human_all = [p[0] for p in pairs]
    llm_all = [p[1] for p in pairs]
    agreement = sum(1 for h, l in pairs if h == l) / len(pairs)

    per_query_stats = compute_per_query_stats(per_query)

    report = {
        "metadata": {
            "n_queries_compared": len(per_query),
            "n_total_pairs": len(pairs),
            "human_qrels_path": h_path,
            "llm_grades_path": l_path,
        },
        "overall": {
            "cohens_kappa": round(kappa, 4) if kappa is not None else None,
            "spearman_rho": round(rho, 4) if rho is not None else None,
            "spearman_p_value": round(p_value, 6) if p_value is not None else None,
            "agreement_rate": round(agreement, 4),
            "human_grade_distribution": compute_grade_distribution(human_all),
            "llm_grade_distribution": compute_grade_distribution(llm_all),
        },
        "per_query": per_query_stats,
        "kappa_interpretation": interpret_kappa(kappa),
    }

    return report


def interpret_kappa(kappa):
    if kappa is None:
        return "N/A"
    if kappa < 0:
        return "Less than chance agreement"
    if kappa < 0.20:
        return "Slight agreement"
    if kappa < 0.40:
        return "Fair agreement"
    if kappa < 0.60:
        return "Moderate agreement"
    if kappa < 0.80:
        return "Substantial agreement"
    return "Almost perfect agreement"


def generate_latex_validation_table(report):
    rows = []
    rows.append(r"\begin{table}[htbp]")
    rows.append(r"\centering")
    rows.append(r"\caption{LLM Grader Validation Against Human Annotations}")
    rows.append(r"\label{tab:llm-validation}")
    rows.append(r"\begin{tabular}{lcccc}")
    rows.append(r"\toprule")
    rows.append(r"Query & $n$ & Kappa & Spearman $\rho$ & Agreement \\")
    rows.append(r"\midrule")

    for qid, stats in report["per_query"].items():
        qid_short = qid[:12]
        kappa_str = f"{stats['kappa']:.3f}" if stats['kappa'] is not None else "---"
        rho_str = f"{stats['spearman_rho']:.3f}" if stats['spearman_rho'] is not None else "---"
        agr_str = f"{stats['agreement_rate']:.1%}"
        rows.append(f"{qid_short} & {stats['n_docs']} & {kappa_str} & {rho_str} & {agr_str} \\\\")

    rows.append(r"\midrule")
    ov = report["overall"]
    n_total = report["metadata"]["n_total_pairs"]
    kappa_str = f"{ov['cohens_kappa']:.3f}" if ov['cohens_kappa'] is not None else "---"
    rho_str = f"{ov['spearman_rho']:.3f}" if ov['spearman_rho'] is not None else "---"
    agr_str = f"{ov['agreement_rate']:.1%}"
    rows.append(f"\\textbf{{Overall}} & \\textbf{{{n_total}}} & \\textbf{{{kappa_str}}} & \\textbf{{{rho_str}}} & \\textbf{{{agr_str}}} \\\\")

    rows.append(r"\bottomrule")
    rows.append(r"\end{tabular}")
    rows.append(r"\end{table}")

    return "\n".join(rows)


if __name__ == "__main__":
    print("=== LLM Grader Validation ===\n")

    report = validate()

    if "error" in report:
        print(f"Error: {report['error']}")
        print(f"Human queries with grades: {report.get('human_queries_with_grades', 0)}")
        print(f"LLM queries with grades: {report.get('llm_queries_with_grades', 0)}")
    else:
        meta = report["metadata"]
        ov = report["overall"]
        print(f"Queries compared: {meta['n_queries_compared']}")
        print(f"Total doc pairs:  {meta['n_total_pairs']}")
        print()
        print("--- Overall Metrics ---")
        print(f"Cohen's Kappa:       {ov['cohens_kappa']}")
        print(f"Spearman rho:        {ov['spearman_rho']}")
        print(f"Spearman p-value:    {ov['spearman_p_value']}")
        print(f"Agreement rate:      {ov['agreement_rate']:.1%}")
        print(f"Kappa interpretation: {report['kappa_interpretation']}")
        print()
        print(f"Human grade dist: {ov['human_grade_distribution']}")
        print(f"LLM grade dist:   {ov['llm_grade_distribution']}")
        print()
        print("--- Per-Query Breakdown ---")
        for qid, stats in report["per_query"].items():
            kappa_s = f"{stats['kappa']:.3f}" if stats['kappa'] is not None else "---"
            rho_s = f"{stats['spearman_rho']:.3f}" if stats['spearman_rho'] is not None else "---"
            print(f"  {qid:40s}  n={stats['n_docs']:3d}  kappa={kappa_s}  rho={rho_s}  agr={stats['agreement_rate']:.1%}")

        latex = generate_latex_validation_table(report)
        latex_path = os.path.join(DATA_DIR, "llm_validation_table.tex")
        with open(latex_path, "w", encoding="utf-8") as f:
            f.write(latex)
        print(f"\nLaTeX table saved to: {latex_path}")

        report_path = os.path.join(DATA_DIR, "llm_validation_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to: {report_path}")
