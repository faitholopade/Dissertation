"""Step 13: Visualise the knowledge graph.

Generates an interactive HTML visualisation (via pyvis) and a static PNG
of the knowledge graph. Nodes are colour-coded by type and sized by
connection degree.

Inputs:
    output/knowledge_graph.ttl

Outputs:
    figures/fig_knowledge_graph_full.html  (interactive)
    figures/fig_knowledge_graph_full.png   (static)
    figures/fig_knowledge_graph.png        (summary view)
"""

import os, re, json
from pathlib import Path
from collections import defaultdict, Counter
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if SCRIPT_DIR.name == "src":
    PROJECT_ROOT = SCRIPT_DIR.parent
else:
    PROJECT_ROOT = SCRIPT_DIR
os.chdir(PROJECT_ROOT)
print(f"Working directory: {PROJECT_ROOT}")

INPUT_CSV = PROJECT_ROOT / "output" / "master_annotation_table_causal.csv"
FALLBACK  = PROJECT_ROOT / "output" / "master_annotation_table_final.csv"
FIG_DIR   = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)

HTML_OUT  = FIG_DIR / "fig_knowledge_graph_full.html"
PNG_OUT   = FIG_DIR / "fig_knowledge_graph_full.png"

NODE_STYLE = {
    "Incident":         {"color": "#4A90D9", "shape": "dot",      "size": 10},
    "AnnexDomain":      {"color": "#E53935", "shape": "diamond",  "size": 30},
    "SystemPattern":    {"color": "#FF9800", "shape": "triangle", "size": 25},
    "FundamentalRight": {"color": "#43A047", "shape": "star",     "size": 28},
    "HarmType":         {"color": "#8E24AA", "shape": "star",     "size": 28},
    "RootCause":        {"color": "#FDD835", "shape": "square",   "size": 25},
    "Mitigation":       {"color": "#00897B", "shape": "triangle", "size": 22},
    "SourceType":       {"color": "#795548", "shape": "square",   "size": 20},
}

EDGE_STYLE = {
    "hasDomain":       {"color": "#E53935", "width": 1.0},
    "hasPattern":      {"color": "#FF9800", "width": 1.0},
    "hasRight":        {"color": "#43A047", "width": 1.5},
    "hasHarm":         {"color": "#8E24AA", "width": 1.5},
    "hasRootCause":    {"color": "#FDD835", "width": 1.2},
    "hasMitigation":   {"color": "#00897B", "width": 1.2},
    "hasSourceType":   {"color": "#795548", "width": 0.5},
}


def slugify(text, max_len=60):
    s = re.sub(r"[^a-zA-Z0-9]+", "_", str(text).strip())
    return s[:max_len].strip("_") or "unknown"

def split_multi(val):
    if pd.isna(val) or str(val).strip() in ("", "nan"):
        return []
    return [v.strip() for v in re.split(r"[|,;]+", str(val)) if v.strip()]

def nice_label(text, max_len=30):
    text = str(text).replace("_", " ").strip()
    return (text[:max_len-1] + "…") if len(text) > max_len else text


def build_full_graph(df):
    G = nx.DiGraph()

    for _, row in df.iterrows():
        source = str(row.get("source", ""))
        sid    = str(row.get("source_id", row.get("sourceid", "")))
        title  = str(row.get("title", ""))[:120]
        desc   = str(row.get("description", ""))[:200]
        inc_id = f"inc:{sid}" if sid and sid != "nan" else f"inc:{slugify(title, 30)}"

        G.add_node(inc_id, label=nice_label(title, 35),
                   full_title=title, description=desc,
                   node_type="Incident", source=source)

        domain = str(row.get("hybrid_v2_annex_domain",
                     row.get("hybridv2annexdomain",
                     row.get("annex_domain",
                     row.get("annexdomain", "unknown"))))).lower().strip()
        if domain and domain != "nan":
            dn = f"domain:{domain}"
            G.add_node(dn, label=nice_label(domain), node_type="AnnexDomain")
            G.add_edge(inc_id, dn, relation="hasDomain")

        pattern = str(row.get("hybrid_v2_system_pattern",
                      row.get("hybridv2systempattern",
                      row.get("system_pattern",
                      row.get("systempattern", "unknown"))))).lower().strip()
        if pattern and pattern not in ("nan", "unknown"):
            pn = f"pattern:{pattern}"
            G.add_node(pn, label=nice_label(pattern), node_type="SystemPattern")
            G.add_edge(inc_id, pn, relation="hasPattern")

        for r in split_multi(row.get("rights", row.get("llmrights", ""))):
            rk = r.lower().strip()
            if rk and rk != "nan":
                rn = f"right:{rk}"
                G.add_node(rn, label=nice_label(rk), node_type="FundamentalRight")
                G.add_edge(inc_id, rn, relation="hasRight")

        for h in split_multi(row.get("harms", row.get("llmharms", ""))):
            hk = h.lower().strip()
            if hk and hk != "nan":
                hn = f"harm:{hk}"
                G.add_node(hn, label=nice_label(hk), node_type="HarmType")
                G.add_edge(inc_id, hn, relation="hasHarm")

        rc = str(row.get("root_cause", "")).lower().strip()
        if rc and rc not in ("nan", "", "unknown"):
            rcn = f"cause:{rc}"
            G.add_node(rcn, label=nice_label(rc), node_type="RootCause")
            G.add_edge(inc_id, rcn, relation="hasRootCause")

        mit = str(row.get("mitigation_reported", "")).strip()
        if mit and mit.lower() not in ("nan", "", "none_reported"):
            mn = f"mit:{slugify(mit, 40)}"
            G.add_node(mn, label=nice_label(mit, 45), node_type="Mitigation")
            G.add_edge(inc_id, mn, relation="hasMitigation")

        st = str(row.get("source_type", "")).lower().strip()
        if st and st not in ("nan", ""):
            sn = f"srctype:{st}"
            G.add_node(sn, label=nice_label(st), node_type="SourceType")
            G.add_edge(inc_id, sn, relation="hasSourceType")

    return G


def export_html(G, outpath):
    try:
        from pyvis.network import Network
    except ImportError:
        print("  pyvis not installed — generating standalone HTML manually")
        export_html_standalone(G, outpath)
        return

    net = Network(height="900px", width="100%", directed=True,
                  bgcolor="#1a1a2e", font_color="white",
                  notebook=False, cdn_resources="remote")

    net.set_options(json.dumps({
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -80,
                "centralGravity": 0.01,
                "springLength": 120,
                "springConstant": 0.02,
                "damping": 0.4
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 200}
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 100,
            "navigationButtons": True,
            "keyboard": True
        }
    }))

    for node, data in G.nodes(data=True):
        ntype = data.get("node_type", "Incident")
        style = NODE_STYLE.get(ntype, NODE_STYLE["Incident"])
        title_hover = f"<b>{data.get('full_title', data.get('label', node))}</b>"
        if data.get("description"):
            title_hover += f"<br><i>{data['description'][:150]}</i>"
        title_hover += f"<br>Type: {ntype}"
        if data.get("source"):
            title_hover += f"<br>Source: {data['source']}"

        net.add_node(node,
                     label=data.get("label", node),
                     title=title_hover,
                     color=style["color"],
                     shape=style["shape"],
                     size=style["size"],
                     group=ntype)

    for u, v, data in G.edges(data=True):
        rel = data.get("relation", "related")
        style = EDGE_STYLE.get(rel, {"color": "#666", "width": 0.5})
        net.add_edge(u, v,
                     title=rel,
                     color=style["color"],
                     width=style["width"],
                     arrows="to")

    legend_html = '<div style="position:fixed;top:10px;right:10px;background:rgba(0,0,0,0.7);padding:12px;border-radius:8px;z-index:999;">'
    legend_html += '<b style="color:white;font-size:14px;">FRIA Knowledge Graph</b><br>'
    for ntype, style in NODE_STYLE.items():
        legend_html += f'<span style="color:{style["color"]};font-size:12px;">● {ntype}</span><br>'
    legend_html += '<br><span style="color:#aaa;font-size:10px;">Scroll to zoom · Drag to pan · Click nodes to explore</span>'
    legend_html += '</div>'

    net.save_graph(str(outpath))

    with open(outpath, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("</body>", legend_html + "</body>")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  {outpath.name}  (open in browser)")


def export_html_standalone(G, outpath):
    nodes_js = []
    for node, data in G.nodes(data=True):
        ntype = data.get("node_type", "Incident")
        style = NODE_STYLE.get(ntype, NODE_STYLE["Incident"])
        nodes_js.append({
            "id": node,
            "label": data.get("label", node),
            "color": style["color"],
            "shape": style["shape"],
            "size": style["size"],
            "title": f"{data.get('full_title', node)}<br>Type: {ntype}",
            "group": ntype,
        })

    edges_js = []
    for u, v, data in G.edges(data=True):
        rel = data.get("relation", "related")
        style = EDGE_STYLE.get(rel, {"color": "#666", "width": 0.5})
        edges_js.append({
            "from": u, "to": v,
            "color": {"color": style["color"]},
            "width": style["width"],
            "arrows": "to",
            "title": rel,
        })

    legend_items = "".join(
        f'<span style="color:{s["color"]}">● {t}</span><br>'
        for t, s in NODE_STYLE.items()
    )

    html = f"""<!DOCTYPE html>
<html><head>
<title>FRIA Knowledge Graph</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ margin:0; background:#1a1a2e; font-family:sans-serif; }}
  #graph {{ width:100vw; height:100vh; }}
  #legend {{ position:fixed; top:10px; right:10px; background:rgba(0,0,0,0.8);
             padding:14px; border-radius:10px; color:white; font-size:12px; z-index:999; }}
  #legend b {{ font-size:15px; }}
  #search {{ position:fixed; top:10px; left:10px; z-index:999; }}
  #search input {{ padding:8px 14px; border-radius:6px; border:none; font-size:14px; width:280px; }}
</style>
</head><body>
<div id="search"><input type="text" id="searchbox" placeholder="Search incidents..." oninput="searchNode(this.value)"></div>
<div id="legend"><b>FRIA Knowledge Graph</b><br><br>{legend_items}<br>
<span style="color:#aaa;font-size:10px">Scroll=zoom · Drag=pan · Click=select</span></div>
<div id="graph"></div>
<script>
var nodes = new vis.DataSet({json.dumps(nodes_js)});
var edges = new vis.DataSet({json.dumps(edges_js)});
var container = document.getElementById('graph');
var data = {{ nodes: nodes, edges: edges }};
var options = {{
  physics: {{ forceAtlas2Based: {{ gravitationalConstant:-80, centralGravity:0.01,
              springLength:120, springConstant:0.02, damping:0.4 }},
              solver:'forceAtlas2Based', stabilization:{{iterations:200}} }},
  interaction: {{ hover:true, tooltipDelay:100, navigationButtons:true, keyboard:true }}
}};
var network = new vis.Network(container, data, options);

function searchNode(query) {{
  if (!query) {{ nodes.forEach(function(n) {{ nodes.update({{id:n.id, hidden:false}}); }}); return; }}
  var q = query.toLowerCase();
  nodes.forEach(function(n) {{
    var match = (n.label||'').toLowerCase().includes(q) || (n.title||'').toLowerCase().includes(q);
    nodes.update({{id:n.id, hidden:!match, opacity: match ? 1 : 0.1}});
  }});
}}
</script></body></html>"""

    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  {outpath.name}  (open in browser)")


def export_png(G, outpath):
    concepts = {n: d for n, d in G.nodes(data=True) if d.get("node_type") != "Incident"}
    incidents = {n: d for n, d in G.nodes(data=True) if d.get("node_type") == "Incident"}

    concept_degree = {n: G.degree(n) for n in concepts}

    # Inner ring = concepts, outer ring = incidents
    concept_list = sorted(concepts.keys(),
                          key=lambda n: (concepts[n].get("node_type", ""), -concept_degree.get(n, 0)))

    pos = {}
    n_concepts = len(concept_list)
    for i, node in enumerate(concept_list):
        angle = 2 * np.pi * i / max(n_concepts, 1)
        r = 3.0
        pos[node] = (r * np.cos(angle), r * np.sin(angle))

    concept_angles = {}
    for i, node in enumerate(concept_list):
        concept_angles[node] = 2 * np.pi * i / max(n_concepts, 1)

    for inc_node in incidents:
        neighbors = [n for n in G.neighbors(inc_node) if n in concepts]
        if not neighbors:
            neighbors = [n for n in G.predecessors(inc_node) if n in concepts]

        if neighbors:
            angles = [concept_angles.get(n, 0) for n in neighbors]
            avg_angle = np.mean(angles)
        else:
            avg_angle = np.random.uniform(0, 2 * np.pi)

        r = 6.0 + np.random.uniform(-0.5, 0.5)
        jitter = np.random.uniform(-0.15, 0.15)
        pos[inc_node] = (r * np.cos(avg_angle + jitter),
                         r * np.sin(avg_angle + jitter))

    fig, ax = plt.subplots(1, 1, figsize=(20, 20))
    ax.set_facecolor("#0f0f23")
    fig.patch.set_facecolor("#0f0f23")

    for u, v, d in G.edges(data=True):
        rel = d.get("relation", "")
        if rel == "hasSourceType":
            continue
        if u in pos and v in pos:
            style = EDGE_STYLE.get(rel, {"color": "#444", "width": 0.3})
            ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                    color=style["color"], linewidth=style["width"] * 0.4,
                    alpha=0.15, zorder=1)

    for node, data in incidents.items():
        if node in pos:
            src = data.get("source", "")
            c = "#3a6fb5" if src == "AIAAIC" else "#5a8a5a" if src == "ECtHR" else "#8a7a5a"
            ax.scatter(*pos[node], s=15, c=c, alpha=0.5, zorder=2, edgecolors="none")

    for node, data in concepts.items():
        if node in pos:
            ntype = data.get("node_type", "")
            style = NODE_STYLE.get(ntype, {"color": "#999", "size": 15})
            size = concept_degree.get(node, 1) * 8
            size = max(size, 40)
            size = min(size, 800)
            ax.scatter(*pos[node], s=size, c=style["color"],
                       alpha=0.9, zorder=3, edgecolors="white", linewidths=0.5)
            ax.annotate(data.get("label", node),
                        pos[node], fontsize=7, color="white",
                        ha="center", va="bottom",
                        xytext=(0, 8), textcoords="offset points",
                        fontweight="bold", zorder=4,
                        bbox=dict(boxstyle="round,pad=0.15",
                                  facecolor="#000000", alpha=0.5, edgecolor="none"))

    legend_handles = []
    for ntype, style in NODE_STYLE.items():
        legend_handles.append(mpatches.Patch(facecolor=style["color"],
                                              edgecolor="white", label=ntype))
    legend_handles.append(mpatches.Patch(facecolor="#3a6fb5", label="AIAAIC incident"))
    legend_handles.append(mpatches.Patch(facecolor="#5a8a5a", label="ECtHR case"))
    legend_handles.append(mpatches.Patch(facecolor="#8a7a5a", label="USFED use case"))

    leg = ax.legend(handles=legend_handles, loc="upper left", fontsize=9,
                    facecolor="#1a1a2e", edgecolor="#333", labelcolor="white",
                    framealpha=0.9, title="Node Types",
                    title_fontsize=10)
    leg.get_title().set_color("white")

    ax.set_title("FRIA Knowledge Graph — AI Incident Risk Linkages\n"
                 "Inner ring: concept hubs (domains, rights, harms, root causes)  ·  "
                 "Outer ring: 150 incident records",
                 fontsize=13, fontweight="bold", color="white", pad=20)
    ax.axis("off")
    ax.set_aspect("equal")

    fig.tight_layout()
    fig.savefig(str(outpath), dpi=250, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  {outpath.name}  ({250} DPI)")


def main():
    csv_path = INPUT_CSV if INPUT_CSV.exists() else FALLBACK
    if not csv_path.exists():
        print(f"ERROR: No input CSV found")
        import sys; sys.exit(1)

    df = pd.read_csv(csv_path)
    print(f"STEP 13  Visual Knowledge Graph")
    print(f"  Loaded {len(df)} rows from {csv_path.name}")

    G = build_full_graph(df)
    print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print("\n  Building interactive HTML graph...")
    export_html(G, HTML_OUT)

    print("\n  Building static PNG...")
    export_png(G, PNG_OUT)

    print(f"\n  Done! HTML: {HTML_OUT}")
    print(f"  PNG: {PNG_OUT}")


if __name__ == "__main__":
    main()
