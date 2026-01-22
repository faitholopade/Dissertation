#!/usr/bin/env python3
"""
generate_figures_v2.py  –  Generate all dissertation figures.

Produces:
  fig_domain_distribution.png       – Annex III domain distribution (3 methods)
  fig_pattern_distribution.png      – System pattern distribution (3 methods)
  fig_unknown_rates.png             – Unknown rates comparison across methods
  fig_confusion_domain.png          – Confusion matrix heatmap (domain)
  fig_confusion_pattern.png         – Confusion matrix heatmap (system pattern)
  fig_rights_agreement.png          – Per-label agreement for rights
  fig_harms_agreement.png           – Per-label agreement for harms
  fig_source_breakdown.png          – Records per data source
  fig_kappa_summary.png             – Cohen's kappa across all dimensions
  fig_method_comparison_radar.png   – Radar chart comparing methods
  fig_pipeline_flow.png             – Annotation pipeline flow diagram
  fig_rights_harms_heatmap.png      – Co-occurrence of rights × harms

Run:
    python generate_figures_v2.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from matplotlib.gridspec import GridSpec
import os, sys, warnings
warnings.filterwarnings("ignore")

# ─── Style config ────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "figure.facecolor": "white",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "figure.figsize": (10, 6),
})

# TCD-friendly colour palette
COLORS = {
    "keyword": "#2C6FAD",
    "llm": "#E07B39",
    "hybrid": "#4CAF50",
    "manual": "#9C27B0",
}
PAL = sns.color_palette("Set2", 8)


def load_data():
    """Load the best available annotation table."""
    for path in [
        "output/master_annotation_table_llm_v2.csv",
        "output/master_annotation_table_hybrid.csv",
        "output/master_annotation_table_llm.csv",
        "data/master_annotation_table_v01.csv",
    ]:
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"Loaded {len(df)} records from {path}")
            return df
    print("⚠ No annotation table found!")
    sys.exit(1)


def fig_domain_distribution(df):
    """Bar chart comparing domain distribution across methods."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)

    methods = [
        ("Keyword", "annex_domain"),
        ("LLM", None),  # will detect
        ("Hybrid", None),
    ]

    # Detect LLM and hybrid columns
    for col in df.columns:
        if "llm" in col.lower() and "domain" in col.lower() and "v2" not in col.lower():
            methods[1] = ("LLM", col)
        if "llm_v2" in col.lower() and "domain" in col.lower():
            methods[1] = ("LLM v2", col)
        if "hybrid" in col.lower() and "domain" in col.lower() and "v2" not in col.lower():
            methods[2] = ("Hybrid", col)
        if "hybrid_v2" in col.lower() and "domain" in col.lower():
            methods[2] = ("Hybrid v2", col)

    colors = [COLORS["keyword"], COLORS["llm"], COLORS["hybrid"]]

    for ax, (label, col), color in zip(axes, methods, colors):
        if col and col in df.columns:
            counts = df[col].value_counts()
            counts.plot(kind="barh", ax=ax, color=color, edgecolor="white")
            ax.set_title(label)
            ax.set_xlabel("Count")
            for i, (v, c) in enumerate(zip(counts.values, counts.index)):
                ax.text(v + 0.5, i, str(v), va="center", fontsize=10)
        else:
            ax.set_title(f"{label} (not available)")

    fig.suptitle("Annex III Domain Distribution by Annotation Method", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig("figures/fig_domain_distribution.png", bbox_inches="tight")
    plt.close()
    print("figures/fig_domain_distribution.png")


def fig_pattern_distribution(df):
    """Bar chart for system pattern distribution."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 6), sharey=True)

    method_cols = [
        ("Keyword", "system_pattern"),
    ]
    for col in df.columns:
        if "llm" in col.lower() and "pattern" in col.lower():
            key = "LLM v2" if "v2" in col.lower() else "LLM"
            method_cols.append((key, col))
        if "hybrid" in col.lower() and "pattern" in col.lower():
            key = "Hybrid v2" if "v2" in col.lower() else "Hybrid"
            method_cols.append((key, col))

    method_cols = method_cols[:3]  # max 3
    colors = [COLORS["keyword"], COLORS["llm"], COLORS["hybrid"]]

    for ax, (label, col), color in zip(axes, method_cols, colors):
        if col in df.columns:
            counts = df[col].value_counts()
            counts.plot(kind="barh", ax=ax, color=color, edgecolor="white")
            ax.set_title(label)
            ax.set_xlabel("Count")
        else:
            ax.set_title(f"{label} (N/A)")

    fig.suptitle("System Pattern Distribution by Annotation Method", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig("figures/fig_pattern_distribution.png", bbox_inches="tight")
    plt.close()
    print("figures/fig_pattern_distribution.png")


def fig_unknown_rates(df):
    """Grouped bar chart of unknown rates across methods."""
    data = {}

    for col in df.columns:
        if "domain" in col.lower() or "pattern" in col.lower():
            unk_rate = (df[col] == "unknown").mean()
            # Clean up label
            label = col.replace("_", " ").replace("annex ", "").title()
            data[label] = unk_rate

    if not data:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    labels = list(data.keys())
    values = list(data.values())

    # Color by method type
    bar_colors = []
    for l in labels:
        if "llm" in l.lower() or "Llm" in l:
            bar_colors.append(COLORS["llm"])
        elif "hybrid" in l.lower() or "Hybrid" in l:
            bar_colors.append(COLORS["hybrid"])
        else:
            bar_colors.append(COLORS["keyword"])

    bars = ax.barh(labels, values, color=bar_colors, edgecolor="white")
    ax.set_xlabel("Unknown Rate")
    ax.set_title("Proportion of 'Unknown' Labels by Method and Dimension")
    ax.set_xlim(0, 1)

    for bar, val in zip(bars, values):
        ax.text(val + 0.01, bar.get_y() + bar.get_height()/2,
