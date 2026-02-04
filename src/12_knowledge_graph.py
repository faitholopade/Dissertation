"""
12_knowledge_graph.py  —  Knowledge-graph construction (Step 12)

Builds a multi-layer knowledge graph from the causal-annotated master table:

    Incident --hasDomain-->      AnnexDomain
    Incident --hasRootCause-->   RootCause
    Incident --hasRight-->       FundamentalRight
    Incident --hasHarm-->        HarmType
    Incident --hasPattern-->     SystemPattern
    Incident --hasSource-->      SourceDocument
    Incident --hasMitigation-->  Mitigation
    Incident --involvedActor-->  Actor

Outputs:
  - output/knowledge_graph.ttl          RDF/Turtle
  - output/knowledge_graph_summary.csv  Node + edge counts
  - figures/fig_knowledge_graph.png     NetworkX visualisation

Usage:
    python src/12_knowledge_graph.py      (from project root)
    python 12_knowledge_graph.py          (from src/)
"""

import os, json, re
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Auto-resolve project root ────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
if SCRIPT_DIR.name == "src":
    PROJECT_ROOT = SCRIPT_DIR.parent
else:
    PROJECT_ROOT = SCRIPT_DIR
os.chdir(PROJECT_ROOT)
print(f"Working directory: {PROJECT_ROOT}")

# ── Try rdflib; fall back to pure-networkx if not installed ──────────────────
try:
    from rdflib import Graph as RDFGraph, Namespace, Literal, URIRef, RDF, RDFS
    from rdflib.namespace import DCTERMS
    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False
    print("  rdflib not installed -- skipping .ttl export (NetworkX graph still built)")

# ── Config ───────────────────────────────────────────────────────────────────
INPUT_CSV  = PROJECT_ROOT / "output" / "master_annotation_table_causal.csv"
FALLBACK   = PROJECT_ROOT / "output" / "master_annotation_table_final.csv"
TTL_OUT    = PROJECT_ROOT / "output" / "knowledge_graph.ttl"
SUMMARY_OUT= PROJECT_ROOT / "output" / "knowledge_graph_summary.csv"
FIG_OUT    = PROJECT_ROOT / "figures" / "fig_knowledge_graph.png"

# Namespaces
VAIR    = "https://w3id.org/vair/"
DPV     = "https://w3id.org/dpv/"
DPVR    = "https://w3id.org/dpv/risk/"
EUR     = "https://w3id.org/dpv/legal/eu/rights/"
FRIA    = "https://example.org/fria-kg/"


# ── Helpers ──────────────────────────────────────────────────────────────────
def slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", str(text).strip())
    return s[:max_len].strip("_") or "unknown"


def split_multi(val) -> list:
    if pd.isna(val) or str(val).strip() in ("", "nan"):
        return []
    return [v.strip() for v in re.split(r"[|,;]+", str(val)) if v.strip()]


# ── URI maps ─────────────────────────────────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════════════════════
#  BUILD NETWORKX GRAPH
# ══════════════════════════════════════════════════════════════════════════════
def build_graph(df: pd.DataFrame):
    G = nx.DiGraph()
    node_types = Counter()
    edge_types = Counter()

    for _, row in df.iterrows():
        source   = str(row.get("source", ""))
        sid      = str(row.get("source_id", row.get("sourceid", "")))
        title    = str(row.get("title", ""))[:80]
        inc_id   = f"inc:{sid}" if sid and sid != "nan" else f"inc:{slugify(title, 30)}"

        # ── Incident node
        G.add_node(inc_id, label=title[:40], node_type="Incident",
                   full_title=title, source=source)
        node_types["Incident"] += 1

        # ── Domain
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

        # ── System pattern
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

        # ── Rights
        rights_col = str(row.get("rights", row.get("llm_rights", row.get("llmrights", ""))))
        for r in split_multi(rights_col):
            r_key = r.lower().strip()
            if r_key and r_key != "nan":
                r_node = f"right:{r_key}"
                G.add_node(r_node, label=r_key, node_type="FundamentalRight")
                G.add_edge(inc_id, r_node, relation="hasRight")
                node_types["FundamentalRight"] += 1
                edge_types["hasRight"] += 1

        # ── Harms
        harms_col = str(row.get("harms", row.get("llm_harms", row.get("llmharms", ""))))
        for h in split_multi(harms_col):
            h_key = h.lower().strip()
            if h_key and h_key != "nan":
                h_node = f"harm:{h_key}"
                G.add_node(h_node, label=h_key, node_type="HarmType")
                G.add_edge(inc_id, h_node, relation="hasHarm")
                node_types["HarmType"] += 1
                edge_types["hasHarm"] += 1

        # ── Root cause (from Step 11)
        rc = str(row.get("root_cause", "")).lower().strip()
        if rc and rc not in ("nan", "", "unknown"):
            rc_node = f"cause:{rc}"
            G.add_node(rc_node, label=rc.replace("_", " "), node_type="RootCause")
            G.add_edge(inc_id, rc_node, relation="hasRootCause")
            node_types["RootCause"] += 1
            edge_types["hasRootCause"] += 1

        # ── Mitigation (from Step 11)
        mit = str(row.get("mitigation_reported", "")).strip()
        if mit and mit.lower() not in ("nan", "", "none_reported"):
            mit_node = f"mit:{slugify(mit, 40)}"
            G.add_node(mit_node, label=mit[:50], node_type="Mitigation")
            G.add_edge(inc_id, mit_node, relation="hasMitigation")
            node_types["Mitigation"] += 1
            edge_types["hasMitigation"] += 1

        # ── Source type
        st = str(row.get("source_type", "")).lower().strip()
        if st and st not in ("nan", ""):
            src_node = f"srctype:{st}"
            G.add_node(src_node, label=st.replace("_", " "), node_type="SourceType")
            G.add_edge(inc_id, src_node, relation="hasSourceType")
            node_types["SourceType"] += 1
            edge_types["hasSourceType"] += 1

        # ── Deployer / Developer (if available)
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


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT RDF/TURTLE
# ══════════════════════════════════════════════════════════════════════════════
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
