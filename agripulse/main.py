"""
AgriPulse Enterprise Agricultural Intelligence Platform
Main entry point.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys

from agripulse.graph import AgriPulseGraph
from agripulse.config import PlatformConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("agripulse")


async def run_query(query: str) -> dict:
    """Execute a single query through the AgriPulse platform."""
    config = PlatformConfig()
    platform = AgriPulseGraph(config)

    logger.info("=" * 60)
    logger.info("AgriPulse Enterprise Intelligence Platform")
    logger.info("=" * 60)
    logger.info(f"Query: {query}")
    logger.info("-" * 60)

    state = await platform.invoke(query)

    # Output results
    result = {
        "request_id": state.request_id,
        "intent": state.intent.value if state.intent else None,
        "status": state.execution_status.value,
        "confidence": state.confidence_score,
        "execution_plan": [a.value for a in state.execution_plan],
        "trace": [
            {
                "agent": t.agent.value,
                "status": t.status.value,
                "duration_ms": t.duration_ms,
                "retries": t.retries,
            }
            for t in state.trace
        ],
        "final_response": state.final_response,
        "citations": state.citations,
    }

    logger.info("-" * 60)
    logger.info("EXECUTION COMPLETE")
    logger.info(f"Status: {state.execution_status.value}")
    logger.info(f"Confidence: {state.confidence_score:.2%}")
    logger.info(f"Agents executed: {len(state.trace)}")
    logger.info(f"Citations: {len(state.citations)}")
    logger.info("=" * 60)

    # Print NL response
    if state.final_response:
        nl = state.final_response.get("natural_language_response", "")
        if nl:
            print("\n" + nl + "\n")

    return result


async def health_check():
    """Run platform health check."""
    platform = AgriPulseGraph()
    health = platform.health_check()
    print(json.dumps(health, indent=2, default=str))
    return health


async def run_tests():
    """Run all agent self-tests."""
    platform = AgriPulseGraph()
    results = platform.run_tests()
    print(json.dumps(results, indent=2))
    all_passed = all(
        all(v for v in tests.values())
        for tests in results.values()
    )
    print(f"\n{'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m agripulse.main <query>")
        print("  python -m agripulse.main --health")
        print("  python -m agripulse.main --test")
        print()
        print("Examples:")
        print('  python -m agripulse.main "Predict rice yield for Maharashtra kharif season"')
        print('  python -m agripulse.main "Pest alert for cotton in Punjab"')
        print('  python -m agripulse.main "Market analysis for wheat procurement in Haryana"')
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--health":
        asyncio.run(health_check())
    elif arg == "--test":
        asyncio.run(run_tests())
    else:
        query = " ".join(sys.argv[1:])
        result = asyncio.run(run_query(query))
        # Write full result to file for downstream use
        with open("/tmp/agripulse_result.json", "w") as f:
            json.dump(result, f, indent=2, default=str)


if __name__ == "__main__":
    main()
