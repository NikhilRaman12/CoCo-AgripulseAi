"""
CoCo Procurement Intelligence Agent
MSP analysis, market forecasting, demand-supply, procurement planning.
"""

from __future__ import annotations

import logging
from typing import Any

from agripulse.agents.base import BaseAgent
from agripulse.state import AgriPulseState, AgentRole
from agripulse.mcp.external_tools import MarketMCP
from agripulse.config import AgentConfig

logger = logging.getLogger("agripulse.agent.procurement")


class ProcurementIntelligenceAgent(BaseAgent):
    """
    CoCo Procurement Intelligence Agent.
    Market prices, MSP, demand-supply analysis, procurement strategy.
    """

    def __init__(self, config: AgentConfig | None = None):
        super().__init__(role=AgentRole.PROCUREMENT, config=config)
        self.market_mcp = MarketMCP()

    async def execute(self, state: AgriPulseState) -> AgriPulseState:
        entities = state.detected_entities
        crops = entities.get("crops", ["rice"])
        regions = entities.get("regions", ["maharashtra"])

        results: dict[str, Any] = {}

        # Step 1: MSP analysis
        results["msp"] = await self._analyze_msp(crops)

        # Step 2: Market price intelligence
        results["market_prices"] = await self._market_intelligence(crops, regions)

        # Step 3: Demand-supply analysis
        results["demand_supply"] = self._demand_supply_analysis(crops, regions)

        # Step 4: Procurement planning
        results["procurement_plan"] = self._build_procurement_plan(crops, results)

        # Step 5: Storage recommendations
        results["storage"] = self._storage_recommendations(crops)

        # Step 6: Farmer profitability
        results["profitability"] = self._farmer_profitability(crops, results)

        state.set_agent_output(self.role, results)

        self._emit_message(
            state,
            target=AgentRole.ORCHESTRATOR,
            payload={
                "status": "procurement_complete",
                "crops_analyzed": crops,
                "strategy": results["procurement_plan"].get("strategy", "hold"),
            },
            confidence=0.78,
        )

        return state

    async def validate(self, state: AgriPulseState) -> bool:
        output = state.get_agent_output(self.role)
        return output is not None and "msp" in output

    async def _analyze_msp(self, crops: list[str]) -> dict[str, Any]:
        """Get MSP rates for all crops."""
        msp_data = {}
        for crop in crops:
            try:
                msp = await self.market_mcp.get_msp_rates(crop)
                msp_data[crop] = msp
            except Exception as e:
                logger.warning(f"MSP fetch failed for {crop}: {e}")
                msp_data[crop] = {"error": str(e)}
        return msp_data

    async def _market_intelligence(self, crops: list[str], regions: list[str]) -> dict[str, Any]:
        """Current mandi prices and trends."""
        prices = {}
        for crop in crops:
            for region in regions[:2]:
                try:
                    price = await self.market_mcp.get_mandi_prices(crop, region)
                    prices[f"{crop}_{region}"] = price
                except Exception as e:
                    logger.warning(f"Market price fetch failed: {e}")
        return prices

    def _demand_supply_analysis(self, crops: list[str], regions: list[str]) -> dict[str, Any]:
        """Analyze demand-supply dynamics."""
        analysis = {}
        for crop in crops:
            analysis[crop] = {
                "demand_trend": "increasing",
                "supply_outlook": "normal",
                "price_pressure": "upward",
                "export_demand": "moderate",
                "stock_position": "adequate",
            }
        return analysis

    def _build_procurement_plan(self, crops: list[str], all_data: dict[str, Any]) -> dict[str, Any]:
        """Build procurement strategy."""
        msp_data = all_data.get("msp", {})
        demand = all_data.get("demand_supply", {})

        plan = {
            "strategy": "buy",
            "timing": "current_week",
            "crops": {},
        }
        for crop in crops:
            msp = msp_data.get(crop, {}).get("msp_per_quintal", 0)
            plan["crops"][crop] = {
                "recommended_action": "procure_at_msp",
                "msp_rate": msp,
                "suggested_premium_pct": 5,
                "volume_recommendation": "standard",
                "risk": "low",
            }
        return plan

    def _storage_recommendations(self, crops: list[str]) -> dict[str, Any]:
        """Storage and warehousing recommendations."""
        storage_specs = {
            "rice": {"temp_c": "25-30", "humidity_pct": "12-14", "max_months": 12, "method": "silo/warehouse"},
            "wheat": {"temp_c": "20-25", "humidity_pct": "10-12", "max_months": 18, "method": "silo"},
            "maize": {"temp_c": "20-25", "humidity_pct": "12-14", "max_months": 8, "method": "airtight"},
        }
        return {crop: storage_specs.get(crop, {"method": "standard_warehouse"}) for crop in crops}

    def _farmer_profitability(self, crops: list[str], all_data: dict[str, Any]) -> dict[str, Any]:
        """Estimate farmer profitability."""
        profitability = {}
        for crop in crops:
            msp = all_data.get("msp", {}).get(crop, {}).get("msp_per_quintal", 0)
            cost_per_quintal = msp * 0.7  # Rough estimate
            profitability[crop] = {
                "msp_per_quintal": msp,
                "estimated_cost_per_quintal": cost_per_quintal,
                "margin_pct": 30,
                "breakeven_yield_tonnes_per_ha": 2.5,
            }
        return profitability

    def tests(self) -> dict[str, bool]:
        base = super().tests()
        base["market_mcp_init"] = self.market_mcp is not None
        return base
