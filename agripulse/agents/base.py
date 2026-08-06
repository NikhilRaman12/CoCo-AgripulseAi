"""
AgriPulse Base Agent
Abstract base with execute/validate/health/metrics/tests interface.
All agents inherit from this.
"""

from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from agripulse.state import (
    AgriPulseState,
    AgentRole,
    A2AMessage,
    TraceEntry,
    ExecutionStatus,
    AgentMemory,
)
from agripulse.config import AgentConfig


class BaseAgent(ABC):
    """Base class for all CoCo Intelligence Agents."""

    def __init__(self, role: AgentRole, config: AgentConfig | None = None):
        self.role = role
        self.config = config or AgentConfig()
        self.logger = logging.getLogger(f"agripulse.{role.value}")
        self._metrics: dict[str, Any] = {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration_ms": 0.0,
            "last_execution": None,
        }

    @abstractmethod
    async def execute(self, state: AgriPulseState) -> AgriPulseState:
        """Execute the agent's primary responsibility."""
        ...

    @abstractmethod
    async def validate(self, state: AgriPulseState) -> bool:
        """Validate the agent's output."""
        ...

    def health(self) -> dict[str, Any]:
        """Health check for observability."""
        return {
            "agent": self.role.value,
            "status": "healthy",
            "metrics": self._metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def metrics(self) -> dict[str, Any]:
        """Return execution metrics."""
        return self._metrics

    def tests(self) -> dict[str, bool]:
        """Self-test suite. Override in subclasses."""
        return {"base_instantiation": True, "config_loaded": self.config is not None}

    async def run(self, state: AgriPulseState) -> AgriPulseState:
        """
        Execute with retry policy, tracing, and A2A message emission.
        This is the main entry point called by the LangGraph node.
        """
        state.current_agent = self.role
        trace = TraceEntry(
            agent=self.role,
            action="execute",
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        start = time.perf_counter()

        for attempt in range(self.config.max_retries):
            try:
                self.logger.info(f"Executing (attempt {attempt + 1})")
                state = await self.execute(state)

                # Trace success
                duration = (time.perf_counter() - start) * 1000
                trace.status = ExecutionStatus.SUCCESS
                trace.completed_at = datetime.utcnow()
                trace.duration_ms = duration
                trace.retries = attempt
                state.add_trace(trace)

                # Update metrics
                self._metrics["total_executions"] += 1
                self._metrics["successful"] += 1
                self._metrics["last_execution"] = datetime.utcnow().isoformat()
                self._update_avg_duration(duration)

                # Update memory
                self._update_memory(state)
                return state

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                trace.retries = attempt + 1
                if attempt == self.config.max_retries - 1:
                    trace.status = ExecutionStatus.FAILED
                    trace.error = str(e)
                    trace.completed_at = datetime.utcnow()
                    trace.duration_ms = (time.perf_counter() - start) * 1000
                    state.add_trace(trace)
                    self._metrics["total_executions"] += 1
                    self._metrics["failed"] += 1
                    self._emit_error(state, str(e))
                else:
                    trace.status = ExecutionStatus.RETRYING
                    import asyncio
                    await asyncio.sleep(self.config.retry_delay_seconds)

        return state

    def _emit_message(
        self,
        state: AgriPulseState,
        target: AgentRole,
        payload: dict[str, Any],
        confidence: float = 1.0,
        citations: list[str] | None = None,
    ) -> None:
        msg = A2AMessage(
            source_agent=self.role,
            target_agent=target,
            payload=payload,
            confidence=confidence,
            citations=citations or [],
        )
        state.add_message(msg)

    def _emit_error(self, state: AgriPulseState, error: str) -> None:
        msg = A2AMessage(
            source_agent=self.role,
            target_agent=AgentRole.ORCHESTRATOR,
            payload={"error": error},
            errors=[error],
            confidence=0.0,
        )
        state.add_message(msg)

    def _update_memory(self, state: AgriPulseState) -> None:
        if not self.config.enable_memory:
            return
        key = self.role.value
        if key not in state.memory:
            state.memory[key] = AgentMemory(agent=self.role)
        mem = state.memory[key]
        mem.last_execution = datetime.utcnow()
        output = state.get_agent_output(self.role)
        if output:
            mem.short_term.append(output)
            if len(mem.short_term) > 10:
                mem.short_term = mem.short_term[-10:]

    def _update_avg_duration(self, duration_ms: float) -> None:
        n = self._metrics["successful"]
        avg = self._metrics["avg_duration_ms"]
        self._metrics["avg_duration_ms"] = avg + (duration_ms - avg) / n
