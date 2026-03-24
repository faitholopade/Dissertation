# Generate all dissertation figures.

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

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "figure.facecolor": "white",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "figure.figsize": (10, 6),
})

COLORS = {
    "keyword": "#2C6FAD",
    "llm": "#E07B39",
    "hybrid": "#4CAF50",
    "manual": "#9C27B0",
}
PAL = sns.color_palette("Set2", 8)


def load_data():
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
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)

    methods = [
        ("Keyword", "annex_domain"),
        ("LLM", None),  # will detect
        ("Hybrid", None),
    ]

    # Find LLM and hybrid columns
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
    data = {}

    for col in df.columns:
        if "domain" in col.lower() or "pattern" in col.lower():
            unk_rate = (df[col] == "unknown").mean()
            # Tidy label text
            label = col.replace("_", " ").replace("annex ", "").title()
            data[label] = unk_rate

    if not data:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    labels = list(data.keys())
    values = list(data.values())

    # Colour bars by method
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
    print(f"  [OK] {filename}")


def fig_source_breakdown(df):
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
    # Load evaluation results if available
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
    rights_labels = ["non_discrimination", "privacy_data_protection",
                     "access_social_protection", "good_administration"]
    harms_labels = ["unfair_exclusion", "privacy_breach",
                    "misinformation_error", "procedural_unfairness"]

    # Check for per-label binary columns
    rights_cols = {}
    harms_cols = {}
    for col in df.columns:
        for r in rights_labels:
            if r in col.lower() and ("right" in col.lower() or "hybrid" in col.lower()):
                rights_cols[r] = col
        for h in harms_labels:
            if h in col.lower() and ("harm" in col.lower() or "hybrid" in col.lower()):
                harms_cols[h] = col

    # Fall back to semicolon-separated string fields
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
                    active_rights.add(r)

        # Get active harms
        active_harms = set()
        if harms_field and harms_field in row.index:
            for h in str(row[harms_field]).split(";"):
                h = h.strip()
                if h in harms_labels:
                    active_harms.add(h)
        else:
            for h, col in harms_cols.items():
                if col in row.index and row[col] == 1:
                    active_harms.add(h)

        for ri, r in enumerate(rights_labels):
            for hi, h in enumerate(harms_labels):
                if r in active_rights and h in active_harms:
                    cooc[ri, hi] += 1

    if cooc.sum() == 0:
        print("  ⚠ No co-occurrence data for rights×harms heatmap")
        return

    fig, ax = plt.subplots(figsize=(9, 6))
    short_rights = ["Non-\ndiscrimination", "Privacy &\nData Prot.", "Social\nProtection", "Good\nAdmin."]
    short_harms = ["Unfair\nExclusion", "Privacy\nBreach", "Misinfo /\nError", "Procedural\nUnfairness"]

    sns.heatmap(cooc, annot=True, fmt=".0f", cmap="YlOrRd",
                xticklabels=short_harms, yticklabels=short_rights, ax=ax)
    ax.set_title("Rights × Harms Co-occurrence Matrix")
    ax.set_xlabel("Harms")
    ax.set_ylabel("Rights Impacted")

    plt.tight_layout()
    plt.savefig("figures/fig_rights_harms_heatmap.png", bbox_inches="tight")
    plt.close()
    print("figures/fig_rights_harms_heatmap.png")


def fig_agreement_bars(df, dimension="rights"):
    if dimension == "rights":
        labels = ["non_discrimination", "privacy_data_protection",
                  "access_social_protection", "good_administration"]
        title = "Per-Label Agreement: Fundamental Rights"
        filename = "figures/fig_rights_agreement.png"
    else:
        labels = ["unfair_exclusion", "privacy_breach",
                  "misinformation_error", "procedural_unfairness"]
        title = "Per-Label Agreement: Harms"
        filename = "figures/fig_harms_agreement.png"

    # Try error analysis CSV first
    for path in [f"output/error_analysis_{dimension}.csv", f"error_analysis_{dimension}.csv"]:
        if os.path.exists(path):
            edf = pd.read_csv(path)
            if "agree" in edf.columns:
                fig, ax = plt.subplots(figsize=(9, 5))
                label_col = edf.columns[0]
                edf.plot(x=label_col, y="agree", kind="bar", ax=ax,
                         color=COLORS["hybrid"], edgecolor="white", legend=False)
                ax.set_ylabel("Agreement Rate")
                ax.set_title(title)
                ax.set_ylim(0, 1)
                ax.axhline(y=0.5, color="red", linestyle="--", alpha=0.4)
                for i, v in enumerate(edf["agree"]):
                    ax.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=9)
                plt.xticks(rotation=30, ha="right")
                plt.tight_layout()
                plt.savefig(filename, bbox_inches="tight")
                plt.close()
                print(f"  [OK] {filename}")
                return

    # Otherwise compute from dataframe columns
    agreements = {}
    for label in labels:
        kw_col = [c for c in df.columns if label in c.lower() and
                  "llm" not in c.lower() and "hybrid" not in c.lower()]
        llm_col = [c for c in df.columns if label in c.lower() and "llm" in c.lower()]

        if kw_col and llm_col:
            agree = (df[kw_col[0]] == df[llm_col[0]]).mean()
            agreements[label.replace("_", "\n")] = agree

    if agreements:
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.bar(agreements.keys(), agreements.values(),
               color=COLORS["hybrid"], edgecolor="white")
        ax.set_ylabel("Agreement Rate")
        ax.set_title(title)
        ax.set_ylim(0, 1)
        ax.axhline(y=0.5, color="red", linestyle="--", alpha=0.4)
        for i, (k, v) in enumerate(agreements.items()):
            ax.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=9)
        plt.tight_layout()
        plt.savefig(filename, bbox_inches="tight")
        plt.close()
        print(f"  [OK] {filename}")
    else:
        print(f"  ⚠ Insufficient data for {filename}")


def fig_pipeline_flow():
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 4)
    ax.axis("off")

    boxes = [
        (0.5, 1.5, "Data\nSources", "#E8F5E9", "AIAAIC\nUSFED\nECtHR"),
        (2.8, 1.5, "Keyword\nFilter", "#E3F2FD", "Employment\nBenefits\nPublic sector"),
        (5.1, 1.5, "Annotation\nTable", "#FFF3E0", f"≥150 records\n6 dimensions"),
        (7.4, 1.5, "LLM\nAnnotation", "#F3E5F5", "GPT-4o\nFew-shot\nJSON mode"),
        (9.7, 1.5, "Hybrid\nMerge", "#E8EAF6", "KW ∪ LLM\nReduce unknowns"),
        (12.0, 1.5, "Evaluation\n& Export", "#FFEBEE", "Gold eval\nJSON-LD\nFigures"),
    ]

    for x, y, label, color, detail in boxes:
        rect = mpatches.FancyBboxPatch((x, y - 0.6), 1.8, 1.2,
                                        boxstyle="round,pad=0.1",
                                        facecolor=color, edgecolor="#333")
        ax.add_patch(rect)
        ax.text(x + 0.9, y + 0.15, label, ha="center", va="center",
                fontsize=10, fontweight="bold")
        ax.text(x + 0.9, y - 0.9, detail, ha="center", va="top",
                fontsize=7, color="#666")

    # Arrows
    for i in range(len(boxes) - 1):
        x1 = boxes[i][0] + 1.8
        x2 = boxes[i+1][0]
        y = 1.5
        ax.annotate("", xy=(x2, y), xytext=(x1, y),
                     arrowprops=dict(arrowstyle="->", color="#333", lw=1.5))

    ax.set_title("Annotation Pipeline Overview", fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig("figures/fig_pipeline_flow.png", bbox_inches="tight")
    plt.close()
    print("figures/fig_pipeline_flow.png")


def main():
    df = load_data()
    print(f"\nGenerating figures from {len(df)} records...\n")

    fig_domain_distribution(df)
    fig_pattern_distribution(df)
    fig_unknown_rates(df)
    fig_source_breakdown(df)
    fig_kappa_summary(df)
    fig_rights_harms_heatmap(df)
    fig_agreement_bars(df, "rights")
    fig_agreement_bars(df, "harms")
    fig_pipeline_flow()

    # Confusion matrices
    llm_domain = [c for c in df.columns if "llm" in c.lower() and "domain" in c.lower()]
    llm_pattern = [c for c in df.columns if "llm" in c.lower() and "pattern" in c.lower()]

    if llm_domain:
        fig_confusion_heatmap(df, "annex_domain", llm_domain[-1],
                              "Confusion Matrix: Annex Domain (Keyword vs LLM)",
                              "figures/fig_confusion_domain.png")
    if llm_pattern:
        fig_confusion_heatmap(df, "system_pattern", llm_pattern[-1],
                              "Confusion Matrix: System Pattern (Keyword vs LLM)",
                              "figures/fig_confusion_pattern.png")

    print("\n[OK] Done! All figures saved.")


if __name__ == "__main__":
    main()
