"""
CoCo Intelligence Orchestrator
LangGraph StateGraph with conditional edges, parallel execution, and intent routing.
"""

from __future__ import annotations

import logging
from typing import Any

from agripulse.state import (
    AgriPulseState,
    AgentRole,
    IntentType,
    ExecutionStatus,
    TraceEntry,
    A2AMessage,
)
from agripulse.agents.base import BaseAgent
from agripulse.config import AgentConfig

logger = logging.getLogger("agripulse.orchestrator")

# Intent → required agents routing table
INTENT_ROUTING: dict[IntentType, list[AgentRole]] = {
    IntentType.CROP_ADVISORY: [
        AgentRole.DATA,
        AgentRole.AGRONOMY,
        AgentRole.CROP_PROTECTION,
        AgentRole.KNOWLEDGE,
        AgentRole.EVIDENCE_TRUST,
        AgentRole.DECISION,
    ],
    IntentType.PEST_ALERT: [
        AgentRole.DATA,
        AgentRole.CROP_PROTECTION,
        AgentRole.KNOWLEDGE,
        AgentRole.EVIDENCE_TRUST,
        AgentRole.DECISION,
    ],
    IntentType.YIELD_PREDICTION: [
        AgentRole.DATA,
        AgentRole.AGRONOMY,
        AgentRole.CROP_INTELLIGENCE,
        AgentRole.EVIDENCE_TRUST,
        AgentRole.DECISION,
    ],
    IntentType.MARKET_ANALYSIS: [
        AgentRole.DATA,
        AgentRole.PROCUREMENT,
        AgentRole.EVIDENCE_TRUST,
        AgentRole.DECISION,
    ],
    IntentType.PROCUREMENT_PLAN: [
        AgentRole.DATA,
        AgentRole.AGRONOMY,
        AgentRole.PROCUREMENT,
        AgentRole.EVIDENCE_TRUST,
        AgentRole.DECISION,
    ],
    IntentType.DATA_INGESTION: [
        AgentRole.DATA,
    ],
    IntentType.KNOWLEDGE_QUERY: [
        AgentRole.KNOWLEDGE,
        AgentRole.EVIDENCE_TRUST,
        AgentRole.DECISION,
    ],
    IntentType.FULL_ASSESSMENT: [
        AgentRole.DATA,
        AgentRole.AGRONOMY,
        AgentRole.CROP_PROTECTION,
        AgentRole.CROP_INTELLIGENCE,
        AgentRole.KNOWLEDGE,
        AgentRole.PROCUREMENT,
        AgentRole.EVIDENCE_TRUST,
        AgentRole.DECISION,
    ],
    IntentType.WEATHER_ANALYSIS: [
        AgentRole.DATA,
        AgentRole.AGRONOMY,
        AgentRole.EVIDENCE_TRUST,
        AgentRole.DECISION,
    ],
}

# Agents that can execute in parallel (no inter-dependency)
PARALLEL_GROUPS: dict[int, list[AgentRole]] = {
    1: [AgentRole.AGRONOMY, AgentRole.CROP_PROTECTION, AgentRole.CROP_INTELLIGENCE,
        AgentRole.KNOWLEDGE, AgentRole.PROCUREMENT],
}


class OrchestratorAgent(BaseAgent):
    """
    CoCo Intelligence Orchestrator.
    Manages intent detection, execution planning, conditional routing, and output merging.
    """

    def __init__(self, config: AgentConfig | None = None):
        super().__init__(role=AgentRole.ORCHESTRATOR, config=config)

    async def execute(self, state: AgriPulseState) -> AgriPulseState:
        state.execution_status = ExecutionStatus.RUNNING

        # Step 1: Detect intent
        state.intent = self._detect_intent(state.user_query)
        logger.info(f"Detected intent: {state.intent}")

        # Step 2: Build execution plan
        state.execution_plan = self._build_plan(state.intent)
        logger.info(f"Execution plan: {[a.value for a in state.execution_plan]}")

        # Step 3: Extract entities
        state.detected_entities = self._extract_entities(state.user_query)

        return state

    async def validate(self, state: AgriPulseState) -> bool:
        return state.intent is not None and len(state.execution_plan) > 0

    def _detect_intent(self, query: str) -> IntentType:
        """Rule-based intent detection with keyword matching."""
        q = query.lower()

        intent_keywords: dict[IntentType, list[str]] = {
            IntentType.PEST_ALERT: ["pest", "insect", "disease", "fungus", "blight", "wilt", "rot", "infestation"],
            IntentType.YIELD_PREDICTION: ["yield", "predict", "forecast", "production", "harvest estimate"],
            IntentType.MARKET_ANALYSIS: ["market", "price", "msp", "mandi", "trade", "export"],
            IntentType.PROCUREMENT_PLAN: ["procurement", "purchase", "buy", "stock", "storage", "supply"],
            IntentType.DATA_INGESTION: ["ingest", "upload", "sync", "import", "load data", "etl"],
            IntentType.KNOWLEDGE_QUERY: ["research", "paper", "advisory", "icar", "kvk", "fao", "publication"],
            IntentType.WEATHER_ANALYSIS: ["weather", "rain", "rainfall", "temperature", "monsoon", "drought"],
            IntentType.CROP_ADVISORY: ["crop", "advisory", "recommend", "what should", "guidance", "sow"],
        }

        for intent, keywords in intent_keywords.items():
            if any(kw in q for kw in keywords):
                return intent

        return IntentType.FULL_ASSESSMENT

    def _build_plan(self, intent: IntentType) -> list[AgentRole]:
        return INTENT_ROUTING.get(intent, INTENT_ROUTING[IntentType.FULL_ASSESSMENT])

    def _extract_entities(self, query: str) -> dict[str, Any]:
        """Extract crop, region, season entities from query."""
        entities: dict[str, Any] = {}

        crops = ["rice", "wheat", "maize", "cotton", "sugarcane", "soybean",
                 "groundnut", "mustard", "potato", "tomato", "onion", "pulses",
                 "bajra", "jowar", "ragi", "turmeric", "chilli"]
        seasons = ["kharif", "rabi", "zaid", "summer", "winter", "monsoon"]
        states = ["maharashtra", "punjab", "haryana", "uttar pradesh", "karnataka",
                  "andhra pradesh", "tamil nadu", "madhya pradesh", "rajasthan",
                  "gujarat", "bihar", "west bengal", "telangana", "odisha"]

        q = query.lower()
        entities["crops"] = [c for c in crops if c in q]
        entities["seasons"] = [s for s in seasons if s in q]
        entities["regions"] = [s for s in states if s in q]

        return entities

    def get_parallel_groups(self, plan: list[AgentRole]) -> list[list[AgentRole]]:
        """Split plan into sequential + parallel execution groups."""
        groups: list[list[AgentRole]] = []

        # DATA always runs first (sequential)
        if AgentRole.DATA in plan:
            groups.append([AgentRole.DATA])
            plan = [a for a in plan if a != AgentRole.DATA]

        # Middle agents can run in parallel
        parallel = [a for a in plan if a in PARALLEL_GROUPS.get(1, [])]
        sequential_end = [a for a in plan if a not in parallel]

        if parallel:
            groups.append(parallel)

        # EVIDENCE_TRUST and DECISION always run last, in sequence
        for agent in [AgentRole.EVIDENCE_TRUST, AgentRole.DECISION]:
            if agent in sequential_end:
                groups.append([agent])
                sequential_end = [a for a in sequential_end if a != agent]

        return groups
