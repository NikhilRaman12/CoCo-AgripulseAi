# SupplyShield 3-Minute Demo

0:00 — Problem
Supply-chain teams have supplier, inventory, shipment, plant, order and customer information spread across systems. A delayed supplier can become a plant shortage and then a customer failure.

0:25 — Governed model
Show Supplier -> Part -> Plant -> Shipment -> Order -> Customer. Explain that the semantic view defines entities, relationships and metrics once.

0:50 — Risk radar
Open the Streamlit app. Show Plant P07 / Thermal Module, days of cover, delayed shipments and risk score.

1:15 — Killer question
Ask: "Which suppliers are putting Plant P07 at risk, and which customer orders are affected?"

1:55 — Follow the chain
Show S104 -> P204 -> P07 -> SH7001/SH7006 -> O9001/O9006 -> MedCore Devices.

2:20 — Low-compute design
SQL computes metrics and risk deterministically. The semantic view constrains business meaning. Cortex Agent handles natural-language orchestration and explanation. No external vector database, GPU model, or large ML training job.

2:40 — Human value
"SupplyShield turns a fragmented supply chain into one governed decision: what is at risk, who is affected, why, and what to investigate next."

Final line
"AI should not guess the business metric. SupplyShield gives AI a governed model of the business first."
