"""Step 3: coverage and balance tables plus PNG charts."""
from __future__ import annotations

from collections import Counter, defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from audit_lib import (CAPTURE_ALIASES, CHARTS, CLASSES, SCOPE_TYPE_TARGET, label_rows,  # noqa: E402
                       pct, write_json)

# Reference palette (dataviz skill, references/palette.md), light mode.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
MIN_TEST_SAMPLES = 30  # below this a per-class test metric is too noisy to report
MIN_TRAIN_SAMPLES = 100


def style(ax, title: str) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", color=INK, fontsize=11, fontweight="bold")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=8)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def bar(counts: dict[str, int], title: str, fname: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=SURFACE)
    keys = list(counts)
    vals = [counts[k] for k in keys]
    ax.bar(keys, vals, color=SERIES[0], width=0.6)
    for x, v in zip(keys, vals):
        ax.text(x, v, str(v), ha="center", va="bottom", fontsize=7, color=INK_2)
    style(ax, title)
    ax.set_ylabel(ylabel, color=INK_2, fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS / fname, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def heatmap(matrix: list[list[int]], rows: list[str], cols: list[str], title: str, fname: str) -> None:
    fig, ax = plt.subplots(figsize=(max(5, 0.55 * len(cols) + 2), 0.38 * len(rows) + 1.4),
                           facecolor=SURFACE)
    vmax = max(max(r) for r in matrix) or 1
    ax.imshow(matrix, cmap="Blues", vmin=0, vmax=vmax, aspect="auto")
    for i, r in enumerate(matrix):
        for j, v in enumerate(r):
            ax.text(j, i, str(v), ha="center", va="center", fontsize=7,
                    color="white" if v > 0.6 * vmax else INK)
    ax.set_xticks(range(len(cols)), cols, fontsize=8, color=INK_2)
    ax.set_yticks(range(len(rows)), rows, fontsize=8, color=INK_2)
    ax.set_title(title, loc="left", color=INK, fontsize=11, fontweight="bold")
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / fname, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def grouped_split_bar(by_split: dict[str, dict[str, int]], keys: list[str], title: str, fname: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 3.8), facecolor=SURFACE)
    splits = ["train", "validation", "test"]
    w = 0.26
    for k, sp in enumerate(splits):
        xs = [i + (k - 1) * w for i in range(len(keys))]
        ax.bar(xs, [by_split[sp].get(c, 0) for c in keys], width=w - 0.02, color=SERIES[k], label=sp)
    ax.set_xticks(range(len(keys)), keys)
    style(ax, title)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK_2, ncols=3, loc="upper right")
    fig.tight_layout()
    fig.savefig(CHARTS / fname, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def table(counter: Counter, keys: list[str] | None = None) -> list[dict]:
    total = sum(counter.values())
    keys = keys or sorted(counter)
    return [{"value": k, "count": counter.get(k, 0), "pct": pct(counter.get(k, 0), total)} for k in keys]


def main() -> dict:
    rows = label_rows()
    for r in rows:
        r["capture"] = CAPTURE_ALIASES.get(r["capture_type"], r["capture_type"])
    digital = [r for r in rows if r["capture_type"] == "digital"]
    tampered_digital = [r for r in digital if r["sample_id"] != r["original_id"]]

    bases = {r["original_id"]: r["doc_type"] for r in rows}
    base_by_type = Counter(bases.values())
    types = ["FIR", "charge_sheet", "statement", "court_order"]

    class_all = Counter(r["tamper_class"] for r in rows)
    class_variants = Counter(r["tamper_class"] for r in tampered_digital)
    class_by_type = {t: Counter(r["tamper_class"] for r in tampered_digital if r["doc_type"] == t) for t in types}
    verdict = Counter(r["expected_verdict"] for r in rows)
    severity = Counter(r["severity"] for r in rows)
    capture = Counter(r["capture"] for r in rows)
    caps = ["digital", "scan", "photo"]
    cross = {c: Counter(r["capture"] for r in rows if r["tamper_class"] == c) for c in CLASSES}
    split_class = {s: Counter(r["tamper_class"] for r in rows if r["split"] == s)
                   for s in ("train", "validation", "test")}

    harmless = sum(1 for r in rows if r["tamper_class"] == "E0")
    flags: list[str] = []
    if not 50 <= len(bases) <= 100:
        flags.append(f"base document count {len(bases)} outside 50 to 100")
    for c in CLASSES:
        for cap in caps:
            if cross[c][cap] == 0:
                flags.append(f"empty cell {c} x {cap}")
        if split_class["test"][c] < MIN_TEST_SAMPLES:
            flags.append(f"{c}: only {split_class['test'][c]} test samples (<{MIN_TEST_SAMPLES})")
        if split_class["validation"][c] < MIN_TEST_SAMPLES:
            flags.append(f"{c}: only {split_class['validation'][c]} validation samples (<{MIN_TEST_SAMPLES})")
        if split_class["train"][c] < MIN_TRAIN_SAMPLES:
            flags.append(f"{c}: only {split_class['train'][c]} train samples (<{MIN_TRAIN_SAMPLES})")
    flags.append(f"harmless (E0) share {pct(harmless, len(rows))}% vs about 33% target (SCOPE.md 5)")
    flags.append(f"verdict imbalance Tampered:Valid = {verdict['Tampered']}:{verdict['Valid']}")
    if severity.get("Minor", 0) == 0:
        flags.append("no Minor severity samples at all")
    for t in types:
        if base_by_type[t] != SCOPE_TYPE_TARGET[t]:
            flags.append(f"{t}: {base_by_type[t]} bases vs SCOPE.md suggestion {SCOPE_TYPE_TARGET[t]}")

    # Charts
    bar({t: base_by_type[t] for t in types}, "Base documents by type", "base_docs_by_type.png", "base documents")
    bar({c: class_all[c] for c in CLASSES}, "Samples per tamper class (all captures)", "class_distribution.png", "samples")
    bar({k: verdict[k] for k in ("Valid", "Tampered", "Inconclusive")}, "Expected verdict (as labelled)",
        "verdict_distribution.png", "samples")
    bar({k: capture[k] for k in caps}, "Capture variant", "capture_distribution.png", "samples")
    heatmap([[cross[c][cap] for cap in caps] for c in CLASSES], CLASSES, caps,
            "Tamper class x capture variant", "class_x_capture.png")
    heatmap([[class_by_type[t][c] for c in CLASSES[1:] ] for t in types], types, CLASSES[1:],
            "Tampered digital variants: class x document type", "class_x_doctype.png")
    grouped_split_bar(split_class, CLASSES, "Samples per class and split", "class_by_split.png")

    result = {
        "base_documents": len(bases),
        "base_by_type": table(base_by_type, types),
        "class_all_rows": table(class_all, CLASSES),
        "class_digital_variants_excluding_base": table(class_variants, CLASSES),
        "class_by_doc_type": {t: dict(class_by_type[t]) for t in types},
        "expected_verdict": table(verdict),
        "severity": table(severity),
        "capture": table(capture, caps),
        "class_x_capture": {c: dict(cross[c]) for c in CLASSES},
        "class_by_split": {s: dict(v) for s, v in split_class.items()},
        "harmless_share_pct": pct(harmless, len(rows)),
        "flags": flags,
        "charts": sorted(p.name for p in CHARTS.glob("*.png")),
    }
    write_json("step3_coverage.json", result)
    print("\n".join(flags))
    return result


if __name__ == "__main__":
    main()
