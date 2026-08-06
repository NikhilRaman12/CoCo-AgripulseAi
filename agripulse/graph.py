"""
AgriPulse LangGraph Execution Graph
StateGraph with conditional edges, parallel execution, and full observability.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langgraph.graph import StateGraph, END

from agripulse.state import AgriPulseState, AgentRole, ExecutionStatus
from agripulse.config import PlatformConfig, AgentConfig
from agripulse.agents.orchestrator import OrchestratorAgent
from agripulse.agents.data_intelligence import DataIntelligenceAgent
from agripulse.agents.agronomy_intelligence import AgronomyIntelligenceAgent
from agripulse.agents.crop_protection import CropProtectionAgent
from agripulse.agents.crop_intelligence import CropIntelligenceAgent
from agripulse.agents.knowledge_intelligence import KnowledgeIntelligenceAgent
from agripulse.agents.procurement_intelligence import ProcurementIntelligenceAgent
from agripulse.agents.evidence_trust import EvidenceTrustAgent
from agripulse.agents.decision_intelligence import DecisionIntelligenceAgent

logger = logging.getLogger("agripulse.graph")


class AgriPulseGraph:
    """
    LangGraph StateGraph implementation for AgriPulse.
    Conditional routing, parallel execution, retry policies.
    """

    def __init__(self, config: PlatformConfig | None = None):
        self.config = config or PlatformConfig()
        agent_config = self.config.agent

        # Initialize all agents
        self.agents = {
            AgentRole.ORCHESTRATOR: OrchestratorAgent(agent_config),
            AgentRole.DATA: DataIntelligenceAgent(agent_config),
            AgentRole.AGRONOMY: AgronomyIntelligenceAgent(agent_config),
            AgentRole.CROP_PROTECTION: CropProtectionAgent(agent_config),
            AgentRole.CROP_INTELLIGENCE: CropIntelligenceAgent(agent_config),
            AgentRole.KNOWLEDGE: KnowledgeIntelligenceAgent(agent_config),
            AgentRole.PROCUREMENT: ProcurementIntelligenceAgent(agent_config),
            AgentRole.EVIDENCE_TRUST: EvidenceTrustAgent(agent_config),
            AgentRole.DECISION: DecisionIntelligenceAgent(agent_config),
        }

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph with conditional edges."""

        # Define state schema for LangGraph
        graph = StateGraph(AgriPulseState)

        # Add nodes
        graph.add_node("intent_detection", self._node_intent_detection)
        graph.add_node("data_intelligence", self._node_data)
        graph.add_node("parallel_analysis", self._node_parallel_analysis)
        graph.add_node("evidence_trust", self._node_evidence_trust)
        graph.add_node("decision", self._node_decision)

        # Set entry point
        graph.set_entry_point("intent_detection")

        # Add conditional edges
        graph.add_conditional_edges(
            "intent_detection",
            self._route_after_intent,
            {
                "data_first": "data_intelligence",
                "skip_data": "parallel_analysis",
            },
        )

        graph.add_conditional_edges(
            "data_intelligence",
            self._route_after_data,
            {
                "parallel": "parallel_analysis",
                "done": "evidence_trust",
            },
        )

        graph.add_edge("parallel_analysis", "evidence_trust")
        graph.add_edge("evidence_trust", "decision")
        graph.add_edge("decision", END)

        return graph

    # --- Node implementations ---

    async def _node_intent_detection(self, state: AgriPulseState) -> AgriPulseState:
        """Orchestrator: detect intent and build execution plan."""
        orchestrator = self.agents[AgentRole.ORCHESTRATOR]
        return await orchestrator.run(state)

    async def _node_data(self, state: AgriPulseState) -> AgriPulseState:
        """Data Intelligence Agent execution."""
        agent = self.agents[AgentRole.DATA]
        return await agent.run(state)

    async def _node_parallel_analysis(self, state: AgriPulseState) -> AgriPulseState:
        """Execute analysis agents in parallel."""
        parallel_agents = [
            role for role in state.execution_plan
            if role in (
                AgentRole.AGRONOMY,
                AgentRole.CROP_PROTECTION,
                AgentRole.CROP_INTELLIGENCE,
                AgentRole.KNOWLEDGE,
                AgentRole.PROCUREMENT,
            )
        ]

        if not parallel_agents:
            return state

        logger.info(f"Executing in parallel: {[a.value for a in parallel_agents]}")

        # Run all analysis agents concurrently
        tasks = [self.agents[role].run(state) for role in parallel_agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results back into state
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent {parallel_agents[i].value} failed: {result}")
            elif isinstance(result, AgriPulseState):
                # Merge agent output from result into current state
                agent_role = parallel_agents[i]
                output = result.get_agent_output(agent_role)
                if output:
                    state.set_agent_output(agent_role, output)
                # Merge messages and trace
                state.messages.extend(
                    m for m in result.messages if m.source_agent == agent_role
                )
                state.trace.extend(
                    t for t in result.trace if t.agent == agent_role
                )

        return state

    async def _node_evidence_trust(self, state: AgriPulseState) -> AgriPulseState:
        """Evidence & Trust validation."""
        if AgentRole.EVIDENCE_TRUST not in state.execution_plan:
            return state
        agent = self.agents[AgentRole.EVIDENCE_TRUST]
        return await agent.run(state)

    async def _node_decision(self, state: AgriPulseState) -> AgriPulseState:
        """Decision Intelligence — final output."""
        if AgentRole.DECISION not in state.execution_plan:
            state.execution_status = ExecutionStatus.SUCCESS
            return state
        agent = self.agents[AgentRole.DECISION]
        return await agent.run(state)

    # --- Conditional routing functions ---

    def _route_after_intent(self, state: AgriPulseState) -> str:
        """Route after intent detection."""
        if AgentRole.DATA in state.execution_plan:
            return "data_first"
        return "skip_data"

    def _route_after_data(self, state: AgriPulseState) -> str:
        """Route after data agent — go to parallel or straight to decision."""
        remaining = [
            r for r in state.execution_plan
            if r not in (AgentRole.DATA, AgentRole.ORCHESTRATOR, AgentRole.EVIDENCE_TRUST, AgentRole.DECISION)
        ]
        if remaining:
            return "parallel"
        return "done"

    # --- Public API ---

    async def invoke(self, query: str) -> AgriPulseState:
        """Execute the full graph for a user query."""
        state = AgriPulseState(user_query=query)
        logger.info(f"Starting graph execution for: {query[:80]}")

        compiled = self.graph.compile()
        final_state = await compiled.ainvoke(state)

        logger.info(f"Graph execution complete. Status: {final_state.execution_status}")
        return final_state

    def health_check(self) -> dict[str, Any]:
        """System-wide health check."""
        return {
            "platform": "AgriPulse Enterprise Intelligence",
            "status": "healthy",
            "agents": {role.value: agent.health() for role, agent in self.agents.items()},
            "graph_nodes": ["intent_detection", "data_intelligence", "parallel_analysis", "evidence_trust", "decision"],
        }

    def run_tests(self) -> dict[str, dict[str, bool]]:
        """Run all agent self-tests."""
        return {role.value: agent.tests() for role, agent in self.agents.items()}
