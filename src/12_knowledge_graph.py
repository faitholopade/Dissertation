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
