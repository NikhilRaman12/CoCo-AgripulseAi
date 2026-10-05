# SupplyShield — Governed Supply Chain Skill

Use the SupplyShield ontology and governed semantic view for supply-chain questions.

Ontology: Supplier -> Part -> Plant -> Shipment -> Order -> Customer.

Source of truth: SUPPLYSHIELD.CORE.SUPPLY_CHAIN_SEMANTIC.

Governed metrics:
- on_time_delivery_rate: percentage delivered on or before promised date
- days_of_cover: on-hand quantity divided by average daily demand
- total_order_quantity: sum of ordered units
- total_on_hand: current inventory
- risk_score: deterministic indicator from SUPPLYSHIELD.CORE.V_STOCKOUT_RISK

Rules:
1. Never invent a metric or join path.
2. Never answer SupplyShield data questions from general knowledge.
3. For risk questions identify supplier, part, plant, shipment and downstream order/customer impact when available.
4. Prefer SQL over LLM reasoning for arithmetic.
5. State the evidence used.
6. If data is insufficient, say what is missing.
7. Keep responses concise and operational.
