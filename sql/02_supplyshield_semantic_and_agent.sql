USE DATABASE SUPPLYSHIELD;
USE SCHEMA CORE;

CREATE OR REPLACE SEMANTIC VIEW SUPPLY_CHAIN_SEMANTIC
 TABLES (
  suppliers AS SUPPLYSHIELD.RAW.SUPPLIERS PRIMARY KEY (SUPPLIER_ID) COMMENT='Supplier master with reliability and risk tier',
  parts AS SUPPLYSHIELD.RAW.PARTS PRIMARY KEY (PART_ID) COMMENT='Parts required by plants and orders',
  plants AS SUPPLYSHIELD.RAW.PLANTS PRIMARY KEY (PLANT_ID) COMMENT='Manufacturing plants consuming parts',
  customers AS SUPPLYSHIELD.RAW.CUSTOMERS PRIMARY KEY (CUSTOMER_ID) COMMENT='Downstream customers receiving orders',
  orders AS SUPPLYSHIELD.RAW.ORDERS PRIMARY KEY (ORDER_ID) COMMENT='Customer orders requiring parts at plants',
  shipments AS SUPPLYSHIELD.RAW.SHIPMENTS PRIMARY KEY (SHIPMENT_ID) COMMENT='Supplier shipments fulfilling orders',
  inventory AS SUPPLYSHIELD.RAW.INVENTORY PRIMARY KEY (PLANT_ID,PART_ID) COMMENT='Current plant inventory and daily demand'
 )
 RELATIONSHIPS (
  orders_to_customers AS orders (CUSTOMER_ID) REFERENCES customers,
  orders_to_plants AS orders (PLANT_ID) REFERENCES plants,
  orders_to_parts AS orders (PART_ID) REFERENCES parts,
  shipments_to_orders AS shipments (ORDER_ID) REFERENCES orders,
  shipments_to_suppliers AS shipments (SUPPLIER_ID) REFERENCES suppliers,
  shipments_to_parts AS shipments (PART_ID) REFERENCES parts,
  inventory_to_plants AS inventory (PLANT_ID) REFERENCES plants,
  inventory_to_parts AS inventory (PART_ID) REFERENCES parts
 )
 DIMENSIONS (
  suppliers.supplier_name AS SUPPLIER_NAME WITH SYNONYMS=('supplier','vendor') COMMENT='Supplier name',
  suppliers.risk_tier AS RISK_TIER COMMENT='Supplier risk tier',
  parts.part_name AS PART_NAME WITH SYNONYMS=('part','material','component') COMMENT='Part name',
  parts.criticality AS CRITICALITY WITH SYNONYMS=('priority','critical part') COMMENT='Part criticality',
  plants.plant_name AS PLANT_NAME WITH SYNONYMS=('plant','factory','site') COMMENT='Manufacturing plant',
  customers.customer_name AS CUSTOMER_NAME WITH SYNONYMS=('customer','account') COMMENT='Customer name',
  orders.order_date AS ORDER_DATE COMMENT='Order date',
  orders.required_date AS REQUIRED_DATE COMMENT='Required fulfillment date',
  orders.priority AS ORDER_PRIORITY COMMENT='Order priority',
  shipments.status AS SHIPMENT_STATUS COMMENT='Shipment status',
  inventory.snapshot_date AS SNAPSHOT_DATE COMMENT='Inventory snapshot date'
 )
 METRICS (
  orders.order_count AS COUNT(ORDER_ID) COMMENT='Number of orders',
  orders.total_order_quantity AS SUM(ORDER_QTY) COMMENT='Total units ordered',
  shipments.shipment_count AS COUNT(SHIPMENT_ID) COMMENT='Number of shipments',
  shipments.on_time_delivery_rate AS AVG(IFF(ACTUAL_DATE<=PROMISED_DATE,100,0)) COMMENT='Percentage delivered on or before promise date',
  inventory.total_on_hand AS SUM(ON_HAND_QTY) COMMENT='Units currently on hand',
  inventory.total_daily_demand AS SUM(AVG_DAILY_DEMAND) COMMENT='Average daily demand units',
  inventory.days_of_cover AS SUM(ON_HAND_QTY)/NULLIF(SUM(AVG_DAILY_DEMAND),0) COMMENT='Inventory days of cover'
 )
 COMMENT='Governed ontology: Supplier -> Part -> Plant -> Shipment -> Order -> Customer';

CREATE OR REPLACE AGENT SUPPLYSHIELD_AGENT
 COMMENT='SupplyShield governed supply-chain decision agent'
 PROFILE='{"display_name":"SupplyShield Decision Agent"}'
 FROM SPECIFICATION
 $$
 models:
   orchestration: auto
 instructions:
   response: "Answer only from the configured Supply Chain Analyst tool. Never invent metrics, suppliers, orders, customers, inventory, or dates. Prefer concise decision-oriented answers. Always state the governed metric or evidence used. For risk questions, explain why and identify downstream impact when available."
   orchestration: "Use SupplyChain_Analyst for all questions about suppliers, parts, plants, shipments, orders, customers, inventory, service level, or risk."
   sample_questions:
     - question: "Which suppliers are putting Plant P07 at risk?"
     - question: "What is the on-time delivery rate by supplier?"
     - question: "Which customer orders are exposed to delayed shipments?"
     - question: "How many days of inventory cover does Plant P07 have for critical parts?"
 tools:
   - tool_spec:
       type: "cortex_analyst_text_to_sql"
       name: "SupplyChain_Analyst"
       description: "Generates governed SQL over the SupplyShield semantic view."
 tool_resources:
   SupplyChain_Analyst:
     semantic_view: "SUPPLYSHIELD.CORE.SUPPLY_CHAIN_SEMANTIC"
     execution_environment:
       type: "warehouse"
       warehouse: "COMPUTE_WH"
 $$;

GRANT USAGE ON DATABASE SUPPLYSHIELD TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA SUPPLYSHIELD.RAW TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA SUPPLYSHIELD.CORE TO ROLE PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA SUPPLYSHIELD.RAW TO ROLE PUBLIC;
GRANT SELECT ON ALL VIEWS IN SCHEMA SUPPLYSHIELD.CORE TO ROLE PUBLIC;
GRANT USAGE ON AGENT SUPPLYSHIELD.CORE.SUPPLYSHIELD_AGENT TO ROLE PUBLIC;