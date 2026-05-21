"""Render the RQ1.1 coarse-split TikZ figure from frozen results.

Reads:
    results/frozen_new/<run-id>/condition_summaries.csv
    results/frozen_new/<run-id>/carry_forward.json

Writes:
    thesis/figures/tikz/results/rq11_coarse_split_results.tex

The figure pegs bar heights, value labels, role colouring (baseline /
selected_main / selected_reference / rejected / degenerate), and the
note text to the frozen artifact. Re-run after any new frozen RQ1.1 run
to keep the chapter figure in sync with the data.

Usage:
    python scripts/render_rq11_figure.py \
        --run results/frozen_new/rq1_1_20260515_111428

Defaults to the thesis-facing run id if --run is omitted.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = REPO_ROOT / "results" / "frozen_new" / "rq1_1_20260515_111428"
DEFAULT_OUT = (
    REPO_ROOT
    / "thesis"
    / "figures"
    / "tikz"
    / "results"
    / "rq11_coarse_split_results.tex"
)

BAR_ORDER = [
    "monolithic",
    "split_after_layer1",
    "split_after_layer2",
    "split_after_layer3",
    "split_after_layer4",
]

SHORT_LABEL = {
    "monolithic": r"\texttt{mono}",
    "split_after_layer1": r"\texttt{layer1}",
    "split_after_layer2": r"\texttt{layer2}",
    "split_after_layer3": r"\texttt{layer3}",
    "split_after_layer4": r"\texttt{layer4}",
}


def _latex_texttt(name: str) -> str:
    """Wrap a condition name in \\texttt{} with underscores escaped."""
    return r"\texttt{" + name.replace("_", r"\_") + "}"


def load_summaries(run_dir: Path) -> Dict[str, Dict[str, float]]:
    path = run_dir / "condition_summaries.csv"
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        out = {}
        for row in reader:
            out[row["condition"]] = {
                "mean_ms": float(row["mean_ms"]),
            }
    return out


def load_carry_forward(run_dir: Path) -> Dict:
    with (run_dir / "carry_forward.json").open("r") as f:
        return json.load(f)


def role_for(condition: str, cf: Dict) -> str:
    """Map a condition to one of: baseline, selected_main,
    selected_reference, degenerate, rejected."""
    if condition == "monolithic":
        return "baseline"
    if condition == cf.get("selected_main"):
        return "selected_main"
    if condition == cf.get("selected_reference"):
        return "selected_reference"
    if condition in cf.get("degenerate_candidates", []):
        return "degenerate"
    return "rejected"


ROLE_TIKZ_STYLE = {
    "baseline": "baselinebar",
    "selected_main": "selectedmainbar",
    "selected_reference": "selectedrefbar",
    "rejected": "rejectedbar",
    "degenerate": "degeneratebar",
}

ROLE_SUBLABEL = {
    "baseline": "",
    "selected_main": "selected",
    "selected_reference": "reference",
    "rejected": "rejected",
    "degenerate": "degenerate",
}


def render_tex(
    summaries: Dict[str, Dict[str, float]], cf: Dict, run_id: str
) -> str:
    means = {c: summaries[c]["mean_ms"] for c in BAR_ORDER}
    lo = min(means.values())
    hi = max(means.values())

    # y axis: leave ~1.5 ms padding below the smallest bar and 1.0 ms above
    # the largest, snap to integers.
    y_lo = int(lo) - 1
    y_hi = int(hi) + 2
    y_scale = 6.0 / (y_hi - y_lo)  # 6 plot-units tall regardless of range

    def y_of(latency: float) -> float:
        return (latency - y_lo) * y_scale

    # x layout
    n_bars = len(BAR_ORDER)
    x_left = 0.8
    bar_width = 1.0
    bar_gap = 0.8
    bar_centers: List[float] = []
    bar_xs: List[tuple] = []
    x = x_left
    for _ in range(n_bars):
        bar_xs.append((x, x + bar_width))
        bar_centers.append(x + bar_width / 2)
        x += bar_width + bar_gap
    x_right = x - bar_gap + 0.3

    # Header / tikz prelude
    out: List[str] = []
    out.append(
        "% Auto-generated from results/frozen_new/{run}/condition_summaries.csv"
        " and carry_forward.json".format(run=run_id)
    )
    out.append(
        "% via scripts/render_rq11_figure.py. Do not edit by hand --"
        " re-run the script."
    )
    out.append(r"\begin{tikzpicture}[")
    out.append(r"    font=\small,")
    out.append(r"    axis/.style={thick, draw=black!70, -{Latex[length=2mm]}},")
    out.append(r"    grid/.style={draw=black!12, thin},")
    out.append(
        r"    baselinebar/.style={draw=black!60, fill=black!10,"
        r" rounded corners=2pt, thick},"
    )
    out.append(
        r"    selectedmainbar/.style={draw=green!45!black, fill=green!22,"
        r" rounded corners=2pt, thick},"
    )
    out.append(
        r"    selectedrefbar/.style={draw=green!40!black, fill=green!10,"
        r" rounded corners=2pt, thick},"
    )
    out.append(
        r"    rejectedbar/.style={draw=red!70!black, fill=red!10,"
        r" rounded corners=2pt, thick},"
    )
    out.append(
        r"    degeneratebar/.style={draw=orange!75!black, fill=orange!15,"
        r" rounded corners=2pt, thick},"
    )
    out.append(
        r"    label/.style={font=\scriptsize, text=black!75, align=center},"
    )
    out.append(
        r"    vallabel/.style={font=\scriptsize\bfseries, text=black!75},"
    )
    out.append(
        r"    note/.style={font=\scriptsize, text=black!65, align=center}"
    )
    out.append(r"]")
    out.append("")

    # Provenance comment block (visible in the source for reviewers)
    out.append("% Frozen means (ms) used for this figure:")
    for c in BAR_ORDER:
        out.append(f"%   {c}: {means[c]:.4f}")
    out.append(f"% Raw fastest split: {cf.get('raw_fastest')}")
    out.append(f"% Selected main: {cf.get('selected_main')}")
    out.append(f"% Selected reference: {cf.get('selected_reference')}")
    out.append(
        f"% Degenerate candidates: {cf.get('degenerate_candidates')}"
    )
    out.append(f"% Rejected: {cf.get('rejected')}")
    out.append("")

    # Grid + y-axis ticks
    for tick in range(y_lo, y_hi + 1):
        y = y_of(tick)
        out.append(
            f"\\draw[grid] (0,{y:.3f}) -- ({x_right:.3f},{y:.3f});"
        )
        out.append(
            f"\\node[anchor=east, font=\\scriptsize, text=black!65] at"
            f" (-0.15,{y:.3f}) {{{tick}}};"
        )

    out.append("")
    out.append(f"\\draw[axis] (0,0) -- ({x_right + 0.3:.3f},0);")
    out.append(f"\\draw[axis] (0,0) -- (0,{y_of(y_hi) + 0.4:.3f});")
    out.append("")

    y_axis_label_y = y_of((y_lo + y_hi) / 2)
    out.append(
        f"\\node[rotate=90, font=\\small, text=black!75] at"
        f" (-0.85,{y_axis_label_y:.3f})"
        " {Mean end-to-end latency (ms)};"
    )
    x_axis_label_x = (x_left + x_right) / 2
    out.append(
        f"\\node[font=\\small, text=black!75] at"
        f" ({x_axis_label_x:.3f},-1.15)"
        " {RQ1.1 condition};"
    )
    out.append("")

    # Bars
    for cond, (xl, xr), center in zip(BAR_ORDER, bar_xs, bar_centers):
        mean = means[cond]
        role = role_for(cond, cf)
        style = ROLE_TIKZ_STYLE[role]
        out.append(
            f"\\draw[{style}] ({xl:.3f},0) rectangle"
            f" ({xr:.3f},{y_of(mean):.3f});"
        )

    out.append("")

    # Value labels above the bars
    for cond, center in zip(BAR_ORDER, bar_centers):
        mean = means[cond]
        out.append(
            f"\\node[vallabel, above] at ({center:.3f},{y_of(mean):.3f})"
            f" {{{mean:.2f}}};"
        )

    out.append("")

    # X-axis labels (condition + role sublabel)
    for cond, center in zip(BAR_ORDER, bar_centers):
        role = role_for(cond, cf)
        sub = ROLE_SUBLABEL[role]
        label = SHORT_LABEL[cond]
        if sub:
            text = f"{label}\\\\{sub}"
        else:
            text = label
        out.append(
            f"\\node[label] at ({center:.3f},-0.45) {{{text}}};"
        )

    out.append("")

    # Note describing the carry-forward outcome (driven by carry_forward.json)
    note_x = (x_left + x_right) / 2
    raw_fastest = cf.get("raw_fastest")
    selected_main = cf.get("selected_main")
    selected_ref = cf.get("selected_reference")
    degenerate = cf.get("degenerate_candidates", [])
    near_best_pct = cf.get("near_best_window_pct")
    degen_pct = cf.get("degeneracy_threshold_pct")

    note_lines: List[str] = []
    if raw_fastest:
        note_lines.append(
            _latex_texttt(raw_fastest) + " is the raw-fastest split."
        )
    if degenerate:
        deg_set = ", ".join(_latex_texttt(d) for d in degenerate)
        note_lines.append(
            deg_set
            + " "
            + ("is" if len(degenerate) == 1 else "are")
            + " excluded by the compute-degeneracy rule (minor side $<$ "
            + f"{degen_pct:g}\\% of split compute)."
        )
    if selected_main and selected_ref:
        note_lines.append(
            "The carry-forward rule ("
            + f"{near_best_pct:g}\\% near-best window)"
            + " selects "
            + _latex_texttt(selected_main)
            + " as the main candidate and "
            + _latex_texttt(selected_ref)
            + " as the reference candidate."
        )
    elif selected_main:
        note_lines.append(
            "The carry-forward rule selects "
            + _latex_texttt(selected_main)
            + " as the main candidate."
        )

    note_text = " ".join(note_lines)
    out.append(
        f"\\node[note, text width=9.2cm] at ({note_x:.3f},-1.85) {{"
    )
    out.append(f"    {note_text}")
    out.append("};")
    out.append("")
    out.append(r"\end{tikzpicture}")

    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        type=Path,
        default=DEFAULT_RUN,
        help="Path to the frozen RQ1.1 run directory.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Path to the TikZ figure to write.",
    )
    args = parser.parse_args()

    run_dir = args.run.resolve()
    summaries = load_summaries(run_dir)
    cf = load_carry_forward(run_dir)

    missing = [c for c in BAR_ORDER if c not in summaries]
    if missing:
        raise SystemExit(
            f"Frozen run is missing conditions {missing} -- cannot render."
        )

    tex = render_tex(summaries, cf, run_id=run_dir.name)
    args.out.write_text(tex, encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
