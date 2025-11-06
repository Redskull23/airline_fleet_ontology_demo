# streamlit_app.py
import streamlit as st
import pandas as pd
from pathlib import Path
import subprocess
import json
from streamlit.components.v1 import html

# =========================================================
# Paths & Setup
# =========================================================
BASE = Path(__file__).resolve().parents[0]
RAW  = BASE / "data" / "raw"
STD  = BASE / "data" / "standardized"
ART  = BASE / "artifacts"
ONTO = BASE / "ontology"

STD.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

# =========================================================
# Page & Theme (airline-style palette; no brand names)
# =========================================================
st.set_page_config(page_title="Fleet Health Ontology — Demo", layout="wide")

PRIMARY = "#002D72"   
ACCENT  = "#C8102E"   
INK     = "#111111"   
MUTED   = "#6B7280"   
PANEL   = "#F5F7FA"   

st.markdown(
    f"""
    <style>
        :root {{
            --primary: {PRIMARY};
            --accent: {ACCENT};
            --ink: {INK};
            --muted: {MUTED};
            --panel: {PANEL};
        }}
        .app-title {{
            font-size: 28px; 
            font-weight: 700; 
            color: var(--primary);
            margin: 0 0 8px 0;
        }}
        .app-caption {{
            color: var(--muted);
            margin-bottom: 18px;
        }}
        .panel {{
            background: var(--panel);
            border: 1px solid #e6e9ee;
            border-radius: 10px;
            padding: 14px 16px;
            margin: 8px 0 18px 0;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
            margin: 6px 0 10px 0;
        }}
        .success-note {{
            border-left: 4px solid var(--primary);
            padding-left: 10px;
        }}
        .warn-note {{
            border-left: 4px solid var(--accent);
            padding-left: 10px;
        }}
        /* Buttons tint */
        .stButton>button {{
            background-color: var(--primary) !important;
            color: white !important;
            border: 0 !important;
            border-radius: 6px !important;
        }}
        .stButton>button:hover {{
            background-color: #001f50 !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="app-title">Fleet Health Ontology — Interactive Demo</div>', unsafe_allow_html=True)
st.markdown('<div class="app-caption">Standardize → Validate → Visualize → Export</div>', unsafe_allow_html=True)

# =========================================================
# Utilities
# =========================================================
def run_script(path: Path) -> tuple[str, str]:
    """Run a local python script and return (stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["python", str(path)],
            capture_output=True,
            text=True,
            cwd=str(BASE),
        )
        return proc.stdout, proc.stderr
    except Exception as e:
        return "", f"ERROR running {path}: {e}"

def list_standardized_files() -> list[str]:
    return sorted(p.name for p in STD.glob("*.csv"))

# =========================================================
# Sidebar Controls
# =========================================================
st.sidebar.header("Pipeline Controls")

if st.sidebar.button("Build Data", use_container_width=True):
    out, err = run_script(BASE / "scripts" / "ingest.py")
    if err.strip():
        st.error("Build encountered errors. See logs below.")
        st.code(err, language="bash")
    st.success("Data build complete.")
    st.code(out or "(no stdout)", language="bash")

    with st.container():
        st.markdown('<div class="section-title">Generated Files</div>', unsafe_allow_html=True)
        files = list_standardized_files()
        st.write(files if files else "(none)")

if st.sidebar.button("Validate", use_container_width=True):
    out, err = run_script(BASE / "scripts" / "validate.py")
    if err.strip():
        st.error("Validation encountered errors. See logs below.")
        st.code(err, language="bash")
    st.info("Validation output:")
    st.code(out or "(no stdout)", language="bash")

if st.sidebar.button("Render Ontology Graph", use_container_width=True):
    out, err = run_script(BASE / "scripts" / "ontology_graph.py")
    if err.strip():
        st.error("Graph render encountered errors. See logs below.")
        st.code(err, language="bash")
    st.success("Static ontology graph rendered.")
    st.code(out or "(no stdout)", language="bash")

if st.sidebar.button("Build Interactive Graph", use_container_width=True):
    out, err = run_script(BASE / "scripts" / "interactive_graph.py")
    if err.strip():
        st.error("Interactive graph encountered errors. See logs below.")
        st.code(err, language="bash")
    st.success("Interactive graph generated.")
    st.code(out or "(no stdout)", language="bash")

if st.sidebar.button("Generate Cypher", use_container_width=True):
    concepts_path = ONTO / "concepts.json"
    rels_path = ONTO / "relationships.json"
    if not concepts_path.exists() or not rels_path.exists():
        st.warning("Missing ontology files. Expected: ontology/concepts.json and ontology/relationships.json")
    else:
        try:
            concepts = json.loads(concepts_path.read_text())["concepts"]
            relationships = json.loads(rels_path.read_text())["relationships"]
            lines = []
            for entity, meta in concepts.items():
                pk = meta.get("primary_key", "id")
                lines.append(
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{entity}) REQUIRE n.{pk} IS UNIQUE;"
                )
            lines.append("// Relationships")
            for rel in relationships:
                lines.append(
                    "MATCH (a:{from_lab}), (b:{to_lab})\n"
                    "WHERE a.{key} = b.{key}\n"
                    "MERGE (a)-[:{rtype}]->(b);".format(
                        from_lab=rel["from"],
                        to_lab=rel["to"],
                        key=rel["key"],
                        rtype=rel["type"],
                    )
                )
            cy_file = ART / "ontology_graph.cypher"
            cy_file.write_text("\n".join(lines))
            st.success(f"Wrote {cy_file}")
            preview = "\n".join(lines)
            st.code(preview[:2000] + ("\n... (truncated)" if len(preview) > 2000 else ""), language="cypher")
        except Exception as e:
            st.error(f"Error generating Cypher: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("Suggested order: Build → Validate → Static Graph → Interactive Graph → Cypher.")

# =========================================================
# Main Content Tabs
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "Ontology",
    "Standardized Data",
    "Features & Alerts",
    "Graphs & Exports",
])

# --------------- Ontology Tab ---------------
with tab1:
    st.markdown('<div class="section-title">Concepts</div>', unsafe_allow_html=True)
    concepts_path = ONTO / "concepts.json"
    if concepts_path.exists():
        try:
            concepts = json.loads(concepts_path.read_text())["concepts"]
            rows = []
            for ent, meta in concepts.items():
                rows.append({
                    "entity": ent,
                    "primary_key": meta.get("primary_key", ""),
                    "tags": ", ".join(meta.get("tags", [])),
                    "description": meta.get("description", "")
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        except Exception as e:
            st.error(f"Could not parse concepts.json: {e}")
    else:
        st.info("Missing ontology/concepts.json")

    st.markdown('<div class="section-title">Relationships</div>', unsafe_allow_html=True)
    rels_path = ONTO / "relationships.json"
    if rels_path.exists():
        try:
            rels = json.loads(rels_path.read_text())["relationships"]
            st.dataframe(pd.DataFrame(rels), use_container_width=True)
        except Exception as e:
            st.error(f"Could not parse relationships.json: {e}")
    else:
        st.info("Missing ontology/relationships.json")

# --------------- Standardized Data Tab ---------------
with tab2:
    st.markdown('<div class="section-title">Current Outputs</div>', unsafe_allow_html=True)
    if STD.exists():
        csvs = sorted(STD.glob("*.csv"))
        if not csvs:
            st.info("No standardized files yet. Use Build Data in the sidebar.")
        for p in csvs:
            st.markdown(f"**{p.name}**")
            try:
                df = pd.read_csv(p)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Error reading {p.name}: {e}")
    else:
        st.info("Standardized folder not found.")

# --------------- Features & Alerts Tab ---------------
with tab3:
    st.markdown('<div class="section-title">Feature Table: Aircraft Health</div>', unsafe_allow_html=True)
    f = STD / "features_aircraft_health.csv"
    if f.exists():
        try:
            st.dataframe(pd.read_csv(f), use_container_width=True)
        except Exception as e:
            st.error(f"Error reading features_aircraft_health.csv: {e}")
    else:
        st.info("Run Build Data to generate features.")

    st.markdown('<div class="section-title">Alerts</div>', unsafe_allow_html=True)
    a = STD / "alerts.csv"
    if a.exists():
        try:
            st.dataframe(pd.read_csv(a), use_container_width=True)
        except Exception as e:
            st.error(f"Error reading alerts.csv: {e}")
    else:
        st.info("Run Build Data to generate alerts.")

# --------------- Graphs & Exports Tab ---------------
with tab4:
    st.markdown('<div class="section-title">Static Ontology Graph (PNG)</div>', unsafe_allow_html=True)
    img = ART / "ontology_graph.png"
    if img.exists():
        st.image(str(img), caption="Entity graph (rendered by scripts/ontology_graph.py)")
    else:
        st.info("Use Render Ontology Graph in the sidebar to generate the static graph.")

    st.markdown('<div class="section-title">Interactive Graph (Physics)</div>', unsafe_allow_html=True)
    html_path = ART / "ontology_graph_interactive.html"
    if html_path.exists():
        html(html_path.read_text(), height=720, scrolling=True)
    else:
        st.info("Use Build Interactive Graph in the sidebar to generate the interactive view.")

    st.markdown('<div class="section-title">Neo4j / Cypher Export</div>', unsafe_allow_html=True)
    cy = ART / "ontology_graph.cypher"
    if cy.exists():
        try:
            txt = cy.read_text()
            st.code(txt[:2000] + ("\n... (truncated)" if len(txt) > 2000 else ""), language="cypher")
        except Exception as e:
            st.error(f"Error reading ontology_graph.cypher: {e}")
    else:
        st.info("Use Generate Cypher in the sidebar to create the export.")