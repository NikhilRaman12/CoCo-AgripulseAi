# SupplyShield AI

## Governed Supply-Chain Intelligence for Real Operational Decisions

Snowflake CoCo CLI Hackathon 2026 — Problem Statement 05

SupplyShield turns fragmented supplier, inventory, shipment, plant, order and customer data into one governed decision layer.

### The problem

The same supply-chain question can produce different answers because teams use different definitions, spreadsheets and join paths.

SupplyShield defines the business ontology once:

Supplier -> Part -> Plant -> Shipment -> Order -> Customer

Then a natural-language question is resolved through a Snowflake Semantic View and executed against governed metrics.

### Killer question

Which suppliers are putting Plant P07 at risk, and which customer orders are affected?

The system returns:
- risk level and days of cover
- delayed supplier shipments
- affected parts and plants
- downstream orders and customers
- governed metrics and evidence
- an operational next step

### Architecture

Natural language -> Cortex Agent -> Governed Semantic View -> Snowflake SQL -> Deterministic risk analytics -> Evidence -> Decision

### Why this is different

SQL-first. AI-second.

We do not use an LLM to calculate inventory, delivery performance or risk.

Snowflake calculates the business truth.

Cortex handles natural-language orchestration and explanation.

This keeps the prototype:
- low-compute
- low-cost
- explainable
- auditable
- resistant to hallucinated business metrics

No external LLM, vector database, GPU training or large ML pipeline is required.

### Project files

- sql/01_supplyshield_setup.sql — synthetic enterprise data and deterministic risk views
- sql/02_supplyshield_semantic_and_agent.sql — governed Semantic View and Cortex Agent
- supplyshield_app/streamlit_app.py — Snowflake Streamlit command center
- .cortex/skills/supplyshield/SKILL.md — CoCo domain skill
- DEMO.md — 3-minute judge walkthrough
- README_SUPPLYSHIELD.md — detailed project description

### Run

Execute the two SQL scripts in Snowflake CoCo CLI, deploy the Streamlit app, then ask the killer question.

All demonstration data is synthetic. This is supply-chain operational decision support.

---
Built by Nikhil Raman
