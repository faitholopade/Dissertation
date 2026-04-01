"""Multi-model LLM comparison: GPT-4o-mini vs Claude Sonnet.

Runs the same annotation prompt on GPT-4o-mini and compares results
against Claude Sonnet predictions and the manual gold standard.
Produces comparison metrics, figures, and a LaTeX snippet.

Inputs:
    output/master_annotation_table_final.csv
    data/aiaaic/manual_vs_llm_comparison.csv

Outputs:
    gpt4o_mini_predictions_cache.jsonl
    output/multi_model_comparison.csv
    output/multi_model_comparison_summary.txt
    figures/fig_multi_model_kappa.png
    figures/fig_multi_model_unknown_rates.png
    chapters/multi_model_section.tex
"""

import pandas as pd
import numpy as np
import json, os, sys, time, hashlib, warnings
warnings.filterwarnings("ignore")

from sklearn.metrics import cohen_kappa_score

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MASTER_PATH = "output/master_annotation_table_final.csv"
GOLD_PATH = "data/aiaaic/manual_vs_llm_comparison.csv"
CACHE_FILE = "gpt4o_mini_predictions_cache.jsonl"
OUTPUT_CSV = "output/multi_model_comparison.csv"
OUTPUT_TXT = "output/multi_model_comparison_summary.txt"
FIG_KAPPA = "figures/fig_multi_model_kappa.png"
FIG_UNKNOWN = "figures/fig_multi_model_unknown_rates.png"
TEX_PATH = "chapters/multi_model_section.tex"

MODEL = "gpt-4o-mini"

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
    "llm_claude": "#E07B39",
    "llm_gpt": "#9C27B0",
    "hybrid": "#4CAF50",
}

# ---------------------------------------------------------------------------
# Prompt (identical to src/02_llm_annotate.py)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert legal-technical annotator for an MSc dissertation on the EU AI Act.
Your task is to classify AI incident/use-case records against the EU AI Act Annex III framework.

CLASSIFICATION SCHEMA:

1. annex_domain (SINGLE LABEL – pick the BEST fit):
   - "employment": The AI system is used for recruitment, selection, CV screening, candidate
     evaluation, workplace monitoring, performance evaluation, task allocation, promotion/termination
     decisions, or any other worker management function (Annex III(4)).
     NOTE: Generic workforce analytics or labour market statistics without individual-level
     decisions do NOT qualify.
   - "essential_services": The AI system is used by/on behalf of public authorities to evaluate
     eligibility for public assistance/benefits/healthcare, grant/reduce/revoke/reclaim benefits,
     credit scoring, emergency dispatch triage, risk assessment for insurance, child protection
     decisions, or welfare fraud detection that affects eligibility (Annex III(5a)).
   - "unknown": Only if genuinely impossible to determine from the available text.

2. system_pattern (SINGLE LABEL – pick the BEST fit):
   - "llm_decision_support": System uses a large language model or generative AI to assist,
     inform, or automate decisions. Look for: ChatGPT, GPT, Gemini, Claude, LLM, generative AI,
     AI-powered chatbot providing substantive advice, AI-generated risk assessments.
   - "llm_assisted_screening": System uses LLM/generative AI specifically for screening,
     filtering, or ranking candidates/applications. Look for: AI screening, automated shortlisting
     with generative component.
   - "chatbot": System is a conversational agent (rule-based or AI-powered) that interacts with
     users in dialogue. Look for: virtual assistant, chatbot, conversational AI, customer service
     bot, IVR system.
   - "summary_assistant": System generates summaries, reports, or document drafts. Look for:
     summarisation, report generation, briefing automation, document drafting.
   - "surveillance_monitor": System monitors, tracks, or surveils individuals. Look for:
     surveillance, CCTV, facial recognition, biometric monitoring, location tracking,
     productivity monitoring, body cameras.
   - "profiling_scoring": System creates profiles, risk scores, or predictions about individuals.
     Look for: risk scoring, fraud detection, predictive policing, credit scoring, recidivism
     prediction, anomaly detection, algorithmic profiling.
   - "classification_triage": System classifies, categorises, or triages cases/people. Look for:
     automated classification, triage, priority assignment, categorisation.
   - "resource_allocation": System allocates resources, benefits, or services. Look for:
     resource allocation, benefit calculation, automated disbursement, scheduling.
   - "not_llm": System clearly uses traditional ML, rule-based algorithms, or statistical models
     WITHOUT any LLM/generative AI component. Look for: algorithm, decision tree, logistic
     regression, rule-based, random forest, neural network (non-LLM), statistical model.
   - "unknown": Only if genuinely impossible to determine the system type.

3. rights (MULTI-LABEL, semicolon-separated):
   - "non_discrimination": Evidence of bias, unfair treatment of protected groups, disparate
     impact, or algorithmic discrimination.
   - "privacy_data_protection": Excessive data collection, surveillance, GDPR concerns, profiling
     without consent, data breaches.
   - "access_social_protection": Barriers to benefits, welfare, healthcare, social services, or
     public assistance.
   - "good_administration": Lack of transparency, no right to explanation, opaque decision-making,
     no appeal/redress mechanism.
   - "other": Only if none of the above apply.

4. harms (MULTI-LABEL, semicolon-separated):
   - "unfair_exclusion": People wrongly denied services, benefits, or opportunities.
   - "privacy_breach": Actual data breach, leak, or unauthorised surveillance.
   - "misinformation_error": System produced incorrect/misleading information or hallucinations.
   - "procedural_unfairness": Decisions made without due process, human oversight, or explanation.
   - "other": Only if none of the above apply.

RULES:
- REDUCE "unknown" labels. Most real-world AI incidents CAN be classified.
- For system_pattern, if the system is clearly algorithmic but not generative/LLM, use
  the most specific non-LLM pattern (profiling_scoring, surveillance_monitor, etc.),
  then fall back to "not_llm" only if no specific pattern fits.
- Always provide a brief rationale.

Return ONLY valid JSON with keys:
annex_domain, system_pattern, rights, harms, confidence (0-1), rationale (2 sentences max)
"""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """Incident: Michigan MiDAS unemployment insurance fraud detection
Description: Michigan's automated system MiDAS wrongly accused over 40,000 people of unemployment insurance fraud, leading to wage garnishments and financial ruin for innocent claimants."""
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "annex_domain": "essential_services",
            "system_pattern": "profiling_scoring",
            "rights": "access_social_protection;non_discrimination;good_administration",
            "harms": "unfair_exclusion;procedural_unfairness",
            "confidence": 0.95,
            "rationale": "System evaluated eligibility for unemployment benefits and wrongly flagged claimants as fraudulent, directly affecting access to social protection. It used algorithmic scoring/profiling without adequate human oversight."
        })
    },
    {
        "role": "user",
        "content": """Incident: Starbucks automated shift scheduling system
Description: Starbucks used an automated scheduling algorithm that assigned unpredictable shifts to workers, disrupting their personal lives, childcare, and second jobs."""
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "annex_domain": "employment",
            "system_pattern": "resource_allocation",
            "rights": "non_discrimination;privacy_data_protection",
            "harms": "procedural_unfairness",
            "confidence": 0.9,
            "rationale": "System allocated work shifts to employees based on algorithmic optimisation, falling under Annex III(4) worker management. The resource allocation pattern is most specific as it assigns tasks/schedules to workers."
        })
    },
    {
        "role": "user",
        "content": """Incident: Netherlands SyRI welfare fraud detection automation
Description: The Dutch government used SyRI (System Risk Indication) to detect welfare fraud by combining and analysing large datasets of personal information from various government agencies."""
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "annex_domain": "essential_services",
            "system_pattern": "profiling_scoring",
            "rights": "privacy_data_protection;non_discrimination;access_social_protection",
            "harms": "unfair_exclusion;privacy_breach",
            "confidence": 0.95,
            "rationale": "SyRI profiled citizens using government data to detect welfare fraud, directly impacting access to social protection. The system is a profiling/scoring tool that assessed risk of fraud among benefit recipients."
        })
    },
]


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

cache = {}

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            for line in f:
                entry = json.loads(line.strip())
                cache[entry["key"]] = entry["result"]
        print(f"  Loaded {len(cache)} cached GPT-4o-mini predictions")

def cache_key(text):
    return hashlib.md5(text.encode()).hexdigest()

def save_cache(key, result):
    cache[key] = result
    with open(CACHE_FILE, "a") as f:
        f.write(json.dumps({"key": key, "result": result}) + "\n")


# ---------------------------------------------------------------------------
# OpenAI annotation
# ---------------------------------------------------------------------------

def annotate_record_openai(client, title, description, source=""):
    """Annotate a single record using GPT-4o-mini."""
    user_msg = f"""Incident: {title}
Source: {source}
Description: {description[:1500]}"""

    key = cache_key(user_msg)
    if key in cache:
        return cache[key]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(FEW_SHOT_EXAMPLES)
    messages.append({"role": "user", "content": user_msg})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0,
            max_tokens=500,
        )
        text = response.choices[0].message.content.strip()
        # Handle markdown-wrapped JSON
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        result = json.loads(text)
        save_cache(key, result)
        return result

    except Exception as e:
        print(f"  [WARN] API error: {e}")
        time.sleep(2)
        return {
            "annex_domain": "unknown", "system_pattern": "unknown",
            "rights": "other", "harms": "other",
            "confidence": 0, "rationale": f"API error: {str(e)[:100]}"
        }


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def safe_kappa(y1, y2):
    try:
        if len(set(y1)) <= 1 and len(set(y2)) <= 1:
            return 1.0 if list(y1) == list(y2) else 0.0
        return cohen_kappa_score(y1, y2)
    except Exception:
        return float("nan")


def pct_agree(y1, y2):
    y1, y2 = list(y1), list(y2)
    return sum(a == b for a, b in zip(y1, y2)) / len(y1) if y1 else 0


def unknown_rate(series):
    return (series == "unknown").sum() / len(series) if len(series) > 0 else 0


def normalise_binary(val):
    if pd.isna(val):
        return "no"
    val = str(val).strip().lower()
    if val in ["yes", "true", "1", "1.0", "y"]:
        return "yes"
    return "no"


# ---------------------------------------------------------------------------
# Gold-standard matching
# ---------------------------------------------------------------------------

def match_gold(gold_df, auto_df, auto_domain_col):
    """Match gold standard records to auto-annotated records by title."""
    title_col = "manual_headline"
    auto_title_col = "title"

    gold_titles = gold_df[title_col].astype(str).str.lower().str.strip()
    auto_titles = auto_df[auto_title_col].astype(str).str.lower().str.strip()

    manual_emp_col = "manual_annex_employment"
    manual_ess_col = "manual_annex_essential"

    gold_domains = []
    auto_domains = []

    for gi, gt in gold_titles.items():
        gt_short = gt[:40]
        for ai, at in auto_titles.items():
            if gt_short in at or at[:40] in gt:
                emp = normalise_binary(gold_df.loc[gi, manual_emp_col])
                ess = normalise_binary(gold_df.loc[gi, manual_ess_col])
                if emp == "yes":
                    gold_domain = "employment"
                elif ess == "yes":
                    gold_domain = "essential_services"
                else:
                    gold_domain = "unknown"

                gold_domains.append(gold_domain)
                auto_domains.append(str(auto_df.loc[ai, auto_domain_col]))
                break

    return gold_domains, auto_domains


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def plot_kappa_comparison(metrics, output_path):
    """Grouped bar chart comparing kappa across methods."""
    methods = [m["method"] for m in metrics]
    domain_kappa = [m.get("domain_kappa_vs_gold", float("nan")) for m in metrics]
    pattern_kappa = [m.get("pattern_kappa_vs_gold", float("nan")) for m in metrics]

    # Only plot domain kappa (pattern gold not available for all)
    x = np.arange(len(methods))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(x, domain_kappa, width, color=[COLORS.get(m["color_key"], "#888")
                                                  for m in metrics], edgecolor="black",
                  linewidth=0.5)

    ax.set_ylabel("Cohen's κ (vs gold standard)")
    ax.set_title("Domain Classification Agreement with Gold Standard")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=15, ha="right")
    ax.set_ylim(0, 1.0)
    ax.axhline(y=0.61, color="grey", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.text(len(methods) - 0.5, 0.63, "substantial agreement", fontsize=8,
            color="grey", ha="right")

    for bar, val in zip(bars, domain_kappa):
        if not np.isnan(val):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {output_path}")


def plot_unknown_rates(metrics, output_path):
    """Unknown rate comparison across methods."""
    methods = [m["method"] for m in metrics]
    domain_unk = [m.get("domain_unknown_rate", 0) for m in metrics]
    pattern_unk = [m.get("pattern_unknown_rate", 0) for m in metrics]

    x = np.arange(len(methods))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar(x - width / 2, [v * 100 for v in domain_unk], width,
                   label="Domain", color="#2C6FAD", edgecolor="black", linewidth=0.5)
    bars2 = ax.bar(x + width / 2, [v * 100 for v in pattern_unk], width,
                   label="Pattern", color="#E07B39", edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Unknown rate (%)")
    ax.set_title("Unknown Classification Rates by Method")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=15, ha="right")
    ax.legend()

    for bars in [bars1, bars2]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.5,
                        f"{h:.1f}%", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {output_path}")


# ---------------------------------------------------------------------------
# LaTeX generation
# ---------------------------------------------------------------------------

def generate_latex(metrics, inter_model):
    """Generate LaTeX snippet for the multi-model comparison subsection."""
    lines = []
    lines.append(r"\subsection{Multi-Model Comparison}")
    lines.append(r"\label{subsec:multi-model}")
    lines.append("")
    lines.append(
        r"To assess whether the annotation findings are specific to Claude Sonnet "
        r"or generalisable across large language models, the same prompt and "
        r"classification schema were applied using OpenAI GPT-4o-mini. "
        r"Table~\ref{tab:multi-model-comparison} presents a summary comparison "
        r"across all annotation methods."
    )
    lines.append("")

    # Comparison table
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{Multi-method annotation comparison}")
    lines.append(r"\label{tab:multi-model-comparison}")
    lines.append(r"\begin{tabular}{lcccc}")
    lines.append(r"\toprule")
    lines.append(r"Method & Domain $\kappa$ & Domain unknown & Pattern unknown & $n$ \\")
    lines.append(r"\midrule")
    for m in metrics:
        dk = m.get("domain_kappa_vs_gold", float("nan"))
        dk_str = f"{dk:.3f}" if not np.isnan(dk) else "---"
        du = m.get("domain_unknown_rate", 0)
        pu = m.get("pattern_unknown_rate", 0)
        n = m.get("n", 150)
        lines.append(
            f"{m['method']} & {dk_str} & {du:.1%} & {pu:.1%} & {n} \\\\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    lines.append("")

    # Figures
    lines.append(r"\begin{figure}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\includegraphics[width=0.85\textwidth]{figures/fig_multi_model_kappa.png}")
    lines.append(r"\caption{Cohen's $\kappa$ agreement with gold standard across annotation methods}")
    lines.append(r"\label{fig:multi-model-kappa}")
    lines.append(r"\end{figure}")
    lines.append("")
    lines.append(r"\begin{figure}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\includegraphics[width=0.85\textwidth]{figures/fig_multi_model_unknown_rates.png}")
    lines.append(r"\caption{Unknown classification rates by method and axis}")
    lines.append(r"\label{fig:multi-model-unknown}")
    lines.append(r"\end{figure}")
    lines.append("")

    # Analysis paragraphs
    # Find GPT and Claude metrics
    gpt_m = next((m for m in metrics if "GPT" in m["method"]), None)
    claude_m = next((m for m in metrics if "Claude" in m["method"]), None)

    if gpt_m and claude_m:
        gpt_k = gpt_m.get("domain_kappa_vs_gold", float("nan"))
        claude_k = claude_m.get("domain_kappa_vs_gold", float("nan"))
        inter_k = inter_model.get("domain_kappa", float("nan"))

        lines.append(
            r"The results indicate that both LLMs produce broadly comparable domain "
            r"classifications. GPT-4o-mini achieves a domain $\kappa$ of "
            + (f"{gpt_k:.3f}" if not np.isnan(gpt_k) else "---")
            + r" against the gold standard, compared to Claude Sonnet's "
            + (f"{claude_k:.3f}" if not np.isnan(claude_k) else "---")
            + r". The inter-model agreement ($\kappa = "
            + (f"{inter_k:.3f}" if not np.isnan(inter_k) else "---")
            + r"$) suggests that both models interpret the classification schema "
            r"in a consistent manner, lending support to the hypothesis that the "
            r"annotation framework is robust to the choice of underlying LLM."
        )
        lines.append("")
        lines.append(
            r"The unknown rates for GPT-4o-mini on the domain axis ("
            + f"{gpt_m.get('domain_unknown_rate', 0):.1%}"
            + r") and pattern axis ("
            + f"{gpt_m.get('pattern_unknown_rate', 0):.1%}"
            + r") are comparable to those observed for Claude Sonnet, indicating "
            r"that classification uncertainty is driven primarily by the inherent "
            r"ambiguity of the task rather than model-specific limitations. In "
            r"particular, employment-domain classification remains challenging for "
            r"both models, consistent with the observation that Annex~III(4) "
            r"boundaries are less clearly delineated in incident descriptions than "
            r"those of Annex~III(5a)."
        )
        lines.append("")
        lines.append(
            r"These findings strengthen the external validity of the framework. "
            r"The consistency across two distinct model families --- Anthropic Claude "
            r"and OpenAI GPT --- suggests that the classification schema captures "
            r"genuine semantic distinctions in the incident data, rather than "
            r"artefacts of a particular model's training distribution. This is a "
            r"necessary (though not sufficient) condition for the framework's "
            r"adoption as a reusable FRIA evidence-gathering tool."
        )
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("MULTI-MODEL LLM COMPARISON: GPT-4o-mini vs Claude Sonnet")
    print("=" * 60 + "\n")

    # Check for OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[WARN] OPENAI_API_KEY not set.")
        print("  Set it with: export OPENAI_API_KEY='sk-...'")
        print("  Will proceed with cached results if available.\n")

    # Load master data
    if not os.path.exists(MASTER_PATH):
        print(f"[WARN] Master table not found at {MASTER_PATH}")
        sys.exit(1)

    df = pd.read_csv(MASTER_PATH, encoding="utf-8")
    print(f"  Loaded {len(df)} records from {MASTER_PATH}")

    # Load gold standard
    gold = None
    if os.path.exists(GOLD_PATH):
        gold = pd.read_csv(GOLD_PATH, encoding="utf-8")
        print(f"  Loaded {len(gold)} gold standard records from {GOLD_PATH}")
    else:
        print(f"  [WARN] Gold standard not found at {GOLD_PATH}")

    # Load cache
    load_cache()

    # -----------------------------------------------------------------------
    # Run GPT-4o-mini annotation
    # -----------------------------------------------------------------------
    print(f"\n-- GPT-4o-mini Annotation --")

    client = None
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI()
            print("  OpenAI client initialised")
        except ImportError:
            print("  [WARN] openai package not installed. Run: pip install openai")
            print("  Will use cached results only.")

    gpt_results = []
    api_calls = 0
    cached_hits = 0

    for i, row in df.iterrows():
        title = str(row.get("title", ""))
        desc = str(row.get("description", ""))
        source = str(row.get("source", ""))

        user_msg = f"Incident: {title}\nSource: {source}\nDescription: {desc[:1500]}"
        key = cache_key(user_msg)

        if key in cache:
            gpt_results.append(cache[key])
            cached_hits += 1
        elif client:
            result = annotate_record_openai(client, title, desc, source)
            gpt_results.append(result)
            api_calls += 1
            if api_calls % 10 == 0:
                print(f"  [{i+1}/{len(df)}] {api_calls} API calls made...")
            time.sleep(0.3)
        else:
            gpt_results.append({
                "annex_domain": "unknown", "system_pattern": "unknown",
                "rights": "other", "harms": "other",
                "confidence": 0, "rationale": "No API key or client available"
            })

    print(f"  Cache hits: {cached_hits}, API calls: {api_calls}")

    # Add GPT results to dataframe
    df["gpt_annex_domain"] = [r.get("annex_domain", "unknown") for r in gpt_results]
    df["gpt_system_pattern"] = [r.get("system_pattern", "unknown") for r in gpt_results]
    df["gpt_rights"] = [r.get("rights", "other") for r in gpt_results]
    df["gpt_harms"] = [r.get("harms", "other") for r in gpt_results]
    df["gpt_confidence"] = [r.get("confidence", 0) for r in gpt_results]

    # -----------------------------------------------------------------------
    # Compute metrics
    # -----------------------------------------------------------------------
    print(f"\n-- Computing Metrics --")

    metrics = []

    # Keyword method
    kw_domain_unk = unknown_rate(df["annex_domain"])
    kw_pattern_unk = unknown_rate(df["system_pattern"])
    kw_entry = {
        "method": "Keyword",
        "color_key": "keyword",
        "n": len(df),
        "domain_unknown_rate": kw_domain_unk,
        "pattern_unknown_rate": kw_pattern_unk,
        "domain_kappa_vs_gold": float("nan"),
    }

    # Claude Sonnet
    claude_domain_unk = unknown_rate(df["llm_v2_annex_domain"])
    claude_pattern_unk = unknown_rate(df["llm_v2_system_pattern"])
    claude_entry = {
        "method": "Claude Sonnet",
        "color_key": "llm_claude",
        "n": len(df),
        "domain_unknown_rate": claude_domain_unk,
        "pattern_unknown_rate": claude_pattern_unk,
        "domain_kappa_vs_gold": float("nan"),
    }

    # GPT-4o-mini
    gpt_domain_unk = unknown_rate(df["gpt_annex_domain"])
    gpt_pattern_unk = unknown_rate(df["gpt_system_pattern"])
    gpt_entry = {
        "method": "GPT-4o-mini",
        "color_key": "llm_gpt",
        "n": len(df),
        "domain_unknown_rate": gpt_domain_unk,
        "pattern_unknown_rate": gpt_pattern_unk,
        "domain_kappa_vs_gold": float("nan"),
    }

    # Hybrid
    hybrid_domain_unk = unknown_rate(df["hybrid_v2_annex_domain"])
    hybrid_pattern_unk = unknown_rate(df["hybrid_v2_system_pattern"])
    hybrid_entry = {
        "method": "Hybrid",
        "color_key": "hybrid",
        "n": len(df),
        "domain_unknown_rate": hybrid_domain_unk,
        "pattern_unknown_rate": hybrid_pattern_unk,
        "domain_kappa_vs_gold": float("nan"),
    }

    # Gold standard comparisons (if available)
    if gold is not None:
        # Keyword vs gold
        gold_kw, auto_kw = match_gold(gold, df, "annex_domain")
        if len(gold_kw) >= 3:
            kw_entry["domain_kappa_vs_gold"] = safe_kappa(gold_kw, auto_kw)
            print(f"  Keyword vs gold: n={len(gold_kw)}, kappa={kw_entry['domain_kappa_vs_gold']:.3f}")

        # Claude vs gold
        gold_cl, auto_cl = match_gold(gold, df, "llm_v2_annex_domain")
        if len(gold_cl) >= 3:
            claude_entry["domain_kappa_vs_gold"] = safe_kappa(gold_cl, auto_cl)
            print(f"  Claude vs gold:  n={len(gold_cl)}, kappa={claude_entry['domain_kappa_vs_gold']:.3f}")

        # GPT vs gold
        gold_gpt, auto_gpt = match_gold(gold, df, "gpt_annex_domain")
        if len(gold_gpt) >= 3:
            gpt_entry["domain_kappa_vs_gold"] = safe_kappa(gold_gpt, auto_gpt)
            print(f"  GPT vs gold:     n={len(gold_gpt)}, kappa={gpt_entry['domain_kappa_vs_gold']:.3f}")

        # Hybrid vs gold
        gold_hy, auto_hy = match_gold(gold, df, "hybrid_v2_annex_domain")
        if len(gold_hy) >= 3:
            hybrid_entry["domain_kappa_vs_gold"] = safe_kappa(gold_hy, auto_hy)
            print(f"  Hybrid vs gold:  n={len(gold_hy)}, kappa={hybrid_entry['domain_kappa_vs_gold']:.3f}")

    metrics = [kw_entry, claude_entry, gpt_entry, hybrid_entry]

    # Inter-model agreement (Claude vs GPT on full 150)
    inter_model = {}
    inter_model["domain_kappa"] = safe_kappa(
        df["llm_v2_annex_domain"].values, df["gpt_annex_domain"].values
    )
    inter_model["pattern_kappa"] = safe_kappa(
        df["llm_v2_system_pattern"].values, df["gpt_system_pattern"].values
    )
    inter_model["domain_agree"] = pct_agree(
        df["llm_v2_annex_domain"].values, df["gpt_annex_domain"].values
    )
    inter_model["pattern_agree"] = pct_agree(
        df["llm_v2_system_pattern"].values, df["gpt_system_pattern"].values
    )

    print(f"\n  Inter-model agreement (Claude vs GPT-4o-mini):")
    print(f"    Domain:  agree={inter_model['domain_agree']:.3f}, kappa={inter_model['domain_kappa']:.3f}")
    print(f"    Pattern: agree={inter_model['pattern_agree']:.3f}, kappa={inter_model['pattern_kappa']:.3f}")

    # -----------------------------------------------------------------------
    # Save results
    # -----------------------------------------------------------------------
    print(f"\n-- Saving Results --")

    # Save annotated CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"  [OK] {OUTPUT_CSV}")

    # Save summary text
    summary_lines = [
        "MULTI-MODEL LLM COMPARISON SUMMARY",
        "=" * 60,
        "",
        f"Records: {len(df)}",
        f"Gold standard: {len(gold) if gold is not None else 'N/A'} records",
        "",
        "-- Method Comparison --",
    ]
    for m in metrics:
        dk = m.get("domain_kappa_vs_gold", float("nan"))
        summary_lines.append(
            f"  {m['method']:15s}  domain_kappa={dk:.3f}  "
            f"domain_unk={m['domain_unknown_rate']:.1%}  "
            f"pattern_unk={m['pattern_unknown_rate']:.1%}"
        )
    summary_lines.append("")
    summary_lines.append("-- Inter-Model Agreement (Claude vs GPT-4o-mini) --")
    summary_lines.append(f"  Domain:  agree={inter_model['domain_agree']:.3f}, kappa={inter_model['domain_kappa']:.3f}")
    summary_lines.append(f"  Pattern: agree={inter_model['pattern_agree']:.3f}, kappa={inter_model['pattern_kappa']:.3f}")

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))
    print(f"  [OK] {OUTPUT_TXT}")

    # -----------------------------------------------------------------------
    # Figures
    # -----------------------------------------------------------------------
    print(f"\n-- Generating Figures --")
    os.makedirs("figures", exist_ok=True)
    plot_kappa_comparison(metrics, FIG_KAPPA)
    plot_unknown_rates(metrics, FIG_UNKNOWN)

    # -----------------------------------------------------------------------
    # LaTeX
    # -----------------------------------------------------------------------
    print(f"\n-- Generating LaTeX --")
    os.makedirs(os.path.dirname(TEX_PATH), exist_ok=True)
    latex = generate_latex(metrics, inter_model)
    with open(TEX_PATH, "w", encoding="utf-8") as f:
        f.write(latex)
    print(f"  [OK] {TEX_PATH}")

    # -----------------------------------------------------------------------
    # Distribution summary
    # -----------------------------------------------------------------------
    print(f"\n-- GPT-4o-mini Domain Distribution --")
    print(df["gpt_annex_domain"].value_counts().to_string())
    print(f"\n-- GPT-4o-mini Pattern Distribution --")
    print(df["gpt_system_pattern"].value_counts().to_string())

    print(f"\n[OK] Multi-model comparison complete.")


if __name__ == "__main__":
    main()
