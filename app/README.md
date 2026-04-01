# FRIA Evidence Retrieval Prototype

Minimal Flask application for querying the FRIA knowledge graph.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser.

## Features

- **Structured query form**: filter incidents by Annex III domain, fundamental rights, and system pattern
- **Raw SPARQL**: write custom queries against the knowledge graph
- **Results table**: view matching incidents with full annotation metadata
