"""Generate Slide 7 technical validation illustration."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def generate_slide7_figure(output_path: str = "synthetic_env/benchmarks/figures/slide7_technical_validation.png") -> Path:
    arms = ["control", "fast_progression", "guided_onboarding", "high_challenge"]
    day7_retention = [0.5886, 0.6508, 0.6219, 0.6435]

    checks = [
        "Day-7 spread",
        "Delayed effect detectability",
        "Behavioral realism",
    ]
    before = ["0.0708", "False", "Fail"]
    after = ["0.0623", "True", "Pass"]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(nrows=2, ncols=3, width_ratios=[2.2, 0.1, 1.2], height_ratios=[0.2, 0.8])

    title_ax = fig.add_subplot(gs[0, :])
    title_ax.axis("off")
    title_ax.text(
        0,
        1,
        "Technical Validation of the Benchmark Environment",
        fontsize=22,
        fontweight="bold",
        va="top",
    )
    title_ax.text(
        0,
        0.52,
        "v1 environment passes structural and statistical checks, with calibrated behavioral dynamics",
        fontsize=12,
        color="#444444",
        va="top",
    )

    bar_ax = fig.add_subplot(gs[1, 0])
    colors = ["#6BAED6", "#31A354", "#9E9AC8", "#FD8D3C"]
    bars = bar_ax.bar(arms, day7_retention, color=colors, edgecolor="#333333", linewidth=0.6)

    bar_ax.set_title("Day-7 Retention by Arm", fontsize=14, pad=12)
    bar_ax.set_ylabel("Retention rate", fontsize=11)
    bar_ax.set_ylim(0.54, 0.68)
    bar_ax.tick_params(axis="x", labelrotation=15)

    for bar, value in zip(bars, day7_retention):
        bar_ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.002,
            f"{value:.4f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    bar_ax.text(
        0.02,
        0.96,
        "Non-trivial spread = 0.0623",
        transform=bar_ax.transAxes,
        fontsize=10,
        color="#1f4e79",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#eaf2fb", "edgecolor": "#b3cde3"},
        va="top",
    )

    table_ax = fig.add_subplot(gs[1, 2])
    table_ax.axis("off")
    table_ax.set_title("Calibration Check", fontsize=14, pad=12)

    cell_text = [[c, b, a] for c, b, a in zip(checks, before, after)]
    table = table_ax.table(
        cellText=cell_text,
        colLabels=["Check", "Before", "After"],
        cellLoc="center",
        colLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.8)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#d9e6f2")
        elif col == 2:
            cell.set_facecolor("#e6f4ea")
        elif col == 1:
            cell.set_facecolor("#fdf2f2")

    fig.text(
        0.01,
        0.01,
        "Population: 11 variables, 4 segments | Arms: control, fast_progression, guided_onboarding, high_challenge",
        fontsize=9,
        color="#555555",
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0, 0.03, 1, 0.98])
    fig.savefig(out, dpi=220)
    plt.close(fig)
    return out


if __name__ == "__main__":
    path = generate_slide7_figure()
    print(f"Wrote {path}")
