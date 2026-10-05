# SupplyShield — Low-Compute Stockout Prevention

## Problem
Essential-medicine procurement teams often discover shortages only after inventory becomes critical. ERP inventory, supplier reliability, shipments, orders and demand signals are fragmented.

## Product
SupplyShield is a governed Snowflake decision-support layer for preventing stockouts.

It answers: Which essential medicines are at risk, why, who will be affected, and what is the lowest-cost safe intervention?

This is procurement and supply-chain decision support, not clinical advice.

## Design principle
Deterministic first, AI second.

SQL calculates coverage, delay, risk and intervention inputs. Cortex is used only to translate a compact evidence package into a human-readable explanation.

## Hackathon alignment
Problem Statement 05 — Supply Chain Ontology and Governed Conversational Analytics.

Ontology:
Supplier -> Medicine/Part -> Plant -> Shipment -> Order -> Hospital/Customer
