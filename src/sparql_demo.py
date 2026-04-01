"""SPARQL query demonstrations against the FRIA knowledge graph.

Loads the existing knowledge graph (output/knowledge_graph.ttl) and runs
four queries that demonstrate the queryability claims made in the
dissertation. Results are printed and saved to output/sparql_demo_results.txt.

Inputs:
    output/knowledge_graph.ttl

Outputs:
    output/sparql_demo_results.txt
    chapters/sparql_demo_section.tex
"""

import os, sys
from collections import defaultdict

try:
    import rdflib
except ImportError:
    print("⚠  rdflib not installed. Run: pip install rdflib")
    sys.exit(1)

from tabulate import tabulate

TTL_PATH = "output/knowledge_graph.ttl"
OUTPUT_PATH = "output/sparql_demo_results.txt"
TEX_PATH = "chapters/sparql_demo_section.tex"

FRIA = rdflib.Namespace("https://example.org/fria-kg/")

QUERIES = [
    {
        "id": "Q1",
        "title": "Essential-services incidents involving non-discrimination rights",
        "description": (
            "Retrieve all incidents classified under the essential services "
            "domain that implicate non-discrimination rights. This demonstrates "
            "combined domain and rights filtering — a core requirement for "
            "Article 27 FRIA evidence retrieval."
        ),
        "sparql": """
PREFIX fria: <https://example.org/fria-kg/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?incident ?label
WHERE {
    ?incident a fria:Incident ;
              rdfs:label ?label ;
              fria:hasDomain fria:domain_essential_services ;
              fria:hasRight fria:right_non_discrimination .
}
ORDER BY ?label
""",
        "columns": ["Incident", "Label"],
    },
    {
        "id": "Q2",
        "title": "Incidents where hybrid method identified profiling/scoring",
        "description": (
            "Find all incidents whose system pattern is classified as "
            "profiling or scoring. This demonstrates pattern-based retrieval, "
            "enabling a deployer to locate precedents where algorithmic "
            "profiling has been documented."
        ),
        "sparql": """
PREFIX fria: <https://example.org/fria-kg/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?incident ?label ?domain
WHERE {
    ?incident a fria:Incident ;
              rdfs:label ?label ;
              fria:hasDomain ?domainNode ;
              fria:hasPattern fria:pattern_profiling_scoring .
    BIND(STRAFTER(STR(?domainNode), "fria-kg/") AS ?domain)
}
ORDER BY ?domain ?label
""",
        "columns": ["Incident", "Label", "Domain"],
    },
    {
        "id": "Q3",
        "title": "Rights implicated by employment-domain incidents, ranked by frequency",
        "description": (
            "List all fundamental rights implicated by employment-domain "
            "incidents, ranked by how frequently they appear. This "
            "demonstrates cross-axis aggregation — combining domain and "
            "rights axes to answer analytical questions about risk patterns."
        ),
        "sparql": """
PREFIX fria: <https://example.org/fria-kg/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?rightLabel (COUNT(?incident) AS ?count)
WHERE {
    ?incident a fria:Incident ;
              fria:hasDomain fria:domain_employment ;
              fria:hasRight ?right .
    BIND(STRAFTER(STR(?right), "fria-kg/") AS ?rightLabel)
}
GROUP BY ?rightLabel
ORDER BY DESC(?count)
""",
        "columns": ["Right", "Count"],
    },
    {
        "id": "Q4",
        "title": "Incidents involving both privacy/data-protection and unfair-exclusion harms",
        "description": (
            "Retrieve incidents that exhibit both privacy or data-protection "
            "harms and unfair-exclusion harms simultaneously. This demonstrates "
            "multi-label intersection querying — identifying cases where "
            "multiple harm types co-occur."
        ),
        "sparql": """
PREFIX fria: <https://example.org/fria-kg/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?incident ?label ?domain
WHERE {
    ?incident a fria:Incident ;
              rdfs:label ?label ;
              fria:hasDomain ?domainNode ;
              fria:hasHarm fria:harm_privacy_breach ;
              fria:hasHarm fria:harm_unfair_exclusion .
    BIND(STRAFTER(STR(?domainNode), "fria-kg/") AS ?domain)
}
ORDER BY ?label
""",
        "columns": ["Incident", "Label", "Domain"],
    },
]


def shorten_uri(uri):
    """Shorten full URIs to readable local names."""
    s = str(uri)
    if "fria-kg/" in s:
        return s.split("fria-kg/")[-1]
    return s


def run_query(graph, query_spec):
    """Run a single SPARQL query and return formatted rows."""
    results = graph.query(query_spec["sparql"])
    rows = []
    for row in results:
        rows.append([shorten_uri(cell) for cell in row])
    return rows


def format_query_block(query_spec, rows):
    """Format a query + results block for text output."""
    lines = []
    lines.append(f"{'='*70}")
    lines.append(f"{query_spec['id']}: {query_spec['title']}")
    lines.append(f"{'='*70}")
    lines.append("")
    lines.append(query_spec["description"])
    lines.append("")
    lines.append("SPARQL query:")
    lines.append(query_spec["sparql"].strip())
    lines.append("")
    lines.append(f"Results: {len(rows)} matches")
    lines.append("")

    if rows:
        display_rows = rows[:10]
        lines.append(tabulate(display_rows, headers=query_spec["columns"],
                              tablefmt="simple"))
        if len(rows) > 10:
            lines.append(f"  ... and {len(rows) - 10} more")
    else:
        lines.append("  (no results)")

    lines.append("")
    return "\n".join(lines)


def generate_latex(query_results):
    """Generate a LaTeX snippet for the SPARQL demonstration subsection."""
    lines = []
    lines.append(r"\subsection{SPARQL Query Demonstration}")
    lines.append(r"\label{subsec:sparql-demo}")
    lines.append("")
    lines.append(
        r"To validate the queryability of the knowledge graph, four SPARQL queries "
        r"were executed against the RDF representation. Each query targets a distinct "
        r"retrieval pattern relevant to FRIA evidence gathering under Article~27 of "
        r"the AI Act. Table~\ref{tab:sparql-summary} summarises the results."
    )
    lines.append("")

    # Summary table
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{SPARQL query demonstration results}")
    lines.append(r"\label{tab:sparql-summary}")
    lines.append(r"\begin{tabular}{clr}")
    lines.append(r"\toprule")
    lines.append(r"Query & Retrieval pattern & Results \\")
    lines.append(r"\midrule")
    for qid, spec, rows in query_results:
        title_short = spec["title"][:55]
        lines.append(f"{qid} & {title_short} & {len(rows)} \\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    lines.append("")

    # Individual query listings and interpretation
    interpretations = {
        "Q1": (
            r"Query~1 demonstrates combined filtering across domain and rights axes. "
            r"The {} results confirm that the graph structure supports the "
            r"retrieval pattern most directly required by Article~27(1)(a): identifying "
            r"precedent incidents within a specific high-risk domain that implicate a "
            r"particular fundamental right."
        ),
        "Q2": (
            r"Query~2 retrieves incidents by system pattern, returning {} records "
            r"classified as profiling or scoring systems. This pattern-based retrieval "
            r"enables deployers to locate precedents involving similar AI architectures, "
            r"supporting the risk-by-analogy reasoning that underpins impact assessment."
        ),
        "Q3": (
            r"Query~3 aggregates rights across employment-domain incidents, demonstrating "
            r"cross-axis analytical capability. The ranked output reveals which fundamental "
            r"rights are most frequently implicated in employment AI systems, providing "
            r"quantitative evidence for FRIA prioritisation decisions."
        ),
        "Q4": (
            r"Query~4 identifies incidents exhibiting both privacy breach and unfair "
            r"exclusion harms simultaneously, returning {} records. This multi-label "
            r"intersection query demonstrates that the graph's multi-valued harm "
            r"annotations support compound risk identification --- a capability not "
            r"available in flat tabular representations."
        ),
    }

    for qid, spec, rows in query_results:
        lines.append(r"\paragraph{" + spec["title"] + "}")
        lines.append("")
        lines.append(r"\begin{lstlisting}[language=SPARQL,basicstyle=\ttfamily\footnotesize,breaklines=true,caption={" + spec["title"] + r"}]")
        lines.append(spec["sparql"].strip())
        lines.append(r"\end{lstlisting}")
        lines.append("")
        interp = interpretations[qid].format(len(rows))
        lines.append(interp)
        lines.append("")

    return "\n".join(lines)


def main():
    if not os.path.exists(TTL_PATH):
        print(f"⚠  Knowledge graph not found at {TTL_PATH}")
        sys.exit(1)

    print("Loading knowledge graph...")
    g = rdflib.Graph()
    g.parse(TTL_PATH, format="turtle")
    print(f"  Loaded {len(g)} triples")

    output_blocks = []
    query_results = []

    for spec in QUERIES:
        print(f"\nRunning {spec['id']}: {spec['title']}...")
        rows = run_query(g, spec)
        print(f"  {len(rows)} results")
        output_blocks.append(format_query_block(spec, rows))
        query_results.append((spec["id"], spec, rows))

    # Save text results
    full_output = (
        "SPARQL QUERY DEMONSTRATION RESULTS\n"
        f"Knowledge graph: {TTL_PATH} ({len(g)} triples)\n"
        f"{'='*70}\n\n"
        + "\n".join(output_blocks)
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(full_output)
    print(f"\n[OK] Saved {OUTPUT_PATH}")

    # Save LaTeX snippet
    os.makedirs(os.path.dirname(TEX_PATH), exist_ok=True)
    latex = generate_latex(query_results)
    with open(TEX_PATH, "w", encoding="utf-8") as f:
        f.write(latex)
    print(f"[OK] Saved {TEX_PATH}")


if __name__ == "__main__":
    main()
