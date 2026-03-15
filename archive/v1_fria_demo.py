# FRIA-style retrieval demos — query annotated incidents by scenario

import os
import pandas as pd


def load_table() -> pd.DataFrame:
    for path in ["master_annotation_table_hybrid.csv",
                  "master_annotation_table_llm.csv",
                  "master_annotation_table.csv"]:
        if os.path.exists(path):
            print(f"(Using {path})")
            return pd.read_csv(path).fillna("")
    raise FileNotFoundError("No annotation table found.")


def _best_domain(row):
    if "hybrid_annex_domain" in row.index:
        return row["hybrid_annex_domain"]
    if "llm_annex_domain" in row.index and row.get("annex_domain") == "unknown":
        return row["llm_annex_domain"]
    return row.get("annex_domain", "unknown")


def search_cases(
    df: pd.DataFrame,
    annex_domain: str | None = None,
    right_contains: str | None = None,
    harm_contains: str | None = None,
    pattern_contains: str | None = None,
) -> pd.DataFrame:
    out = df.copy()

    if annex_domain:
        domain_cols = [c for c in ["annex_domain", "llm_annex_domain", "hybrid_annex_domain"]
                       if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in domain_cols:
            mask |= (out[col] == annex_domain)
        out = out[mask]

    if right_contains:
        rights_cols = [c for c in ["rights", "llm_rights"] if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in rights_cols:
            mask |= out[col].str.contains(right_contains, na=False)
        out = out[mask]

    if harm_contains:
        harm_cols = [c for c in ["harms", "llm_harms"] if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in harm_cols:
            mask |= out[col].str.contains(harm_contains, na=False)
        out = out[mask]

    if pattern_contains:
        pat_cols = [c for c in ["system_pattern", "llm_system_pattern", "hybrid_system_pattern"]
                    if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in pat_cols:
            mask |= out[col].str.contains(pattern_contains, na=False)
        out = out[mask]

    return out


DISPLAY_COLS = ["source", "source_id", "title", "annex_domain",
                "system_pattern", "rights", "harms"]


def _show(subset, extra_cols=None):
    cols = DISPLAY_COLS.copy()
    if extra_cols:
        cols.extend([c for c in extra_cols if c in subset.columns])
    cols = [c for c in cols if c in subset.columns]
    print(subset[cols].head(15).to_markdown(index=False))
    print(f"\n-> {len(subset)} total matching records")


def scenario_1():
    print("\n" + "=" * 70)
    print("SCENARIO 1: Welfare eligibility chatbot — privacy risks")
    print("=" * 70)
    df = load_table()
    subset = search_cases(df, annex_domain="essential_services",
                          right_contains="privacy_data_protection")
    if subset.empty:
        subset = search_cases(df, annex_domain="essential_services")
    _show(subset)


def scenario_2():
    print("\n" + "=" * 70)
    print("SCENARIO 2: LLM-assisted recruitment screening — discrimination")
    print("=" * 70)
    df = load_table()
    subset = search_cases(df, annex_domain="employment",
                          right_contains="non_discrimination")
    if subset.empty:
        subset = search_cases(df, annex_domain="employment")
    _show(subset)


def scenario_3():
    print("\n" + "=" * 70)
    print("SCENARIO 3: All LLM-related incidents (any domain)")
    print("=" * 70)
    df = load_table()
    subset = search_cases(df, pattern_contains="llm")
    _show(subset)


def scenario_4():
    print("\n" + "=" * 70)
    print("SCENARIO 4: Unfair exclusion / bias harms (any domain)")
    print("=" * 70)
    df = load_table()
    subset = search_cases(df, harm_contains="unfair_exclusion")
    _show(subset)


def scenario_5():
    print("\n" + "=" * 70)
    print("SCENARIO 5: Misinformation risks in essential services")
    print("=" * 70)
    df = load_table()
    subset = search_cases(df, annex_domain="essential_services",
                          harm_contains="misinformation_error")
    _show(subset)


if __name__ == "__main__":
    scenario_1()
    scenario_2()
    scenario_3()
    scenario_4()
    scenario_5()
