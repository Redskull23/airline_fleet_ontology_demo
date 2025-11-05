import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

concepts = json.loads((BASE/"ontology"/"concepts.json").read_text())["concepts"]
relationships = json.loads((BASE/"ontology"/"relationships.json").read_text())["relationships"]

cypher_out = []

# Create Nodes
for entity, meta in concepts.items():
    cypher_out.append(f"// Create {entity} Nodes")
    pk = meta["primary_key"]
    cypher_out.append(f"CREATE CONSTRAINT ON (n:{entity}) ASSERT n.{pk} IS UNIQUE;")

# Create Relationships
cypher_out.append("\n// Relationships")
for rel in relationships:
    cypher_out.append(
        f"""
MATCH (a:{rel["from"]}), (b:{rel["to"]})
WHERE a.{rel["key"]} = b.{rel["key"]}
MERGE (a)-[:{rel["type"]}]->(b);
"""
    )

out_path = BASE/"artifacts"/"ontology_graph.cypher"
out_path.write_text("\n".join(cypher_out))
print(f"Cypher script written to: {out_path}")