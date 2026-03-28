"""Step 12: Construct the RDF knowledge graph.

Builds an RDF/Turtle knowledge graph from the causal-annotated master
table, linking incidents to domains, patterns, rights, harms, and
causal factors using the FRIA risk schema vocabulary.

Inputs:
    output/master_annotation_table_causal.csv

Outputs:
    output/knowledge_graph.ttl        (1,351 triples)
    output/knowledge_graph_summary.csv
"""

import os, json, re
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
if SCRIPT_DIR.name == "src":
    PROJECT_ROOT = SCRIPT_DIR.parent
else:
    PROJECT_ROOT = SCRIPT_DIR
os.chdir(PROJECT_ROOT)
print(f"Working directory: {PROJECT_ROOT}")

try:
    from rdflib import Graph as RDFGraph, Namespace, Literal, URIRef, RDF, RDFS
    from rdflib.namespace import DCTERMS
    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False
    print("  rdflib not installed -- skipping .ttl export (NetworkX graph still built)")

INPUT_CSV  = PROJECT_ROOT / "output" / "master_annotation_table_causal.csv"
FALLBACK   = PROJECT_ROOT / "output" / "master_annotation_table_final.csv"
TTL_OUT    = PROJECT_ROOT / "output" / "knowledge_graph.ttl"
SUMMARY_OUT= PROJECT_ROOT / "output" / "knowledge_graph_summary.csv"
FIG_OUT    = PROJECT_ROOT / "figures" / "fig_knowledge_graph.png"

VAIR    = "https://w3id.org/vair/"
DPV     = "https://w3id.org/dpv/"
DPVR    = "https://w3id.org/dpv/risk/"
EUR     = "https://w3id.org/dpv/legal/eu/rights/"
FRIA    = "https://example.org/fria-kg/"


def slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", str(text).strip())
    return s[:max_len].strip("_") or "unknown"


def split_multi(val) -> list:
    if pd.isna(val) or str(val).strip() in ("", "nan"):
        return []
    return [v.strip() for v in re.split(r"[|,;]+", str(val)) if v.strip()]


DOMAIN_URI = {
    "employment":        VAIR + "Employment",
    "essentialservices": VAIR + "EssentialPublicServices",
    "unknown":           VAIR + "UnspecifiedDomain",
}

RIGHT_URI = {
    "privacy_data_protection": EUR + "A8-ProtectionOfPersonalData",
    "privacydataprotection":   EUR + "A8-ProtectionOfPersonalData",
    "non_discrimination":      EUR + "A21-NonDiscrimination",
    "nondiscrimination":       EUR + "A21-NonDiscrimination",
    "access_social_protection":EUR + "A34-SocialSecurity",
    "accesssocialprotection":  EUR + "A34-SocialSecurity",
    "good_administration":     EUR + "A41-RightToGoodAdministration",
    "goodadministration":      EUR + "A41-RightToGoodAdministration",
    "other":                   EUR + "FundamentalRights",
}

HARM_URI = {
    "unfairexclusion":       DPVR + "Discrimination",
    "privacybreach":         DPVR + "DataBreach",
    "misinformationerror":   DPVR + "Misinformation",
    "proceduralunfairness":  DPVR + "RightToRemedyImpairment",
    "other":                 DPVR + "Harm",
}

ROOT_CAUSE_URI = {
    "technology_failure": FRIA + "TechnologyFailure",
    "context_of_use":     FRIA + "ContextOfUseMismatch",
    "missing_mitigation": FRIA + "MissingMitigation",
    "human_error":        FRIA + "HumanError",
    "data_quality":       FRIA + "DataQualityIssue",
    "policy_gap":         FRIA + "PolicyGap",
    "unknown":            FRIA + "UnknownCause",
}

PATTERN_URI = {
    "llmdecisionsupport":   VAIR + "DecisionSupport",
    "llmassistedscreening": VAIR + "AutomatedScreening",
    "chatbot":              VAIR + "Chatbot",
    "summaryassistant":     VAIR + "TextGeneration",
    "notllm":               VAIR + "NonLLMSystem",
    "profilingscoring":     VAIR + "ProfilingScoring",
    "resourceallocation":   VAIR + "ResourceAllocation",
    "classificationtriage": VAIR + "ClassificationTriage",
    "surveillancemonitor":  VAIR + "SurveillanceMonitoring",
    "misinformationerror":  VAIR + "MisinformationRisk",
    "unknown":              VAIR + "UnspecifiedPattern",
}


def build_graph(df: pd.DataFrame):
    G = nx.DiGraph()
    node_types = Counter()
    edge_types = Counter()

    for _, row in df.iterrows():
        source   = str(row.get("source", ""))
        sid      = str(row.get("source_id", row.get("sourceid", "")))
        title    = str(row.get("title", ""))[:80]
        inc_id   = f"inc:{sid}" if sid and sid != "nan" else f"inc:{slugify(title, 30)}"

        G.add_node(inc_id, label=title[:40], node_type="Incident",
                   full_title=title, source=source)
        node_types["Incident"] += 1

        domain = str(row.get("hybrid_v2_annex_domain",
                     row.get("hybridv2annexdomain",
                     row.get("annex_domain",
                     row.get("annexdomain", "unknown"))))).lower().strip()
        if domain and domain != "nan":
            dom_node = f"domain:{domain}"
            G.add_node(dom_node, label=domain, node_type="AnnexDomain")
            G.add_edge(inc_id, dom_node, relation="hasDomain")
            node_types["AnnexDomain"] += 1
            edge_types["hasDomain"] += 1

        pattern = str(row.get("hybrid_v2_system_pattern",
                      row.get("hybridv2systempattern",
                      row.get("system_pattern",
                      row.get("systempattern", "unknown"))))).lower().strip()
        if pattern and pattern not in ("nan", "unknown"):
            pat_node = f"pattern:{pattern}"
            G.add_node(pat_node, label=pattern, node_type="SystemPattern")
            G.add_edge(inc_id, pat_node, relation="hasPattern")
            node_types["SystemPattern"] += 1
            edge_types["hasPattern"] += 1

        rights_col = str(row.get("rights", row.get("llm_rights", row.get("llmrights", ""))))
        for r in split_multi(rights_col):
            r_key = r.lower().strip()
            if r_key and r_key != "nan":
                r_node = f"right:{r_key}"
                G.add_node(r_node, label=r_key, node_type="FundamentalRight")
                G.add_edge(inc_id, r_node, relation="hasRight")
                node_types["FundamentalRight"] += 1
                edge_types["hasRight"] += 1

        harms_col = str(row.get("harms", row.get("llm_harms", row.get("llmharms", ""))))
        for h in split_multi(harms_col):
            h_key = h.lower().strip()
            if h_key and h_key != "nan":
                h_node = f"harm:{h_key}"
                G.add_node(h_node, label=h_key, node_type="HarmType")
                G.add_edge(inc_id, h_node, relation="hasHarm")
                node_types["HarmType"] += 1
                edge_types["hasHarm"] += 1

        rc = str(row.get("root_cause", "")).lower().strip()
        if rc and rc not in ("nan", "", "unknown"):
            rc_node = f"cause:{rc}"
            G.add_node(rc_node, label=rc.replace("_", " "), node_type="RootCause")
            G.add_edge(inc_id, rc_node, relation="hasRootCause")
            node_types["RootCause"] += 1
            edge_types["hasRootCause"] += 1

        mit = str(row.get("mitigation_reported", "")).strip()
        if mit and mit.lower() not in ("nan", "", "none_reported"):
            mit_node = f"mit:{slugify(mit, 40)}"
            G.add_node(mit_node, label=mit[:50], node_type="Mitigation")
            G.add_edge(inc_id, mit_node, relation="hasMitigation")
            node_types["Mitigation"] += 1
            edge_types["hasMitigation"] += 1

        st = str(row.get("source_type", "")).lower().strip()
        if st and st not in ("nan", ""):
            src_node = f"srctype:{st}"
            G.add_node(src_node, label=st.replace("_", " "), node_type="SourceType")
            G.add_edge(inc_id, src_node, relation="hasSourceType")
            node_types["SourceType"] += 1
            edge_types["hasSourceType"] += 1

        for col, rel in [("Deployers", "involvedDeployer"),
                         ("Developers", "involvedDeveloper"),
                         ("deployers", "involvedDeployer"),
                         ("developers", "involvedDeveloper")]:
            actors = str(row.get(col, "")).strip()
            if actors and actors.lower() not in ("nan", ""):
                for a in re.split(r"[;,|]+", actors):
                    a = a.strip()
                    if a:
                        a_node = f"actor:{slugify(a, 30)}"
                        G.add_node(a_node, label=a[:30], node_type="Actor")
                        G.add_edge(inc_id, a_node, relation=rel)
                        node_types["Actor"] += 1
                        edge_types[rel] += 1

    return G, node_types, edge_types


def export_ttl(G: nx.DiGraph, outpath: Path):
    if not HAS_RDFLIB:
        print("  Skipping .ttl export (rdflib not installed)")
        return

    vair  = Namespace(VAIR)
    dpv   = Namespace(DPV)
    dpvr  = Namespace(DPVR)
    eur   = Namespace(EUR)
    fria  = Namespace(FRIA)

    g = RDFGraph()
    g.bind("vair",  vair)
    g.bind("dpv",   dpv)
    g.bind("dpv-risk", dpvr)
    g.bind("eu-rights", eur)
    g.bind("fria",  fria)
    g.bind("dct",   DCTERMS)

    REL_MAP = {
        "hasDomain":        fria["hasDomain"],
        "hasPattern":       fria["hasPattern"],
        "hasRight":         fria["hasRight"],
        "hasHarm":          fria["hasHarm"],
        "hasRootCause":     fria["hasRootCause"],
        "hasMitigation":    fria["hasMitigation"],
        "hasSourceType":    fria["hasSourceType"],
        "involvedDeployer": fria["involvedDeployer"],
        "involvedDeveloper":fria["involvedDeveloper"],
    }

    for u, v, data in G.edges(data=True):
        subj = URIRef(FRIA + slugify(u))
        obj  = URIRef(FRIA + slugify(v))
        pred = REL_MAP.get(data.get("relation", ""), fria["relatedTo"])
        g.add((subj, pred, obj))

    for node, data in G.nodes(data=True):
        uri = URIRef(FRIA + slugify(node))
        g.add((uri, RDFS.label, Literal(data.get("label", node))))
        ntype = data.get("node_type", "")
        if ntype:
            g.add((uri, RDF.type, fria[ntype]))

    g.serialize(destination=str(outpath), format="turtle")
    print(f"  {outpath.name}  ({len(g)} triples)")


NODE_COLOURS = {
    "Incident":         "#4A90D9",
    "AnnexDomain":      "#E57373",
    "SystemPattern":    "#FFB74D",
    "FundamentalRight": "#81C784",
    "HarmType":         "#CE93D8",
    "RootCause":        "#FFD54F",
    "Mitigation":       "#4DB6AC",
    "SourceType":       "#A1887F",
    "Actor":            "#90A4AE",
}

def visualise(G: nx.DiGraph, outpath: Path):
    concept_nodes = [n for n, d in G.nodes(data=True)
                     if d.get("node_type") != "Incident"]

    C = nx.Graph()
    for cn in concept_nodes:
        d = G.nodes[cn]
        C.add_node(cn, **d)

    concept_incidents = defaultdict(set)
    for u, v, d in G.edges(data=True):
        utype = G.nodes[u].get("node_type", "")
        vtype = G.nodes[v].get("node_type", "")
        if utype == "Incident" and vtype != "Incident":
            concept_incidents[v].add(u)
        elif vtype == "Incident" and utype != "Incident":
            concept_incidents[u].add(v)

    concept_list = list(concept_incidents.keys())
    for i, a in enumerate(concept_list):
        for b in concept_list[i+1:]:
            shared = len(concept_incidents[a] & concept_incidents[b])
            if shared >= 3:
                C.add_edge(a, b, weight=shared)

    if len(C.nodes) == 0:
        print("  No concept-level co-occurrence edges -- skipping figure")
        return

    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    pos = nx.spring_layout(C, k=2.5, iterations=80, seed=42)

    sizes = [min(max(len(concept_incidents.get(n, set())), 1) * 80, 3000)
             for n in C.nodes]
    colors = [NODE_COLOURS.get(C.nodes[n].get("node_type", ""), "#BDBDBD")
              for n in C.nodes]

    widths = [C.edges[e].get("weight", 1) * 0.3 for e in C.edges]

    nx.draw_networkx_edges(C, pos, ax=ax, width=widths,
                           alpha=0.25, edge_color="#999999")
    nx.draw_networkx_nodes(C, pos, ax=ax, node_size=sizes,
                           node_color=colors, alpha=0.85, edgecolors="white",
                           linewidths=0.5)

    labels = {n: C.nodes[n].get("label", n)[:20] for n in C.nodes}
    nx.draw_networkx_labels(C, pos, labels=labels, font_size=7, ax=ax)

    from matplotlib.patches import Patch
    legend_items = [Patch(facecolor=c, label=t)
                    for t, c in NODE_COLOURS.items()
                    if any(C.nodes[n].get("node_type") == t for n in C.nodes)]
    ax.legend(handles=legend_items, loc="upper left", fontsize=8, framealpha=0.9)

    ax.set_title("FRIA Knowledge Graph — Concept Co-occurrence\n"
                 "(edges = shared incidents >= 3; node size = incident count)",
                 fontsize=12, fontweight="bold")
    ax.axis("off")
    fig.tight_layout()
    os.makedirs(outpath.parent, exist_ok=True)
    fig.savefig(str(outpath), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {outpath.name}")


def main():
    csv_path = INPUT_CSV if INPUT_CSV.exists() else FALLBACK

    if not csv_path.exists():
        print(f"ERROR: Cannot find input CSV")
        print(f"  Tried:    {INPUT_CSV}")
        print(f"  Fallback: {FALLBACK}")
        print(f"\n  Contents of output/:")
        out_dir = PROJECT_ROOT / "output"
        if out_dir.exists():
            for f in sorted(out_dir.glob("master_annotation*")):
                print(f"    {f.name}")
        import sys
        sys.exit(1)

    df = pd.read_csv(csv_path)
    print(f"STEP 12  Knowledge Graph Construction")
    print(f"  Loaded {len(df)} rows from {csv_path.name}")
    has_causal = "root_cause" in df.columns
    if not has_causal:
        print("  (No root_cause column -- run 11_chain_of_events.py first for full graph)")

    G, node_types, edge_types = build_graph(df)
    print(f"\n  Graph:  {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"\n  -- Node types --")
    for t, c in node_types.most_common():
        print(f"    {t:<20} {c}")
    print(f"\n  -- Edge types --")
    for t, c in edge_types.most_common():
        print(f"    {t:<20} {c}")

    export_ttl(G, TTL_OUT)

    rows = []
    for t, c in node_types.most_common():
        rows.append({"category": "node_type", "label": t, "count": c})
    for t, c in edge_types.most_common():
        rows.append({"category": "edge_type", "label": t, "count": c})
    pd.DataFrame(rows).to_csv(SUMMARY_OUT, index=False)
    print(f"  {SUMMARY_OUT.name}")

    os.makedirs(PROJECT_ROOT / "figures", exist_ok=True)
    visualise(G, FIG_OUT)

    print("\nKnowledge graph complete.")


if __name__ == "__main__":
    main()
