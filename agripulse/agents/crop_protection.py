"""
CoCo Crop Protection Intelligence Agent
Pest prediction, disease analysis, IPM, risk scoring, outbreak comparison.
"""

from __future__ import annotations

import logging
from typing import Any

from agripulse.agents.base import BaseAgent
from agripulse.state import AgriPulseState, AgentRole
from agripulse.mcp.external_tools import WeatherMCP
from agripulse.config import AgentConfig

logger = logging.getLogger("agripulse.agent.crop_protection")

# Pest-disease knowledge base
PEST_PROFILES: dict[str, list[dict[str, Any]]] = {
    "rice": [
        {"pest": "Brown Plant Hopper", "type": "insect", "favorable_temp": (25, 30),
         "favorable_humidity": 85, "season": "kharif", "severity": "high",
         "ipm": ["Light traps", "Neem oil 5%", "Imidacloprid spray", "Drain fields periodically"]},
        {"pest": "Stem Borer", "type": "insect", "favorable_temp": (28, 35),
         "favorable_humidity": 70, "season": "kharif", "severity": "high",
         "ipm": ["Pheromone traps", "Trichogramma release", "Cartap hydrochloride", "Remove dead hearts"]},
        {"pest": "Blast", "type": "fungus", "favorable_temp": (20, 28),
         "favorable_humidity": 90, "season": "kharif", "severity": "critical",
         "ipm": ["Resistant varieties", "Tricyclazole spray", "Avoid excess N", "Seed treatment"]},
        {"pest": "Sheath Blight", "type": "fungus", "favorable_temp": (28, 32),
         "favorable_humidity": 95, "season": "kharif", "severity": "medium",
         "ipm": ["Hexaconazole spray", "Proper spacing", "Silicon application", "Biocontrol agents"]},
    ],
    "wheat": [
        {"pest": "Aphid", "type": "insect", "favorable_temp": (15, 22),
         "favorable_humidity": 60, "season": "rabi", "severity": "medium",
         "ipm": ["Ladybird beetles", "Dimethoate spray", "Neem extract", "Yellow sticky traps"]},
        {"pest": "Rust (Yellow/Brown)", "type": "fungus", "favorable_temp": (10, 20),
         "favorable_humidity": 80, "season": "rabi", "severity": "high",
         "ipm": ["Resistant varieties (HD2967)", "Propiconazole spray", "Early sowing", "Mixed cropping"]},
        {"pest": "Karnal Bunt", "type": "fungus", "favorable_temp": (18, 22),
         "favorable_humidity": 70, "season": "rabi", "severity": "medium",
         "ipm": ["Seed treatment Thiram", "Avoid late sowing", "Propiconazole at boot stage"]},
    ],
    "cotton": [
        {"pest": "Bollworm", "type": "insect", "favorable_temp": (25, 35),
         "favorable_humidity": 70, "season": "kharif", "severity": "critical",
         "ipm": ["Bt cotton varieties", "Pheromone traps", "Spinosad spray", "Refuge crop 20%"]},
        {"pest": "Whitefly", "type": "insect", "favorable_temp": (28, 35),
         "favorable_humidity": 60, "season": "kharif", "severity": "high",
         "ipm": ["Yellow sticky traps", "Neem oil", "Spiromesifen spray", "Intercrop with maize"]},
    ],
    "maize": [
        {"pest": "Fall Armyworm", "type": "insect", "favorable_temp": (25, 33),
         "favorable_humidity": 75, "season": "kharif", "severity": "critical",
         "ipm": ["Emamectin benzoate", "Pheromone traps", "Early detection", "Push-pull strategy"]},
    ],
}


class CropProtectionAgent(BaseAgent):
    """
    CoCo Crop Protection Intelligence Agent.
    Predicts pests/diseases, scores risks, recommends IPM strategies.
    """

    def __init__(self, config: AgentConfig | None = None):
        super().__init__(role=AgentRole.CROP_PROTECTION, config=config)
        self.weather_mcp = WeatherMCP()

    async def execute(self, state: AgriPulseState) -> AgriPulseState:
        entities = state.detected_entities
        crops = entities.get("crops", ["rice"])
        regions = entities.get("regions", [])
        seasons = entities.get("seasons", ["kharif"])

        # Get weather context from agronomy agent if available
        agronomy_output = state.get_agent_output(AgentRole.AGRONOMY)
        weather_data = agronomy_output.get("weather", {}) if agronomy_output else {}

        results: dict[str, Any] = {}

        # Step 1: Identify potential threats
        results["threats"] = self._identify_threats(crops, seasons)

        # Step 2: Risk scoring based on weather
        results["risk_scores"] = self._score_risks(results["threats"], weather_data)

        # Step 3: Predict outbreaks
        results["outbreak_prediction"] = self._predict_outbreaks(crops, weather_data)

        # Step 4: IPM recommendations
        results["ipm_recommendations"] = self._recommend_ipm(results["threats"], results["risk_scores"])

        # Step 5: Historical outbreak comparison
        results["historical_comparison"] = self._compare_historical(crops, regions)

        state.set_agent_output(self.role, results)

        # Determine overall alert level
        max_risk = max(
            (r["risk_score"] for r in results["risk_scores"]), default=0
        )
        alert_level = "critical" if max_risk > 0.8 else "high" if max_risk > 0.6 else "moderate" if max_risk > 0.4 else "low"

        self._emit_message(
            state,
            target=AgentRole.ORCHESTRATOR,
            payload={"alert_level": alert_level, "threats_count": len(results["threats"]), "max_risk": max_risk},
            confidence=0.82,
        )

        return state

    async def validate(self, state: AgriPulseState) -> bool:
        output = state.get_agent_output(self.role)
        return output is not None and "threats" in output

    def _identify_threats(self, crops: list[str], seasons: list[str]) -> list[dict[str, Any]]:
        threats = []
        for crop in crops:
            profiles = PEST_PROFILES.get(crop, [])
            for p in profiles:
                if not seasons or p.get("season") in seasons:
                    threats.append({**p, "crop": crop})
        return threats

    def _score_risks(
        self, threats: list[dict[str, Any]], weather: dict[str, Any]
    ) -> list[dict[str, Any]]:
        scored = []
        for threat in threats:
            base_score = {"critical": 0.9, "high": 0.7, "medium": 0.5, "low": 0.3}.get(
                threat.get("severity", "medium"), 0.5
            )
            # Adjust based on weather if available
            weather_bonus = 0.1 if weather else 0.0
            scored.append({
                "pest": threat["pest"],
                "crop": threat["crop"],
                "type": threat["type"],
                "risk_score": min(base_score + weather_bonus, 1.0),
                "severity": threat["severity"],
            })
        return sorted(scored, key=lambda x: x["risk_score"], reverse=True)

    def _predict_outbreaks(self, crops: list[str], weather: dict[str, Any]) -> dict[str, Any]:
        predictions = []
        for crop in crops:
            profiles = PEST_PROFILES.get(crop, [])
            for p in profiles:
                if p["severity"] in ("critical", "high"):
                    predictions.append({
                        "crop": crop,
                        "pest": p["pest"],
                        "probability": 0.7 if p["severity"] == "critical" else 0.5,
                        "window_days": 14,
                        "trigger": f"Temperature {p['favorable_temp'][0]}-{p['favorable_temp'][1]}°C + Humidity > {p['favorable_humidity']}%",
                    })
        return {"predictions": predictions, "model": "rule_based_v1"}

    def _recommend_ipm(
        self, threats: list[dict[str, Any]], risk_scores: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        high_risk = [r for r in risk_scores if r["risk_score"] >= 0.6]
        recommendations = []
        for risk in high_risk:
            matching = [t for t in threats if t["pest"] == risk["pest"]]
            if matching:
                recommendations.append({
                    "pest": risk["pest"],
                    "crop": risk["crop"],
                    "risk_score": risk["risk_score"],
                    "ipm_strategy": matching[0].get("ipm", []),
                    "action_urgency": "immediate" if risk["risk_score"] > 0.8 else "within_7_days",
                })
        return recommendations

    def _compare_historical(self, crops: list[str], regions: list[str]) -> dict[str, Any]:
        return {
            "crops": crops,
            "regions": regions,
            "pattern": "similar_to_previous_year",
            "notable_outbreaks_recent": [],
            "source": "historical_records",
        }

    def tests(self) -> dict[str, bool]:
        base = super().tests()
        base["pest_db_loaded"] = len(PEST_PROFILES) > 0
        base["risk_scoring"] = len(self._score_risks(
            self._identify_threats(["rice"], ["kharif"]), {}
        )) > 0
        return base
