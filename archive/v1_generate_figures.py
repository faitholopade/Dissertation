# generate_figures.py — Generate dissertation figures from annotation results.

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import numpy as np


def ensure_llm_table():
    path = "master_annotation_table_llm.csv"
    if not os.path.exists(path):
        sys.exit(f"ERROR: {path} not found. Run llm_annotate.py first.")
    return pd.read_csv(path).fillna("")


def fig_domain_distribution(df):
    ct = pd.crosstab(df["source"], df["annex_domain"])
    ax = ct.plot(kind="bar", figsize=(8, 5), colormap="Set2")
    ax.set_ylabel("Count")
    ax.set_title("Annex Domain Distribution by Source (Keyword)")
    ax.legend(title="Domain")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig("fig_domain_distribution.png", dpi=150)
    plt.close()
    print("[OK] fig_domain_distribution.png")


def fig_pattern_comparison(df):
    kw = df["system_pattern"].value_counts().rename("Keyword")
    llm = df["llm_system_pattern"].value_counts().rename("LLM")
    combined = pd.concat([kw, llm], axis=1).fillna(0)
    ax = combined.plot(kind="bar", figsize=(9, 5), colormap="Paired")
    ax.set_ylabel("Count")
    ax.set_title("System Pattern: Keyword vs LLM")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig("fig_pattern_distribution.png", dpi=150)
    plt.close()
    print("[OK] fig_pattern_distribution.png")


def fig_unknown_rates(df):
    n = len(df)
    data = {
        "Keyword domain":  (df["annex_domain"] == "unknown").sum() / n * 100,
        "LLM domain":      (df["llm_annex_domain"] == "unknown").sum() / n * 100,
        "Keyword pattern":   (df["system_pattern"] == "unknown").sum() / n * 100,
        "LLM pattern":      (df["llm_system_pattern"] == "unknown").sum() / n * 100,
    }
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(data.keys(), data.values(), color=["#4c72b0", "#55a868", "#4c72b0", "#55a868"])
    ax.set_ylabel("% Unknown")
    ax.set_title("Unknown Label Rates: Keyword vs LLM")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig("fig_unknown_rates.png", dpi=150)
    plt.close()
    print("[OK] fig_unknown_rates.png")


def fig_confusion_domain(df):
    labels = ["employment", "essential_services", "unknown"]
    cm = confusion_matrix(df["annex_domain"], df["llm_annex_domain"], labels=labels)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", xticklabels=labels, yticklabels=labels,
                cmap="Blues", ax=ax)
    ax.set_xlabel("LLM label")
    ax.set_ylabel("Keyword label")
    ax.set_title("Confusion Matrix: Annex Domain (Keyword vs LLM)")
    plt.tight_layout()
    plt.savefig("fig_confusion_domain.png", dpi=150)
    plt.close()
    print("[OK] fig_confusion_domain.png")


def fig_rights_agreement(df):
    labels = ["privacy_data_protection", "non_discrimination",
              "access_social_protection", "good_administration"]
    agrees = []
    for label in labels:
        kw  = df["rights"].str.contains(label, na=False).astype(int)
        llm = df["llm_rights"].str.contains(label, na=False).astype(int)
        agrees.append((kw == llm).mean() * 100)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(labels, agrees, color="#4c72b0")
    ax.set_xlabel("% Agreement")
    ax.set_title("Per-Label Rights Agreement (Keyword vs LLM)")
    ax.set_xlim(0, 105)
    for i, v in enumerate(agrees):
        ax.text(v + 1, i, f"{v:.1f}%", va="center")
    plt.tight_layout()
    plt.savefig("fig_rights_agreement.png", dpi=150)
    plt.close()
    print("[OK] fig_rights_agreement.png")


def fig_harms_agreement(df):
    labels = ["unfair_exclusion", "privacy_breach",
              "misinformation_error", "procedural_unfairness"]
    agrees = []
    for label in labels:
        kw  = df["harms"].str.contains(label, na=False).astype(int)
        llm = df["llm_harms"].str.contains(label, na=False).astype(int)
        agrees.append((kw == llm).mean() * 100)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(labels, agrees, color="#c44e52")
    ax.set_xlabel("% Agreement")
    ax.set_title("Per-Label Harms Agreement (Keyword vs LLM)")
    ax.set_xlim(0, 105)
    for i, v in enumerate(agrees):
        ax.text(v + 1, i, f"{v:.1f}%", va="center")
    plt.tight_layout()
    plt.savefig("fig_harms_agreement.png", dpi=150)
    plt.close()
    print("[OK] fig_harms_agreement.png")


if __name__ == "__main__":
    df = ensure_llm_table()
    print(f"Generating figures from {len(df)} records...\n")
    fig_domain_distribution(df)
    fig_pattern_comparison(df)
    fig_unknown_rates(df)
    fig_confusion_domain(df)
    fig_rights_agreement(df)
    fig_harms_agreement(df)
    print("\nDone! All figures saved.")
