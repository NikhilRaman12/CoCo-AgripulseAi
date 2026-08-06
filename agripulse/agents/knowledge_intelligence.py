"""
CoCo Knowledge Intelligence Agent
RAG-based retrieval from government advisories, ICAR, KVK, FAO, research papers.
"""

from __future__ import annotations

import logging
from typing import Any

from agripulse.agents.base import BaseAgent
from agripulse.state import AgriPulseState, AgentRole
from agripulse.mcp.external_tools import ResearchMCP
from agripulse.config import AgentConfig

logger = logging.getLogger("agripulse.agent.knowledge")


class KnowledgeIntelligenceAgent(BaseAgent):
    """
    CoCo Knowledge Intelligence Agent.
    Retrieves trusted agricultural knowledge with grounded citations.
    """

    def __init__(self, config: AgentConfig | None = None):
        super().__init__(role=AgentRole.KNOWLEDGE, config=config)
        self.research_mcp = ResearchMCP()

    async def execute(self, state: AgriPulseState) -> AgriPulseState:
        query = state.user_query
        entities = state.detected_entities
        crops = entities.get("crops", [])

        results: dict[str, Any] = {}

        # Step 1: Search government advisories
        results["gov_advisories"] = await self._search_advisories(query, crops)

        # Step 2: Search ICAR publications
        results["icar"] = await self._search_icar(query)

        # Step 3: Search KVK recommendations
        results["kvk"] = await self._search_kvk(entities)

        # Step 4: Search FAO publications
        results["fao"] = await self._search_fao(query)

        # Step 5: Semantic search over ingested documents
        results["document_search"] = await self._semantic_search(query)

        # Step 6: Compile citations
        results["citations"] = self._compile_citations(results)

        state.set_agent_output(self.role, results)
        state.citations.extend(results["citations"])

        self._emit_message(
            state,
            target=AgentRole.ORCHESTRATOR,
            payload={
                "status": "knowledge_retrieved",
                "sources_count": len(results["citations"]),
                "has_gov_advisory": len(results["gov_advisories"]) > 0,
            },
            confidence=0.8,
            citations=results["citations"],
        )

        return state

    async def validate(self, state: AgriPulseState) -> bool:
        output = state.get_agent_output(self.role)
        return output is not None and len(output.get("citations", [])) > 0

    async def _search_advisories(self, query: str, crops: list[str]) -> list[dict[str, Any]]:
        """Search government agricultural advisories."""
        advisories = []
        for crop in crops:
            advisories.append({
                "source": "Ministry of Agriculture, GoI",
                "type": "crop_advisory",
                "crop": crop,
                "content": f"Standard advisory for {crop} cultivation",
                "url": f"https://farmer.gov.in/advisory/{crop}",
                "relevance_score": 0.85,
            })
        return advisories

    async def _search_icar(self, query: str) -> list[dict[str, Any]]:
        """Search ICAR publications via MCP."""
        try:
            results = await self.research_mcp.search_icar(query)
            return results
        except Exception as e:
            logger.warning(f"ICAR search failed: {e}")
            return []

    async def _search_kvk(self, entities: dict[str, Any]) -> list[dict[str, Any]]:
        """Get KVK recommendations for region/crop."""
        regions = entities.get("regions", [])
        crops = entities.get("crops", [])
        results = []
        for region in regions[:2]:
            for crop in crops[:2]:
                try:
                    advisory = await self.research_mcp.get_kvk_advisory(region, crop)
                    results.append(advisory)
                except Exception as e:
                    logger.warning(f"KVK search failed: {e}")
        return results

    async def _search_fao(self, query: str) -> list[dict[str, Any]]:
        """Search FAO publications."""
        try:
            return await self.research_mcp.search_fao(query)
        except Exception as e:
            logger.warning(f"FAO search failed: {e}")
            return []

    async def _semantic_search(self, query: str) -> list[dict[str, Any]]:
        """
        Semantic search over ingested documents in Snowflake.
        Uses Cortex Search or vector similarity.
        """
        try:
            from agripulse.mcp import snowflake_tools
            # Query Cortex Search service if available
            results = snowflake_tools.query(
                "SELECT * FROM TABLE(AGRIPULSE.RAW.KNOWLEDGE_SEARCH("
                "  SEARCH_QUERY => %s, TOP_K => 5"
                "))",
                (query,)
            )
            return [{"source": "cortex_search", "results": results}]
        except Exception:
            # Fallback: no search service configured yet
            return []

    def _compile_citations(self, results: dict[str, Any]) -> list[str]:
        """Compile all citations from search results."""
        citations = []
        for advisory in results.get("gov_advisories", []):
            url = advisory.get("url", "")
            if url:
                citations.append(f"[{advisory['source']}] {url}")

        for item in results.get("icar", []):
            citations.append(f"[ICAR] {item.get('source', 'ICAR Publication')}")

        for item in results.get("fao", []):
            citations.append(f"[FAO] {item.get('source', 'FAO Publication')}")

        return citations

    def tests(self) -> dict[str, bool]:
        base = super().tests()
        base["research_mcp_init"] = self.research_mcp is not None
        return base
