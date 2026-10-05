# SupplyShield

Prevent stockouts before they become emergencies.

SupplyShield is a Snowflake-native, low-compute supply-chain intelligence prototype for Problem Statement 05 — Supply Chain Ontology and Governed Conversational Analytics.

## Killer question

Which essential medicines are likely to stock out in the next 14 days, which hospitals will be affected, and what is the lowest-cost intervention?

## Architecture

User -> CoCo CLI -> SupplyShield skill -> governed semantic views -> deterministic SQL -> evidence package -> Cortex explanation -> decision.

## Run

1. Execute sql/01_schema.sql.
2. Execute sql/02_seed.sql.
3. Execute sql/03_semantic.sql.
4. Ask CoCo:
   - Which medicines at P07 are at high stockout risk and why?
   - Which hospitals will be affected if the delayed M001 shipment slips another 3 days?
   - What is the cheapest intervention based on current inventory and incoming supply?

## Safety boundary

This prototype supports procurement and supply-chain decisions using synthetic data. It does not provide clinical diagnosis, treatment or patient-specific medical advice.

## Ontology

Supplier -> Medicine/Part -> Plant -> Shipment -> Order -> Hospital/Customer
