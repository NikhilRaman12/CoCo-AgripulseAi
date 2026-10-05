# SupplyShield AI

Governed Supply-Chain Intelligence for Preventing Operational Shortages.

Built for the Snowflake CoCo CLI Hackathon 2026 — Problem Statement 05: Supply Chain Ontology and Governed Conversational Analytics.

## Why this exists
Supply-chain teams have supplier, inventory, shipment, plant, order and customer information spread across systems. The same question can produce different answers because business definitions and join paths are inconsistent.

SupplyShield creates one governed ontology and turns it into operational decisions.

## Real-world workflow
A user asks: "Which suppliers are putting Plant P07 at risk, and which customer orders are affected?"

SupplyShield resolves the question against a semantic view, runs deterministic Snowflake analytics, follows the relationship chain, and returns an evidence-backed answer.

## Architecture
User -> CoCo/Cortex Agent -> Governed Semantic View -> Snowflake SQL -> Evidence -> Decision

Ontology:
Supplier -> Part -> Plant -> Shipment -> Order -> Customer

## Low-cost principle
SupplyShield is SQL-first and AI-second.
- No external LLM
- No external vector database
- No GPU training
- No large ML pipeline
- Deterministic metrics stay in Snowflake
- Cortex Agent is used for natural-language orchestration and explanation
- Small synthetic data demonstrates the full decision path

## Snowflake components
- Snowflake tables
- Governed Semantic View
- Cortex Agent
- Cortex Analyst tool
- Snowflake SQL
- Streamlit in Snowflake
- CoCo CLI skill

## Setup
1. Open Snowflake CoCo CLI.
2. Run sql/01_supplyshield_setup.sql.
3. Run sql/02_supplyshield_semantic_and_agent.sql.
4. Deploy supplyshield_app as a Streamlit in Snowflake app using supplyshield_app/snowflake.yml.
5. Open the app and run the killer question.
6. Use the same question in the CoCo/Cortex Agent playground.

## Important
All demonstration data is synthetic. This is supply-chain decision support, not clinical advice.

See DEMO.md.
