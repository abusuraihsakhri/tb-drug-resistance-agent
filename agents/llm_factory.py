"""
Deterministic mock adapter for the demonstration supervisor; live providers are not implemented.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Tb Drug Resistance Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} Demonstration Mock]: Mock output (no clinical or scientific verification performed) for query: '{prompt[:60]}...'. Parameters evaluated under DEMONSTRATION ONLY - no guideline validation."


class LLMFactory:
    """Creates a mock response provider; no live LLM or comprehensive PHI guard."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Tb Drug Resistance Agent"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError(
            f"LLM provider {provider!r} is not implemented. "
            "Only the deterministic mock provider is available."
        )
