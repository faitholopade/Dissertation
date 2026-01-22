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
                f"{val:.1%}", va="center", fontsize=9)

    # Legend
    patches = [
        mpatches.Patch(color=COLORS["keyword"], label="Keyword"),
        mpatches.Patch(color=COLORS["llm"], label="LLM"),
        mpatches.Patch(color=COLORS["hybrid"], label="Hybrid"),
    ]
    ax.legend(handles=patches, loc="lower right")

    plt.tight_layout()
    plt.savefig("figures/fig_unknown_rates.png", bbox_inches="tight")
    plt.close()
    print("figures/fig_unknown_rates.png")


def fig_confusion_heatmap(df, kw_col, llm_col, title, filename):
    """Confusion matrix heatmap."""
    if kw_col not in df.columns or llm_col not in df.columns:
        print(f"  ⚠ Skipping {filename}: columns not found")
        return

    from sklearn.metrics import confusion_matrix as cm_func

    labels = sorted(set(df[kw_col].unique()) | set(df[llm_col].unique()))
    matrix = cm_func(df[kw_col], df[llm_col], labels=labels)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues",
                xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_ylabel("Keyword")
    ax.set_xlabel("LLM")
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(filename, bbox_inches="tight")
    plt.close()
    print(f"  ✅ {filename}")


def fig_source_breakdown(df):
    """Pie/bar chart of records per source."""
    if "source" not in df.columns:
        return

    counts = df["source"].value_counts()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Pie chart
    ax1.pie(counts.values, labels=counts.index, autopct="%1.0f%%",
            colors=PAL[:len(counts)], startangle=90)
    ax1.set_title("Records by Source")

    # Bar chart with detail
    counts.plot(kind="bar", ax=ax2, color=PAL[:len(counts)], edgecolor="white")
    ax2.set_ylabel("Number of Records")
    ax2.set_title("Source Distribution")
    ax2.set_xticklabels(counts.index, rotation=0)
    for i, v in enumerate(counts.values):
        ax2.text(i, v + 0.5, str(v), ha="center", fontsize=11, fontweight="bold")

    plt.tight_layout()
    plt.savefig("figures/fig_source_breakdown.png", bbox_inches="tight")
    plt.close()
    print("figures/fig_source_breakdown.png")


def fig_kappa_summary(df):
    """Bar chart of Cohen's kappa across all evaluation dimensions."""
    # Try to load evaluation results
    eval_data = []
    for path in ["evaluate_results.csv", "output/gold_evaluation_results.csv"]:
        if os.path.exists(path):
            edf = pd.read_csv(path)
            if "kappa" in edf.columns:
                for _, row in edf.iterrows():
                    label = row.get("label", row.get("Dimension", ""))
                    kappa = row.get("kappa", row.get("Cohen's κ", 0))
                    try:
                        kappa = float(kappa)
                    except (ValueError, TypeError):
                        continue
                    eval_data.append({"label": str(label), "kappa": kappa})

    if not eval_data:
        # Calculate from df directly
        from sklearn.metrics import cohen_kappa_score
        pairs = [
            ("annex_domain", "llm_annex_domain"),
            ("system_pattern", "llm_system_pattern"),
        ]
        # Add v2 columns if available
        for col in df.columns:
            if "llm_v2" in col:
                base = col.replace("llm_v2_", "")
                if base in df.columns:
                    pairs.append((base, col))

        for kw_col, llm_col in pairs:
            if kw_col in df.columns and llm_col in df.columns:
                try:
                    k = cohen_kappa_score(df[kw_col].fillna("unknown"),
                                          df[llm_col].fillna("unknown"))
                    eval_data.append({
                        "label": f"{kw_col}\n(kw vs llm)",
                        "kappa": round(k, 3)
                    })
                except:
                    pass

    if not eval_data:
        print("  ⚠ No evaluation data for kappa summary")
        return

    edf = pd.DataFrame(eval_data)
    fig, ax = plt.subplots(figsize=(10, max(5, len(edf) * 0.5)))

    colors = ["#E74C3C" if k < 0.2 else "#F39C12" if k < 0.4
              else "#27AE60" if k < 0.6 else "#2980B9"
              for k in edf["kappa"]]

    bars = ax.barh(edf["label"], edf["kappa"], color=colors, edgecolor="white")
    ax.axvline(x=0.2, color="red", linestyle="--", alpha=0.5, label="Poor (0.2)")
    ax.axvline(x=0.4, color="orange", linestyle="--", alpha=0.5, label="Fair (0.4)")
    ax.axvline(x=0.6, color="green", linestyle="--", alpha=0.5, label="Moderate (0.6)")

    for bar, val in zip(bars, edf["kappa"]):
        ax.text(max(val + 0.02, 0.02), bar.get_y() + bar.get_height()/2,
                f"κ={val:.3f}", va="center", fontsize=9)

    ax.set_xlabel("Cohen's κ")
    ax.set_title("Inter-Method Agreement (Cohen's Kappa) Across Dimensions")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_xlim(-0.4, 1.0)

    plt.tight_layout()
    plt.savefig("figures/fig_kappa_summary.png", bbox_inches="tight")
    plt.close()
    print("figures/fig_kappa_summary.png")


def fig_rights_harms_heatmap(df):
    """Co-occurrence matrix of rights × harms."""
    rights_labels = ["non_discrimination", "privacy_data_protection",
                     "access_social_protection", "good_administration"]
    harms_labels = ["unfair_exclusion", "privacy_breach",
                    "misinformation_error", "procedural_unfairness"]

    # Detect rights/harms columns
    rights_cols = {}
    harms_cols = {}
    for col in df.columns:
        for r in rights_labels:
            if r in col.lower() and ("right" in col.lower() or "hybrid" in col.lower()):
                rights_cols[r] = col
        for h in harms_labels:
            if h in col.lower() and ("harm" in col.lower() or "hybrid" in col.lower()):
                harms_cols[h] = col

    # If no separate columns, try parsing semicolon-separated fields
    rights_field = None
    harms_field = None
    for col in df.columns:
        if col in ["rights", "llm_v2_rights", "hybrid_rights"]:
            rights_field = col
        if col in ["harms", "llm_v2_harms", "hybrid_harms"]:
            harms_field = col

    cooc = np.zeros((len(rights_labels), len(harms_labels)))

    for _, row in df.iterrows():
        # Get active rights
        active_rights = set()
        if rights_field and rights_field in row.index:
            for r in str(row[rights_field]).split(";"):
                r = r.strip()
                if r in rights_labels:
                    active_rights.add(r)
        else:
            for r, col in rights_cols.items():
                if col in row.index and row[col] == 1:
