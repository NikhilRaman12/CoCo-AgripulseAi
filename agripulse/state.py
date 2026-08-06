"""
AgriPulse Enterprise State Management
Typed Shared State for LangGraph StateGraph execution.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    DATA = "data_intelligence"
    AGRONOMY = "agronomy_intelligence"
    CROP_PROTECTION = "crop_protection"
    CROP_INTELLIGENCE = "crop_intelligence"
    KNOWLEDGE = "knowledge_intelligence"
    PROCUREMENT = "procurement_intelligence"
    EVIDENCE_TRUST = "evidence_trust"
    DECISION = "decision_intelligence"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class IntentType(str, Enum):
    CROP_ADVISORY = "crop_advisory"
    PEST_ALERT = "pest_alert"
    YIELD_PREDICTION = "yield_prediction"
    MARKET_ANALYSIS = "market_analysis"
    PROCUREMENT_PLAN = "procurement_plan"
    DATA_INGESTION = "data_ingestion"
    KNOWLEDGE_QUERY = "knowledge_query"
    FULL_ASSESSMENT = "full_assessment"
    WEATHER_ANALYSIS = "weather_analysis"


class A2AMessage(BaseModel):
    """Agent-to-Agent communication contract."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_agent: AgentRole
    target_agent: AgentRole
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    citations: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class TraceEntry(BaseModel):
    """Single entry in the execution trace."""
    agent: AgentRole
    action: str
    status: ExecutionStatus
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    retries: int = 0
    error: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentMemory(BaseModel):
    """Per-agent memory for context retention."""
    agent: AgentRole
    short_term: list[dict[str, Any]] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    last_execution: Optional[datetime] = None


class AgriPulseState(BaseModel):
    """
    Typed Shared State for the entire LangGraph execution.
    Passed through all nodes in the StateGraph.
    """
    # Request
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_query: str = ""
    intent: Optional[IntentType] = None
    detected_entities: dict[str, Any] = Field(default_factory=dict)

    # Execution plan
    execution_plan: list[AgentRole] = Field(default_factory=list)
    current_agent: Optional[AgentRole] = None
    execution_status: ExecutionStatus = ExecutionStatus.PENDING

    # Agent outputs (A2A messages)
    messages: list[A2AMessage] = Field(default_factory=list)
    agent_outputs: dict[str, Any] = Field(default_factory=dict)

    # Trace & observability
    trace: list[TraceEntry] = Field(default_factory=list)
    memory: dict[str, AgentMemory] = Field(default_factory=dict)

    # Final output
    final_response: Optional[dict[str, Any]] = None
    confidence_score: float = 0.0
    citations: list[str] = Field(default_factory=list)

    # Retry policy
    max_retries: int = 3
    retry_count: int = 0

    class Config:
        arbitrary_types_allowed = True

    def add_message(self, msg: A2AMessage) -> None:
        self.messages.append(msg)

    def add_trace(self, entry: TraceEntry) -> None:
        self.trace.append(entry)

    def get_agent_output(self, agent: AgentRole) -> Optional[dict[str, Any]]:
        return self.agent_outputs.get(agent.value)

    def set_agent_output(self, agent: AgentRole, output: dict[str, Any]) -> None:
        self.agent_outputs[agent.value] = output
