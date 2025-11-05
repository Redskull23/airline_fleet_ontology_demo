# scripts/interactive_graph.py
import json
import yaml
from pathlib import Path
from html import escape

BASE = Path(__file__).resolve().parents[1]
ONTO_YAML = BASE / "ontology" / "base_zero.yaml"
CONCEPTS_JSON = BASE / "ontology" / "concepts.json"
RELS_JSON = BASE / "ontology" / "relationships.json"
OUT_HTML = BASE / "artifacts" / "ontology_graph_interactive.html"

TAG_COLORS = {
    "asset": "#2b8a3e",
    "telemetry": "#1d4ed8",
    "maintenance": "#b45309",
    "component": "#7c3aed",
    "signal": "#dc2626",
}
DEFAULT_COLOR = "#64748b"


def pick_color(tags):
    if not tags:
        return DEFAULT_COLOR
    for t in tags:
        if t in TAG_COLORS:
            return TAG_COLORS[t]
    return DEFAULT_COLOR


def load_ontology():
    """Return (concepts_dict, relationships_list). Prefer concepts/relationships JSON for richer tags."""
    if CONCEPTS_JSON.exists() and RELS_JSON.exists():
        concepts = json.loads(CONCEPTS_JSON.read_text())["concepts"]
        rels = json.loads(RELS_JSON.read_text())["relationships"]
        return concepts, rels

    if ONTO_YAML.exists():
        y = yaml.safe_load(ONTO_YAML.read_text())
        concepts = {
            ent: {"description": "", "tags": [], "primary_key": "id"} for ent in y.get("entities", {}).keys()
        }
        rels = []
        for _, r in (y.get("relations") or {}).items():
            rels.append(
                {
                    "from": r["from"],
                    "to": r["to"],
                    "type": r.get("type", r.get("via", "RELATES_TO")),
                    "key": r.get("via", "id"),
                }
            )
        return concepts, rels

    # minimal fallback
    concepts = {
        "Aircraft": {"tags": ["asset"], "primary_key": "aircraft_id"},
        "SensorReading": {"tags": ["telemetry"], "primary_key": "reading_id"},
        "WorkOrder": {"tags": ["maintenance"], "primary_key": "wo_id"},
        "Part": {"tags": ["component"], "primary_key": "part_number"},
        "Alert": {"tags": ["signal"], "primary_key": "alert_id"},
    }
    rels = [
        {"from": "Aircraft", "to": "SensorReading", "type": "HAS_TELEMETRY", "key": "aircraft_id"},
        {"from": "Aircraft", "to": "WorkOrder", "type": "HAS_MAINTENANCE_ACTION", "key": "aircraft_id"},
        {"from": "WorkOrder", "to": "Part", "type": "CONSUMES_COMPONENT", "key": "part_number"},
        {"from": "Aircraft", "to": "Alert", "type": "HAS_HEALTH_SIGNAL", "key": "aircraft_id"},
    ]
    return concepts, rels


def to_vis_data(concepts, relationships):
    nodes = []
    edges = []

    for entity, meta in concepts.items():
        tags = meta.get("tags", [])
        color = pick_color(tags)
        title = f"<b>{escape(entity)}</b><br>Tags: {escape(', '.join(tags) or '-')}" \
                f"<br>PK: {escape(meta.get('primary_key', 'id'))}"
        nodes.append(
            {
                "id": entity,
                "label": entity,
                "color": {"background": color, "border": "#111", "highlight": {"background": color, "border": "#111"}},
                "shape": "dot",
                "size": 20,
                "title": title,
                "font": {"size": 16, "bold": True},
            }
        )

    for rel in relationships:
        rtype = rel.get("type") or rel.get("name") or "RELATES_TO"
        key = rel.get("key", "")
        title = f"{escape(rtype)} (key: {escape(key)})"
        edges.append(
            {
                "from": rel["from"],
                "to": rel["to"],
                "arrows": "to",
                "label": rtype,
                "title": title,
                "font": {"size": 12, "align": "top"},
                "color": {"color": "#555"},
                "smooth": {"type": "dynamic"},
            }
        )
    return nodes, edges


def write_html(nodes, edges, out_path: Path):
    options = {
        "physics": {
            "enabled": True,
            "barnesHut": {
                "gravitationalConstant": -3000,
                "centralGravity": 0.3,
                "springLength": 150,
                "springConstant": 0.04,
                "damping": 0.09,
            },
            "stabilization": {"enabled": True, "iterations": 250},
        },
        "interaction": {"hover": True, "tooltipDelay": 120},
    }

    html_str = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Ontology Graph (Interactive)</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="preconnect" href="https://cdnjs.cloudflare.com">
<style>
  html, body {{ height: 100%; margin: 0; }}
  #mynetwork {{ width: 100%; height: 95vh; border: 1px solid #ccc; }}
  .legend {{ padding: 8px 12px; font-family: sans-serif; font-size: 14px; }}
  .pill {{ display:inline-block; padding:2px 8px; margin:2px; border-radius:12px; color:#fff; }}
</style>
</head>
<body>
<div class="legend">
  <strong>Legend:</strong>
  <span class="pill" style="background:{TAG_COLORS.get('asset', '#2b8a3e')}">asset</span>
  <span class="pill" style="background:{TAG_COLORS.get('telemetry', '#1d4ed8')}">telemetry</span>
  <span class="pill" style="background:{TAG_COLORS.get('maintenance', '#b45309')}">maintenance</span>
  <span class="pill" style="background:{TAG_COLORS.get('component', '#7c3aed')}">component</span>
  <span class="pill" style="background:{TAG_COLORS.get('signal', '#dc2626')}">signal</span>
</div>
<div id="mynetwork"></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.9/standalone/umd/vis-network.min.js"></script>
<script>
  const nodes = new vis.DataSet({json.dumps(nodes)});
  const edges = new vis.DataSet({json.dumps(edges)});
  const container = document.getElementById('mynetwork');
  const data = {{ nodes, edges }};
  const options = {json.dumps(options)};
  const network = new vis.Network(container, data, options);
  // Fit once stabilization is done
  network.once('stabilizationIterationsDone', function() {{
    network.fit({{animation: true}});
  }});
</script>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_str, encoding="utf-8")
    print(str(out_path))


def main():
    concepts, relationships = load_ontology()
    nodes, edges = to_vis_data(concepts, relationships)
    write_html(nodes, edges, OUT_HTML)


if __name__ == "__main__":
    main()