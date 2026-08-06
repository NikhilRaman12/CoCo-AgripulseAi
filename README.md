# CoCo-AgriPulseAI

**Unstructured Data Intelligence System for Agriculture**

Snowflake CoCo CLI Hackathon 2026 | Problem Statement 01

---

## What It Does

CoCo-AgriPulseAI extracts, interprets, and derives actionable intelligence from unstructured agricultural documents (government advisories, research papers, farmer field reports, insurance claims) and combines them with structured data (yield records, market prices, pest databases) to deliver real-time crop management decisions.

A farmer asks a question. The system searches across 8 unstructured documents and 12 structured tables, trains ML models on 4,500+ records, and returns a grounded, citation-backed advisory — all within Snowflake, powered by CoCo CLI.

---

## Architecture

```
                         USER QUERY
                             |
                    CoCo Intelligence Orchestrator
                    (Intent Detection + Routing)
                             |
              +--------------+--------------+
              |                             |
    UNSTRUCTURED PIPELINE           STRUCTURED PIPELINE
              |                             |
  +-------------------+         +-------------------+
  | Raw Documents     |         | CURATED Schema    |
  | (Advisories, PDFs,|         | (12 tables,       |
  |  Farmer Reports,  |         |  4,768 records)   |
  |  Research Papers) |         +-------------------+
  +-------------------+                  |
         |                    +----------+----------+
         v                    |          |          |
  +-------------------+   Agronomy  Protection  Procurement
  | Cortex AI LLM     |   Agent     Agent       Agent
  | - AI_EXTRACT      |      |          |          |
  | - AI_CLASSIFY     |      +----------+----------+
  | - AI_SUMMARIZE    |                  |
  +-------------------+         +-------------------+
         |                      | ML Pipeline       |
         v                      | (GradientBoosting |
  +-------------------+         |  RandomForest)    |
  | Cortex Search     |         +-------------------+
  | Service           |                  |
  | (Semantic RAG)    |                  |
  +-------------------+                  |
              |                          |
              +--------------+-----------+
                             |
                   COMBINED INTELLIGENCE
                   (Cortex AI Fusion)
                             |
                    Evidence & Trust Agent
                    (Validation + Grounding)
                             |
                    Decision Intelligence Agent
                             |
                   ACTIONABLE REPORT + ACTION PLAN
```

---

## Snowflake Services Used

| Service | Usage |
|---------|-------|
| **Cortex LLM** (`SNOWFLAKE.CORTEX.COMPLETE`) | Entity extraction, classification, summarization from unstructured text |
| **Cortex Search** | Semantic search over agricultural document corpus |
| **Snowpark Python** | ML model training (scikit-learn) on Snowflake compute |
| **Snowflake Tables** | Structured knowledge base (12 tables, 3 schemas) |
| **CoCo CLI** | Entire development and execution environment |

---

## Data Architecture

### AGRIPULSE.UNSTRUCTURED — Document Intelligence
| Table | Purpose |
|-------|---------|
| `RAW_DOCUMENTS` | 8 ingested documents (advisories, research, farmer reports, insurance claims) |
| `PROCESSED_DOCUMENTS` | AI-processed: extracted entities, classification, summaries |
| `DOC_SEARCH_SERVICE` | Cortex Search for semantic retrieval |

### AGRIPULSE.CURATED — Structured Knowledge Base
| Table | Records | Source |
|-------|---------|--------|
| `CROP_MASTER` | 3 | Core profiles (rice, cotton, chilli) |
| `CROP_GROWTH_STAGES` | 19 | Stage-wise agronomy |
| `PEST_DISEASE_KB` | 16 | Pests/diseases with full IPM protocols |
| `MSP_HISTORY` | 21 | Government MSP rates 2019-2025 (CACP) |
| `MARKET_PRICES` | 15 | Mandi prices across major markets |
| `NUTRIENT_RECOMMENDATIONS` | 8 | ICAR fertilizer schedules |
| `CROP_WEATHER_THRESHOLDS` | 12 | Critical weather limits |
| `YIELD_HISTORY` | 40 | State-wise actuals 2020-2023 (DES) |

### AGRIPULSE.FEATURES — ML Training Data
| Dataset | Rows | Task |
|---------|------|------|
| `RICE_YIELD_TRAINING` | 1,200 | Regression (15 features) |
| `COTTON_YIELD_TRAINING` | 1,000 | Regression (16 features) |
| `CHILLI_YIELD_TRAINING` | 800 | Regression (16 features) |
| `PEST_RISK_TRAINING` | 1,500 | Classification (15 features) |

---

## Multi-Agent System

| Agent | Responsibility |
|-------|---------------|
| **Orchestrator** | Intent detection, conditional routing, execution planning |
| **Data Intelligence** | Dataset discovery, quality validation, lineage |
| **Agronomy Intelligence** | Growth stages, soil, nutrients, irrigation, weather |
| **Crop Protection** | Pest prediction, risk scoring, IPM recommendations |
| **Crop Intelligence** | ML pipeline (train → predict → explain) |
| **Knowledge Intelligence** | RAG over unstructured documents via Cortex Search |
| **Procurement Intelligence** | MSP, market prices, demand-supply, strategy |
| **Evidence & Trust** | Validation, hallucination check, confidence scoring |
| **Decision Intelligence** | Final report, action plan, NL response |

---

## Evaluation Criteria Alignment

### Real-World Relevance (30%)

- **Genuine business need**: Indian agriculture employs 42% of the workforce. Farmers lose 15-25% yield annually to pests due to delayed information. This system delivers real-time, AI-powered advisories.
- **Realistic data sources**: Government advisories (IMD/MoA), ICAR research, farmer WhatsApp complaints, PMFBY insurance claims — exactly how agricultural data flows in India.
- **Domain**: Rice, Cotton, Chilli — three crops covering 60+ million hectares and 100+ million farmers.

### Technical Execution (40%)

- **Unstructured ingestion**: 8 real-format documents (multi-page advisories, research papers, field reports)
- **AI processing**: Cortex LLM extracts entities, classifies documents, generates summaries
- **Semantic search**: Cortex Search Service enables natural language queries over the corpus
- **Structured + unstructured integration**: ML models use structured features; Cortex AI fuses both pipelines for final advisory
- **ML pipeline**: GradientBoosting (yield prediction) + RandomForest (pest risk classification) with cross-validation
- **Multi-agent architecture**: 9 specialized agents with typed state, A2A messaging, conditional routing

### Solution Completeness (30%)

Full lifecycle demonstrated in a single execution:
1. **Ingest** → Raw unstructured documents loaded
2. **Process** → Cortex AI extracts, classifies, summarizes
3. **Search** → Cortex Search enables semantic retrieval
4. **Analyze** → Structured data queried across 12 tables
5. **Predict** → ML models trained and predictions generated
6. **Fuse** → Cortex AI combines structured + unstructured insights
7. **Validate** → Evidence & Trust agent verifies outputs
8. **Deliver** → Actionable report with timeline and action plan

---

## How to Run

```bash
# In Snowflake CoCo CLI / Snowsight Workspace:
# 1. Open run_agripulse.py
# 2. Connect to a compute service
# 3. Run the file

# Output: Full 5-phase intelligence report
# Phase 1: Unstructured AI Processing
# Phase 2: Structured Data Intelligence
# Phase 3: ML Model Training & Prediction
# Phase 4: Combined Intelligence (Cortex AI fusion)
# Phase 5: Final Report + Action Plan
```

---

## Project Structure

```
workspace/
├── run_agripulse.py              # Main demo (full lifecycle execution)
├── gdrive_sync.py                # Google Drive MCP sync script
├── .env                          # Configuration (secrets excluded)
├── requirements.txt              # Python dependencies
└── agripulse/                    # Multi-agent framework
    ├── __init__.py
    ├── state.py                  # Typed Shared State (Pydantic)
    ├── config.py                 # Secure environment config
    ├── graph.py                  # LangGraph StateGraph
    ├── main.py                   # CLI entry point
    ├── agents/
    │   ├── base.py               # Abstract base (execute/validate/health/metrics/tests)
    │   ├── orchestrator.py       # Intent + conditional routing
    │   ├── data_intelligence.py
    │   ├── agronomy_intelligence.py
    │   ├── crop_protection.py
    │   ├── crop_intelligence.py  # Full ML pipeline
    │   ├── knowledge_intelligence.py
    │   ├── procurement_intelligence.py
    │   ├── evidence_trust.py
    │   └── decision_intelligence.py
    └── mcp/
        ├── snowflake_tools.py    # Snowflake MCP (secure auth)
        ├── gdrive_tools.py       # Google Drive MCP
        └── external_tools.py     # Weather + Market + Research APIs
```

---

## Key Design Decisions

1. **Cortex AI over external LLMs** — All AI processing stays within Snowflake. No data leaves the platform.
2. **Secure auth** — No passwords stored. Uses session tokens (workspace) or key-pair (production).
3. **Real agricultural data** — Based on published ICAR, CICR, CACP, Agmarknet, NHB, IMD sources.
4. **Production-ready agents** — Each agent exposes `execute()`, `validate()`, `health()`, `metrics()`, `tests()`.
5. **Cortex Search for RAG** — Semantic search over documents without external vector databases.

---

## Team

- **Nikhil Raman** — Builder, CoCo-AgriPulseAI

---

## Built With

- Snowflake CoCo CLI
- Snowflake Cortex AI (LLM + Search)
- Snowpark Python
- scikit-learn / XGBoost
- Pydantic (typed state)
- LangGraph architecture (StateGraph, conditional edges, parallel execution)

---

*CoCo-AgriPulseAI: Where unstructured agricultural intelligence meets structured data science — all on Snowflake.*
