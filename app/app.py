"""FRIA Evidence Retrieval Prototype.

Minimal Flask application that loads the FRIA knowledge graph and
provides a web interface for querying AI incident records by domain,
rights, and system pattern.

Usage:
    pip install -r requirements.txt
    python app.py

Then open http://localhost:5000 in your browser.
"""

import os, sys

try:
    from flask import Flask, render_template, request
except ImportError:
    print("[WARN] Flask not installed. Run: pip install flask")
    sys.exit(1)

try:
    import rdflib
except ImportError:
    print("[WARN] rdflib not installed. Run: pip install rdflib")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TTL_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "knowledge_graph.ttl")
FRIA = rdflib.Namespace("https://example.org/fria-kg/")

DOMAIN_OPTIONS = [
    ("domain_employment", "Employment (Annex III/4)"),
    ("domain_essential_services", "Essential Services (Annex III/5a)"),
]

RIGHTS_OPTIONS = [
    ("right_non_discrimination", "Non-discrimination"),
    ("right_privacy_data_protection", "Privacy & Data Protection"),
    ("right_access_social_protection", "Access to Social Protection"),
    ("right_good_administration", "Good Administration"),
    ("right_other", "Other"),
]

PATTERN_OPTIONS = [
    ("", "Any pattern"),
    ("pattern_profiling_scoring", "Profiling / Scoring"),
    ("pattern_surveillance_monitor", "Surveillance / Monitoring"),
    ("pattern_classification_triage", "Classification / Triage"),
    ("pattern_resource_allocation", "Resource Allocation"),
    ("pattern_llm_decision_support", "LLM Decision Support"),
    ("pattern_llm_assisted_screening", "LLM-Assisted Screening"),
    ("pattern_chatbot", "Chatbot"),
    ("pattern_summary_assistant", "Summary Assistant"),
    ("pattern_not_llm", "Non-LLM System"),
]

SOURCE_LABELS = {
    "srctype_court_case": "Court Case",
    "srctype_government_inventory": "Gov. Inventory",
    "srctype_news_article": "News Article",
    "srctype_regulator_opinion": "Regulator Opinion",
}

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
graph = None


def load_graph():
    """Load the knowledge graph on first request."""
    global graph
    if graph is not None:
        return graph

    ttl = os.path.abspath(TTL_PATH)
    if not os.path.exists(ttl):
        print(f"[WARN] Knowledge graph not found at {ttl}")
        sys.exit(1)

    print(f"Loading knowledge graph from {ttl}...")
    graph = rdflib.Graph()
    graph.parse(ttl, format="turtle")
    print(f"  Loaded {len(graph)} triples")
    return graph


def shorten_uri(uri):
    """Extract local name from URI."""
    s = str(uri)
    if "fria-kg/" in s:
        return s.split("fria-kg/")[-1]
    return s


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Homepage with query form."""
    g = load_graph()
    return render_template(
        "index.html",
        domain_options=DOMAIN_OPTIONS,
        rights_options=RIGHTS_OPTIONS,
        pattern_options=PATTERN_OPTIONS,
        results=None,
        query_sparql=None,
    )


@app.route("/query", methods=["POST"])
def query():
    """Handle structured query form submission."""
    g = load_graph()

    domains = request.form.getlist("domains")
    rights = request.form.getlist("rights")
    pattern = request.form.get("pattern", "")

    # Build SPARQL query dynamically
    where_clauses = [
        "?incident a fria:Incident .",
        "?incident rdfs:label ?label .",
        "?incident fria:hasDomain ?domainNode .",
        "?incident fria:hasPattern ?patternNode .",
    ]

    # Domain filter
    if domains:
        domain_values = " ".join(f"fria:{d}" for d in domains)
        where_clauses.append(f"VALUES ?domainNode {{ {domain_values} }}")

    # Rights filter
    for r in rights:
        where_clauses.append(f"?incident fria:hasRight fria:{r} .")

    # Pattern filter
    if pattern:
        where_clauses.append(f"?incident fria:hasPattern fria:{pattern} .")

    # Source type (optional)
    where_clauses.append(
        "OPTIONAL { ?incident fria:hasSourceType ?sourceNode . }"
    )

    # Harms
    where_clauses.append(
        "OPTIONAL { ?incident fria:hasHarm ?harmNode . }"
    )

    sparql = f"""PREFIX fria: <https://example.org/fria-kg/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?incident ?label ?domainNode ?patternNode
       (GROUP_CONCAT(DISTINCT ?harmNode; SEPARATOR=", ") AS ?harms)
       (GROUP_CONCAT(DISTINCT ?rightNode; SEPARATOR=", ") AS ?rights_list)
       (SAMPLE(?sourceNode) AS ?source)
WHERE {{
    {chr(10).join("    " + c for c in where_clauses)}
    OPTIONAL {{ ?incident fria:hasRight ?rightNode . }}
}}
GROUP BY ?incident ?label ?domainNode ?patternNode
ORDER BY ?label
LIMIT 200"""

    try:
        results_raw = g.query(sparql)
        results = []
        for row in results_raw:
            source_short = shorten_uri(row.source) if row.source else "N/A"
            results.append({
                "label": str(row.label),
                "source": SOURCE_LABELS.get(source_short, source_short),
                "domain": shorten_uri(row.domainNode).replace("domain_", ""),
                "pattern": shorten_uri(row.patternNode).replace("pattern_", ""),
                "rights": ", ".join(
                    shorten_uri(r).replace("right_", "")
                    for r in str(row.rights_list).split(", ")
                    if r and "fria-kg" in r
                ) if row.rights_list else "N/A",
                "harms": ", ".join(
                    shorten_uri(h).replace("harm_", "")
                    for h in str(row.harms).split(", ")
                    if h and "fria-kg" in h
                ) if row.harms else "N/A",
            })

        return render_template(
            "index.html",
            domain_options=DOMAIN_OPTIONS,
            rights_options=RIGHTS_OPTIONS,
            pattern_options=PATTERN_OPTIONS,
            results=results,
            result_count=len(results),
            query_sparql=sparql,
            selected_domains=domains,
            selected_rights=rights,
            selected_pattern=pattern,
        )

    except Exception as e:
        return render_template(
            "index.html",
            domain_options=DOMAIN_OPTIONS,
            rights_options=RIGHTS_OPTIONS,
            pattern_options=PATTERN_OPTIONS,
            results=None,
            error=str(e),
            query_sparql=sparql,
        )


@app.route("/sparql", methods=["POST"])
def sparql_query():
    """Handle raw SPARQL query."""
    g = load_graph()
    raw_sparql = request.form.get("sparql", "").strip()

    if not raw_sparql:
        return render_template(
            "index.html",
            domain_options=DOMAIN_OPTIONS,
            rights_options=RIGHTS_OPTIONS,
            pattern_options=PATTERN_OPTIONS,
            results=None,
            error="Please enter a SPARQL query.",
            query_sparql=raw_sparql,
        )

    try:
        results_raw = g.query(raw_sparql)
        results = []
        for row in results_raw:
            row_dict = {}
            for var in results_raw.vars:
                val = row[var]
                row_dict[str(var)] = shorten_uri(val) if val else "N/A"
            results.append(row_dict)

        return render_template(
            "sparql_results.html",
            results=results,
            result_count=len(results),
            columns=results_raw.vars,
            query_sparql=raw_sparql,
        )

    except Exception as e:
        return render_template(
            "index.html",
            domain_options=DOMAIN_OPTIONS,
            rights_options=RIGHTS_OPTIONS,
            pattern_options=PATTERN_OPTIONS,
            results=None,
            error=f"SPARQL error: {str(e)}",
            query_sparql=raw_sparql,
        )


if __name__ == "__main__":
    load_graph()
    app.run(debug=True, port=5000)
