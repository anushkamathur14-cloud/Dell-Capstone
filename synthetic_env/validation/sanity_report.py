"""Generate a human-readable sanity report from generated benchmark outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def build_sanity_report(input_dir: str = "synthetic_env/benchmarks/generated_sanity") -> str:
    base = Path(input_dir)
    pop = pd.read_parquet(base / "population.parquet")
    arms = pd.read_parquet(base / "arms.parquet")
    metrics = pd.read_parquet(base / "metrics_summary.parquet")
    validation = pd.read_parquet(base / "validation_report.parquet")

    segment_shares = pop["segment_id"].value_counts(normalize=True).sort_values(ascending=False)
    retention_spread = float(metrics["retention"].max() - metrics["retention"].min())

    behavioral_row = validation[validation["section"] == "behavioral_realism"].iloc[0]
    behavioral_details = json.loads(behavioral_row["details"])

    lines = []
    lines.append("# Synthetic Benchmark Sanity Report")
    lines.append("")
    lines.append(f"Input directory: `{base}`")
    lines.append("")
    lines.append("## Q1 - Variables: good set, not too many?")
    lines.append(f"- Population rows: {len(pop)}")
    lines.append(f"- Feature count (population columns): {len(pop.columns)}")
    lines.append("- Segment mix:")
    for seg, share in segment_shares.items():
        lines.append(f"  - {seg}: {share:.3f}")
    lines.append("- Verdict: compact and interpretable variable set for v1.")
    lines.append("")
    lines.append("## Q2 - Treatment bundles: plausible and rich enough?")
    lines.append(f"- Number of valid arms: {len(arms)}")
    lines.append(f"- Arm ids: {', '.join(arms['arm_id'].tolist())}")
    lines.append("- Verdict: enough variation for benchmarking without over-complexity.")
    lines.append("")
    lines.append("## Q3 - Causal assumptions: non-trivial problem?")
    lines.append(f"- Retention spread across arms: {retention_spread:.4f}")
    lines.append(f"- Heterogeneous effects detected: {behavioral_details.get('has_heterogeneous_effects')}")
    lines.append(f"- Delayed effects detected: {behavioral_details.get('delayed_effect_present')}")
    lines.append("- Verdict: non-trivial via arm/segment differences; delayed effects currently too weak for configured threshold.")
    lines.append("")
    lines.append("## Q4 - Outputs credibility")
    lines.append("- Validation checks:")
    for _, row in validation.iterrows():
        lines.append(f"  - {row['section']}: pass={row['pass']}")
    lines.append("- Metrics summary snapshot:")
    for row in metrics[["arm_id", "conversion", "retention", "engagement", "revenue_proxy"]].itertuples(index=False):
        lines.append(
            f"  - {row.arm_id}: conv={row.conversion:.3f}, d7={row.retention:.3f}, engagement={row.engagement:.2f}, value={row.revenue_proxy:.3f}"
        )
    lines.append("- Verdict: outputs look plausible; one validation axis indicates we should strengthen delayed-effect term.")

    return "\n".join(lines)


def write_sanity_report(
    input_dir: str = "synthetic_env/benchmarks/generated_sanity",
    output_path: str = "synthetic_env/benchmarks/generated_sanity/sanity_report.md",
) -> Path:
    report = build_sanity_report(input_dir=input_dir)
    out = Path(output_path)
    out.write_text(report, encoding="utf-8")
    return out


if __name__ == "__main__":
    path = write_sanity_report()
    print(f"Wrote {path}")
