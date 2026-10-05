# Hackathon Submission Pack

## Title
SupplyShield AI — Governed Supply-Chain Intelligence

## One-line pitch
A low-compute Snowflake intelligence layer that turns fragmented supplier, inventory, shipment, plant, order and customer data into one governed answer: what is at risk, who is affected, why, and what to investigate next.

## Problem Statement
05 — Supply Chain Ontology and Governed Conversational Analytics

## Killer user question
Which suppliers are putting Plant P07 at risk, and which customer orders are affected?

## Why it matters
Supply-chain failures propagate. A delayed supplier can become a plant shortage, then an order miss and finally a customer impact. SupplyShield exposes the full relationship chain before the failure is hidden inside separate dashboards.

## Innovation
The prototype is SQL-first and AI-second. Snowflake computes governed metrics and deterministic risk signals. Cortex Agent translates natural language into governed analytics through a Semantic View and explains the evidence. This avoids expensive ML training, external vector stores and LLM-based arithmetic.

## Snowflake-native implementation
- CoCo CLI custom skill
- Snowflake Semantic View
- Cortex Agent
- Cortex Analyst tool
- Snowflake SQL risk views
- Streamlit in Snowflake
- Synthetic enterprise data

## End-to-end flow
Natural language -> Cortex Agent -> Semantic View -> governed SQL -> risk/evidence -> downstream impact -> operational decision.

## Demo proof
Supplier S104 -> Part P204 -> Plant P07 -> delayed shipments SH7001/SH7006 -> orders O9001/O9006 -> customer MedCore Devices.

## Responsible scope
Synthetic data only. Operational supply-chain decision support. No clinical decision making.

## Repository
https://github.com/NikhilRaman12/CoCo-AgripulseAi

## Demo
See DEMO.md and deploy supplyshield_app in Snowflake.
