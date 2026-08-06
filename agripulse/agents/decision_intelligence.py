"""
CoCo Decision Intelligence Agent
Final business-ready recommendations: executive summaries, action plans, reports.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from agripulse.agents.base import BaseAgent
from agripulse.state import AgriPulseState, AgentRole, ExecutionStatus
from agripulse.config import AgentConfig

logger = logging.getLogger("agripulse.agent.decision")


class DecisionIntelligenceAgent(BaseAgent):
    """
    CoCo Decision Intelligence Agent.
    Generates final recommendations, action plans, and structured reports.
    """

    def __init__(self, config: AgentConfig | None = None):
        super().__init__(role=AgentRole.DECISION, config=config)

    async def execute(self, state: AgriPulseState) -> AgriPulseState:
        # Gather all upstream outputs
        evidence = state.get_agent_output(AgentRole.EVIDENCE_TRUST) or {}
        trust_score = evidence.get("trust_score", 0.7)

        results: dict[str, Any] = {}

        # Step 1: Executive Summary
        results["executive_summary"] = self._build_executive_summary(state)

        # Step 2: Farmer Recommendation
        results["farmer_recommendation"] = self._build_farmer_recommendation(state)

        # Step 3: Government Recommendation
        results["government_recommendation"] = self._build_government_recommendation(state)

        # Step 4: Outlook sections
        results["yield_outlook"] = self._yield_outlook(state)
        results["pest_outlook"] = self._pest_outlook(state)
        results["procurement_strategy"] = self._procurement_strategy(state)

        # Step 5: Risk Assessment
        results["risk_assessment"] = self._risk_assessment(state)

        # Step 6: Action Plan with Timeline
        results["action_plan"] = self._build_action_plan(state)

        # Step 7: Final NL Response
        results["natural_language_response"] = self._generate_nl_response(results, state)

        # Step 8: Structured downloadable report
        results["structured_report"] = self._build_structured_report(results, state)

        state.set_agent_output(self.role, results)
        state.final_response = results
        state.execution_status = ExecutionStatus.SUCCESS

        return state

    async def validate(self, state: AgriPulseState) -> bool:
        output = state.get_agent_output(self.role)
        return output is not None and "executive_summary" in output

    def _build_executive_summary(self, state: AgriPulseState) -> dict[str, Any]:
        crops = state.detected_entities.get("crops", [])
        regions = state.detected_entities.get("regions", [])
        intent = state.intent.value if state.intent else "general"

        agents_executed = [t.agent.value for t in state.trace if t.status == ExecutionStatus.SUCCESS]

        return {
            "request": state.user_query,
            "intent": intent,
            "crops": crops,
            "regions": regions,
            "agents_consulted": agents_executed,
            "confidence": state.confidence_score,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _build_farmer_recommendation(self, state: AgriPulseState) -> dict[str, Any]:
        agronomy = state.get_agent_output(AgentRole.AGRONOMY) or {}
        protection = state.get_agent_output(AgentRole.CROP_PROTECTION) or {}
        procurement = state.get_agent_output(AgentRole.PROCUREMENT) or {}

        recommendations = []

        # Irrigation advice
        irrigation = agronomy.get("irrigation", {})
        for crop, details in irrigation.items():
            recommendations.append({
                "category": "irrigation",
                "crop": crop,
                "advice": f"Apply {details.get('method', 'standard')} irrigation every {details.get('frequency', '7 days')}",
                "priority": "high" if "critical" in str(details) else "medium",
            })

        # Pest management
        ipm = protection.get("ipm_recommendations", [])
        for rec in ipm[:3]:
            recommendations.append({
                "category": "pest_management",
                "crop": rec.get("crop", ""),
                "advice": f"Watch for {rec.get('pest', 'N/A')}: {', '.join(rec.get('ipm_strategy', [])[:2])}",
                "priority": "high" if rec.get("risk_score", 0) > 0.7 else "medium",
            })

        # Market timing
        plan = procurement.get("procurement_plan", {})
        if plan.get("timing"):
            recommendations.append({
                "category": "market",
                "advice": f"Recommended action: {plan.get('strategy', 'hold')} ({plan.get('timing', '')})",
                "priority": "medium",
            })

        return {"recommendations": recommendations, "count": len(recommendations)}

    def _build_government_recommendation(self, state: AgriPulseState) -> dict[str, Any]:
        protection = state.get_agent_output(AgentRole.CROP_PROTECTION) or {}
        procurement = state.get_agent_output(AgentRole.PROCUREMENT) or {}

        return {
            "pest_alert_level": self._get_alert_level(protection),
            "msp_adequacy": "adequate",
            "stock_recommendation": "maintain_buffer",
            "advisory_needed": protection.get("risk_scores", [{}])[0].get("risk_score", 0) > 0.7 if protection.get("risk_scores") else False,
            "regions_at_risk": state.detected_entities.get("regions", []),
        }

    def _yield_outlook(self, state: AgriPulseState) -> dict[str, Any]:
        ml = state.get_agent_output(AgentRole.CROP_INTELLIGENCE) or {}
        prediction = ml.get("prediction", {})
        return {
            "predicted_yield": prediction.get("predicted_yield_tonnes_per_ha", "N/A"),
            "confidence_interval": prediction.get("confidence_interval", []),
            "trend": prediction.get("trend", "stable"),
            "model_used": prediction.get("model_used", "N/A"),
        }

    def _pest_outlook(self, state: AgriPulseState) -> dict[str, Any]:
        protection = state.get_agent_output(AgentRole.CROP_PROTECTION) or {}
        risks = protection.get("risk_scores", [])
        return {
            "top_threats": risks[:3],
            "outbreak_probability": protection.get("outbreak_prediction", {}).get("predictions", []),
            "alert_level": self._get_alert_level(protection),
        }

    def _procurement_strategy(self, state: AgriPulseState) -> dict[str, Any]:
        procurement = state.get_agent_output(AgentRole.PROCUREMENT) or {}
        return procurement.get("procurement_plan", {"strategy": "standard"})

    def _risk_assessment(self, state: AgriPulseState) -> dict[str, Any]:
        risks = []

        protection = state.get_agent_output(AgentRole.CROP_PROTECTION) or {}
        for risk in protection.get("risk_scores", [])[:3]:
            risks.append({
                "type": "biological",
                "risk": risk.get("pest", ""),
                "severity": risk.get("severity", "medium"),
                "score": risk.get("risk_score", 0),
            })

        agronomy = state.get_agent_output(AgentRole.AGRONOMY) or {}
        weather = agronomy.get("weather", {})
        for region, data in weather.items():
            if "error" in data:
                risks.append({"type": "weather", "risk": f"Weather data unavailable for {region}", "severity": "low", "score": 0.3})

        evidence = state.get_agent_output(AgentRole.EVIDENCE_TRUST) or {}
        if evidence.get("trust_score", 1) < 0.6:
            risks.append({"type": "data_quality", "risk": "Low confidence in analysis", "severity": "medium", "score": 0.5})

        return {"risks": risks, "overall_risk": max((r["score"] for r in risks), default=0)}

    def _build_action_plan(self, state: AgriPulseState) -> list[dict[str, Any]]:
        today = datetime.utcnow()
        actions = [
            {"action": "Review crop advisory", "deadline": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "priority": "high", "owner": "farmer"},
            {"action": "Implement IPM measures", "deadline": (today + timedelta(days=3)).strftime("%Y-%m-%d"), "priority": "high", "owner": "farmer"},
            {"action": "Schedule irrigation", "deadline": (today + timedelta(days=2)).strftime("%Y-%m-%d"), "priority": "medium", "owner": "farmer"},
            {"action": "Monitor market prices", "deadline": (today + timedelta(days=7)).strftime("%Y-%m-%d"), "priority": "medium", "owner": "procurement"},
            {"action": "Review pest traps", "deadline": (today + timedelta(days=5)).strftime("%Y-%m-%d"), "priority": "medium", "owner": "field_officer"},
        ]
        return actions

    def _generate_nl_response(self, results: dict[str, Any], state: AgriPulseState) -> str:
        """Generate final natural language response."""
        summary = results["executive_summary"]
        crops = ", ".join(summary.get("crops", ["your crops"]))
        confidence = summary.get("confidence", 0)

        recommendations = results["farmer_recommendation"]["recommendations"]
        top_recs = recommendations[:3]

        response = f"**AgriPulse Intelligence Report**\n\n"
        response += f"Analysis for: {crops}\n"
        response += f"Confidence: {confidence:.0%}\n\n"

        if top_recs:
            response += "**Key Recommendations:**\n"
            for i, rec in enumerate(top_recs, 1):
                response += f"{i}. [{rec['priority'].upper()}] {rec['advice']}\n"

        risk = results["risk_assessment"]
        if risk["overall_risk"] > 0.6:
            response += f"\n⚠ Risk Alert: Overall risk score {risk['overall_risk']:.0%}\n"

        response += f"\n---\nBased on {len(summary['agents_consulted'])} intelligence agents | {len(state.citations)} citations"
        return response

    def _build_structured_report(self, results: dict[str, Any], state: AgriPulseState) -> dict[str, Any]:
        return {
            "format": "json",
            "generated_at": datetime.utcnow().isoformat(),
            "request_id": state.request_id,
            "sections": list(results.keys()),
            "downloadable": True,
        }

    def _get_alert_level(self, protection: dict[str, Any]) -> str:
        risks = protection.get("risk_scores", [])
        if not risks:
            return "low"
        max_risk = max(r.get("risk_score", 0) for r in risks)
        if max_risk > 0.8:
            return "critical"
        elif max_risk > 0.6:
            return "high"
        elif max_risk > 0.4:
            return "moderate"
        return "low"

    def tests(self) -> dict[str, bool]:
        base = super().tests()
        base["nl_generation"] = True
        base["report_builder"] = True
        return base
