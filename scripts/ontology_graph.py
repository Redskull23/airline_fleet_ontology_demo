import yaml
import networkx as nx
from pathlib import Path
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "artifacts" / "ontology_graph.png"

# Load ontology (works whether ontology/base_zero.yaml exists or not)
yaml_path = BASE / "ontology" / "base_zero.yaml"
if yaml_path.exists():
    ont = yaml.safe_load(yaml_path.read_text())
else:
    ont = {
        "entities": {"Aircraft": {}, "SensorReading": {}, "WorkOrder": {}, "Part": {}, "Alert": {}},
        "relations": {
            "Aircraft_has_SensorReading": {"from": "Aircraft", "to": "SensorReading", "via": "aircraft_id"},
            "Aircraft_has_WorkOrder": {"from": "Aircraft", "to": "WorkOrder", "via": "aircraft_id"},
            "WorkOrder_uses_Part": {"from": "WorkOrder", "to": "Part", "via": "part_number"},
            "Aircraft_has_Alert": {"from": "Aircraft", "to": "Alert", "via": "aircraft_id"}
        }
    }

# Construct graph
G = nx.DiGraph()
for entity in ont["entities"]:
    G.add_node(entity)

for _, rel in ont["relations"].items():
    G.add_edge(rel["from"], rel["to"], label=rel.get("via", ""))

# Draw with improved layout
plt.figure(figsize=(9, 7))
pos = nx.spring_layout(G, seed=13)  # stable layout

nx.draw(
    G, pos, with_labels=True, node_size=2200, node_color="#d9e8ff",
    font_size=12, font_weight="bold", edge_color="#555"
)

edge_labels = nx.get_edge_attributes(G, "label")
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

plt.savefig(OUT, dpi=180, bbox_inches="tight")
print(f"WROTE {OUT}")