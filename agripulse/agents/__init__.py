"""AgriPulse Agent Registry"""

from agripulse.agents.orchestrator import OrchestratorAgent
from agripulse.agents.data_intelligence import DataIntelligenceAgent
from agripulse.agents.agronomy_intelligence import AgronomyIntelligenceAgent
from agripulse.agents.crop_protection import CropProtectionAgent
from agripulse.agents.crop_intelligence import CropIntelligenceAgent
from agripulse.agents.knowledge_intelligence import KnowledgeIntelligenceAgent
from agripulse.agents.procurement_intelligence import ProcurementIntelligenceAgent
from agripulse.agents.evidence_trust import EvidenceTrustAgent
from agripulse.agents.decision_intelligence import DecisionIntelligenceAgent

__all__ = [
    "OrchestratorAgent",
    "DataIntelligenceAgent",
    "AgronomyIntelligenceAgent",
    "CropProtectionAgent",
    "CropIntelligenceAgent",
    "KnowledgeIntelligenceAgent",
    "ProcurementIntelligenceAgent",
    "EvidenceTrustAgent",
    "DecisionIntelligenceAgent",
]
