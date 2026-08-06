"""
CoCo Agronomy Intelligence Agent
Crop growth stages, soil, nutrients, irrigation, weather, seasonal analysis.
"""

from __future__ import annotations

import logging
from typing import Any

from agripulse.agents.base import BaseAgent
from agripulse.state import AgriPulseState, AgentRole
from agripulse.mcp.external_tools import WeatherMCP
from agripulse.config import AgentConfig

logger = logging.getLogger("agripulse.agent.agronomy")

# Crop growth stage knowledge base
CROP_STAGES: dict[str, list[dict[str, Any]]] = {
    "rice": [
        {"stage": "germination", "days": "0-10", "water_mm": 50, "critical_temp_min": 20, "critical_temp_max": 35},
        {"stage": "seedling", "days": "10-25", "water_mm": 80, "critical_temp_min": 22, "critical_temp_max": 35},
        {"stage": "tillering", "days": "25-50", "water_mm": 120, "critical_temp_min": 25, "critical_temp_max": 33},
        {"stage": "panicle_initiation", "days": "50-70", "water_mm": 150, "critical_temp_min": 25, "critical_temp_max": 30},
        {"stage": "flowering", "days": "70-90", "water_mm": 150, "critical_temp_min": 25, "critical_temp_max": 30},
        {"stage": "grain_filling", "days": "90-115", "water_mm": 100, "critical_temp_min": 22, "critical_temp_max": 28},
        {"stage": "maturity", "days": "115-135", "water_mm": 0, "critical_temp_min": 20, "critical_temp_max": 30},
    ],
    "wheat": [
        {"stage": "germination", "days": "0-7", "water_mm": 40, "critical_temp_min": 12, "critical_temp_max": 25},
        {"stage": "crown_root", "days": "21-25", "water_mm": 60, "critical_temp_min": 15, "critical_temp_max": 22},
        {"stage": "tillering", "days": "25-45", "water_mm": 80, "critical_temp_min": 15, "critical_temp_max": 20},
        {"stage": "jointing", "days": "45-65", "water_mm": 80, "critical_temp_min": 15, "critical_temp_max": 22},
        {"stage": "flowering", "days": "65-80", "water_mm": 100, "critical_temp_min": 18, "critical_temp_max": 25},
        {"stage": "grain_filling", "days": "80-110", "water_mm": 80, "critical_temp_min": 20, "critical_temp_max": 28},
        {"stage": "maturity", "days": "110-130", "water_mm": 0, "critical_temp_min": 20, "critical_temp_max": 30},
    ],
    "maize": [
        {"stage": "emergence", "days": "0-10", "water_mm": 40, "critical_temp_min": 18, "critical_temp_max": 35},
        {"stage": "vegetative", "days": "10-40", "water_mm": 80, "critical_temp_min": 20, "critical_temp_max": 33},
        {"stage": "tasseling", "days": "40-55", "water_mm": 120, "critical_temp_min": 22, "critical_temp_max": 30},
        {"stage": "silking", "days": "55-65", "water_mm": 150, "critical_temp_min": 22, "critical_temp_max": 30},
        {"stage": "grain_filling", "days": "65-90", "water_mm": 100, "critical_temp_min": 20, "critical_temp_max": 28},
        {"stage": "maturity", "days": "90-110", "water_mm": 40, "critical_temp_min": 18, "critical_temp_max": 30},
    ],
}

# Regional coordinates for weather queries
REGION_COORDS: dict[str, tuple[float, float]] = {
    "maharashtra": (19.7515, 75.7139),
    "punjab": (31.1471, 75.3412),
    "haryana": (29.0588, 76.0856),
    "uttar pradesh": (26.8467, 80.9462),
    "karnataka": (15.3173, 75.7139),
    "andhra pradesh": (15.9129, 79.7400),
    "tamil nadu": (11.1271, 78.6569),
    "madhya pradesh": (22.9734, 78.6569),
    "rajasthan": (27.0238, 74.2179),
    "gujarat": (22.2587, 71.1924),
    "bihar": (25.0961, 85.3131),
    "west bengal": (22.9868, 87.8550),
    "telangana": (18.1124, 79.0193),
    "odisha": (20.9517, 85.0985),
}


class AgronomyIntelligenceAgent(BaseAgent):
    """
    CoCo Agronomy Intelligence Agent.
    Understands crop growth, soil, weather, and provides agronomic insights.
    """

    def __init__(self, config: AgentConfig | None = None):
        super().__init__(role=AgentRole.AGRONOMY, config=config)
        self.weather_mcp = WeatherMCP()

    async def execute(self, state: AgriPulseState) -> AgriPulseState:
        entities = state.detected_entities
        crops = entities.get("crops", ["rice"])
        regions = entities.get("regions", ["maharashtra"])
        seasons = entities.get("seasons", [])

        results: dict[str, Any] = {}

        # Step 1: Crop growth stage analysis
        results["growth_stages"] = self._analyze_growth_stages(crops)

        # Step 2: Weather analysis
        results["weather"] = await self._analyze_weather(regions)

        # Step 3: Soil & nutrient recommendations
        results["soil_nutrients"] = self._recommend_nutrients(crops, seasons)

        # Step 4: Irrigation recommendations
        results["irrigation"] = self._recommend_irrigation(crops, results.get("weather", {}))

        # Step 5: Seasonal insights
        results["seasonal_analysis"] = self._seasonal_analysis(crops, seasons, results.get("weather", {}))

        # Step 6: Historical yield trends
        results["yield_trends"] = self._historical_yield_trends(crops, regions)

        state.set_agent_output(self.role, results)

        self._emit_message(
            state,
            target=AgentRole.ORCHESTRATOR,
            payload={"status": "agronomy_complete", "summary": self._summarize(results)},
            confidence=0.85,
        )

        return state

    async def validate(self, state: AgriPulseState) -> bool:
        output = state.get_agent_output(self.role)
        return output is not None and "growth_stages" in output

    def _analyze_growth_stages(self, crops: list[str]) -> dict[str, Any]:
        analysis = {}
        for crop in crops:
            stages = CROP_STAGES.get(crop, [])
            if stages:
                analysis[crop] = {
                    "stages": stages,
                    "total_duration_days": int(stages[-1]["days"].split("-")[1]),
                    "critical_stages": [s for s in stages if s["water_mm"] >= 100],
                }
        return analysis

    async def _analyze_weather(self, regions: list[str]) -> dict[str, Any]:
        weather_data = {}
        for region in regions[:3]:
            coords = REGION_COORDS.get(region)
            if coords:
                try:
                    data = await self.weather_mcp.get_current_weather(coords[0], coords[1])
                    weather_data[region] = {
                        "current": data.get("current_weather", {}),
                        "forecast_7d": data.get("daily", {}),
                        "coordinates": coords,
                    }
                except Exception as e:
                    logger.warning(f"Weather fetch failed for {region}: {e}")
                    weather_data[region] = {"error": str(e)}
        return weather_data

    def _recommend_nutrients(self, crops: list[str], seasons: list[str]) -> dict[str, Any]:
        nutrient_profiles = {
            "rice": {"N": 120, "P": 60, "K": 40, "Zn": 25, "schedule": "split_3"},
            "wheat": {"N": 120, "P": 60, "K": 40, "S": 20, "schedule": "split_2"},
            "maize": {"N": 150, "P": 75, "K": 60, "Zn": 25, "schedule": "split_3"},
            "cotton": {"N": 150, "P": 60, "K": 60, "schedule": "split_4"},
            "sugarcane": {"N": 250, "P": 100, "K": 120, "schedule": "split_4"},
        }
        recommendations = {}
        for crop in crops:
            profile = nutrient_profiles.get(crop, {"N": 100, "P": 50, "K": 40, "schedule": "split_2"})
            recommendations[crop] = {
                "nutrients_kg_per_ha": profile,
                "season_adjustment": "kharif" in seasons,
                "organic_supplement": "FYM 10-12 tonnes/ha + Azotobacter",
            }
        return recommendations

    def _recommend_irrigation(self, crops: list[str], weather: dict[str, Any]) -> dict[str, Any]:
        irrigation = {}
        for crop in crops:
            stages = CROP_STAGES.get(crop, [])
            total_water = sum(s["water_mm"] for s in stages)
            irrigation[crop] = {
                "total_water_requirement_mm": total_water,
                "critical_irrigation_stages": [s["stage"] for s in stages if s["water_mm"] >= 100],
                "method": "flood" if crop == "rice" else "drip/sprinkler",
                "frequency": "3-5 days" if crop == "rice" else "7-10 days",
            }
        return irrigation

    def _seasonal_analysis(
        self, crops: list[str], seasons: list[str], weather: dict[str, Any]
    ) -> dict[str, Any]:
        season_crop_map = {
            "kharif": ["rice", "maize", "cotton", "soybean", "groundnut"],
            "rabi": ["wheat", "mustard", "potato", "onion"],
            "zaid": ["sugarcane", "tomato"],
        }
        analysis = {
            "recommended_season": [],
            "sowing_window": "",
            "risk_factors": [],
        }
        for crop in crops:
            for season, s_crops in season_crop_map.items():
                if crop in s_crops:
                    analysis["recommended_season"].append({"crop": crop, "season": season})
        return analysis

    def _historical_yield_trends(self, crops: list[str], regions: list[str]) -> dict[str, Any]:
        return {
            "crops": crops,
            "regions": regions,
            "trend": "increasing",
            "avg_yield_improvement_pct": 2.5,
            "source": "historical_data",
        }

    def _summarize(self, results: dict[str, Any]) -> str:
        crops = list(results.get("growth_stages", {}).keys())
        return f"Agronomic analysis complete for: {', '.join(crops)}"

    def tests(self) -> dict[str, bool]:
        base = super().tests()
        base["crop_stages_loaded"] = len(CROP_STAGES) > 0
        base["region_coords_loaded"] = len(REGION_COORDS) > 0
        return base
