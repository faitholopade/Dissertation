"""
13_visualise_knowledge_graph.py  —  Visual knowledge graph for dissertation

Produces:
  1. figures/fig_knowledge_graph_full.html   Interactive browser-based graph
  2. figures/fig_knowledge_graph_full.png    High-res static figure for submission

The HTML version is zoomable, draggable, and searchable — great for viva demos.
The PNG version is a clean, publication-ready layout for the dissertation PDF.

Usage:
    python src/13_visualise_knowledge_graph.py
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

# ── Auto-resolve project root ────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
if SCRIPT_DIR.name == "src":
    PROJECT_ROOT = SCRIPT_DIR.parent
else:
    PROJECT_ROOT = SCRIPT_DIR
os.chdir(PROJECT_ROOT)
print(f"Working directory: {PROJECT_ROOT}")

# ── Config ───────────────────────────────────────────────────────────────────
INPUT_CSV = PROJECT_ROOT / "output" / "master_annotation_table_causal.csv"
FALLBACK  = PROJECT_ROOT / "output" / "master_annotation_table_final.csv"
FIG_DIR   = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)

HTML_OUT  = FIG_DIR / "fig_knowledge_graph_full.html"
PNG_OUT   = FIG_DIR / "fig_knowledge_graph_full.png"


# ── Styling ──────────────────────────────────────────────────────────────────
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


# ── Helpers ──────────────────────────────────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════════════════════
#  BUILD FULL GRAPH
# ══════════════════════════════════════════════════════════════════════════════
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

        # Domain
        domain = str(row.get("hybrid_v2_annex_domain",
                     row.get("hybridv2annexdomain",
                     row.get("annex_domain",
                     row.get("annexdomain", "unknown"))))).lower().strip()
        if domain and domain != "nan":
            dn = f"domain:{domain}"
            G.add_node(dn, label=nice_label(domain), node_type="AnnexDomain")
            G.add_edge(inc_id, dn, relation="hasDomain")

        # Pattern
        pattern = str(row.get("hybrid_v2_system_pattern",
                      row.get("hybridv2systempattern",
                      row.get("system_pattern",
                      row.get("systempattern", "unknown"))))).lower().strip()
        if pattern and pattern not in ("nan", "unknown"):
            pn = f"pattern:{pattern}"
            G.add_node(pn, label=nice_label(pattern), node_type="SystemPattern")
            G.add_edge(inc_id, pn, relation="hasPattern")

        # Rights
        for r in split_multi(row.get("rights", row.get("llmrights", ""))):
            rk = r.lower().strip()
            if rk and rk != "nan":
                rn = f"right:{rk}"
                G.add_node(rn, label=nice_label(rk), node_type="FundamentalRight")
                G.add_edge(inc_id, rn, relation="hasRight")

        # Harms
        for h in split_multi(row.get("harms", row.get("llmharms", ""))):
            hk = h.lower().strip()
            if hk and hk != "nan":
                hn = f"harm:{hk}"
                G.add_node(hn, label=nice_label(hk), node_type="HarmType")
                G.add_edge(inc_id, hn, relation="hasHarm")

        # Root cause
        rc = str(row.get("root_cause", "")).lower().strip()
        if rc and rc not in ("nan", "", "unknown"):
            rcn = f"cause:{rc}"
            G.add_node(rcn, label=nice_label(rc), node_type="RootCause")
            G.add_edge(inc_id, rcn, relation="hasRootCause")

        # Mitigation
        mit = str(row.get("mitigation_reported", "")).strip()
        if mit and mit.lower() not in ("nan", "", "none_reported"):
            mn = f"mit:{slugify(mit, 40)}"
            G.add_node(mn, label=nice_label(mit, 45), node_type="Mitigation")
            G.add_edge(inc_id, mn, relation="hasMitigation")

        # Source type
        st = str(row.get("source_type", "")).lower().strip()
        if st and st not in ("nan", ""):
            sn = f"srctype:{st}"
            G.add_node(sn, label=nice_label(st), node_type="SourceType")
            G.add_edge(inc_id, sn, relation="hasSourceType")

    return G


# ══════════════════════════════════════════════════════════════════════════════
#  INTERACTIVE HTML (pyvis)
# ══════════════════════════════════════════════════════════════════════════════
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

    # Physics settings for good layout
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

    # Add legend as HTML overlay
    legend_html = '<div style="position:fixed;top:10px;right:10px;background:rgba(0,0,0,0.7);padding:12px;border-radius:8px;z-index:999;">'
    legend_html += '<b style="color:white;font-size:14px;">FRIA Knowledge Graph</b><br>'
    for ntype, style in NODE_STYLE.items():
        legend_html += f'<span style="color:{style["color"]};font-size:12px;">● {ntype}</span><br>'
    legend_html += '<br><span style="color:#aaa;font-size:10px;">Scroll to zoom · Drag to pan · Click nodes to explore</span>'
    legend_html += '</div>'

    net.save_graph(str(outpath))

    # Inject legend
    with open(outpath, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("</body>", legend_html + "</body>")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  {outpath.name}  (open in browser)")


def export_html_standalone(G, outpath):
    """Fallback: generate vis.js HTML without pyvis."""
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

