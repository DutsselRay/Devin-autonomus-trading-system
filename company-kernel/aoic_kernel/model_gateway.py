from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from aoic_kernel.models import ModelProvider, ModelProviderStatus


class ModelGateway:
    """Provider-agnostic model gateway with per-agent budgets, caching, batch and kill switch."""

    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {}
        self._agent_budgets: dict[str, float] = {}
        self._agent_spent: dict[str, float] = {}
        self._cache: dict[tuple[str, str, str, str], Any] = {}
        self._kill_switch_active = False

    def register_provider(
        self,
        name: str,
        model_family: str,
        cost_per_1k_tokens: float,
        max_rpm: int = 60,
        provider_id: Optional[str] = None,
    ) -> ModelProvider:
        if cost_per_1k_tokens < 0:
            raise ValueError("cost must be non-negative")
        provider = ModelProvider(
            provider_id=provider_id or f"PROV-{uuid4().hex[:8].upper()}",
            name=name,
            model_family=model_family,
            cost_per_1k_tokens=cost_per_1k_tokens,
            max_rpm=max_rpm,
            registered_at=datetime.now(timezone.utc),
        )
        self._providers[provider.provider_id] = provider
        return provider

    def get_provider(self, provider_id: str) -> ModelProvider:
        if provider_id not in self._providers:
            raise KeyError(provider_id)
        return self._providers[provider_id]

    def set_budget(self, agent_id: str, budget: float) -> None:
        if budget < 0:
            raise ValueError("budget must be non-negative")
        self._agent_budgets[agent_id] = budget
        self._agent_spent[agent_id] = 0.0

    def kill_switch(self, active: bool = True) -> None:
        self._kill_switch_active = active

    def call(
        self,
        agent_id: str,
        provider_id: str,
        prompt: str,
        tokens: int = 1000,
        use_cache: bool = True,
        batch: bool = False,
    ) -> dict[str, Any]:
        if self._kill_switch_active:
            raise RuntimeError("global kill switch is active")
        provider = self.get_provider(provider_id)
        if provider.status == ModelProviderStatus.KILLED:
            raise RuntimeError(f"provider {provider_id} is killed")

        budget = self._agent_budgets.get(agent_id, float("inf"))
        spent = self._agent_spent.get(agent_id, 0.0)
        cost = (tokens / 1000) * provider.cost_per_1k_tokens
        if spent + cost > budget:
            raise RuntimeError(f"agent {agent_id} would exceed budget")

        cache_key = (agent_id, provider_id, provider.model_family, prompt)
        if use_cache and cache_key in self._cache:
            return {
                "provider_id": provider_id,
                "cached": True,
                "model_family": provider.model_family,
                "batch": batch,
                "response": self._cache[cache_key],
            }

        # Shadow-mode response; no real model call.
        response = f"shadow-response-{uuid4().hex[:8]}"
        if use_cache:
            self._cache[cache_key] = response
        self._agent_spent[agent_id] = spent + cost
        return {
            "provider_id": provider_id,
            "cached": False,
            "model_family": provider.model_family,
            "batch": batch,
            "response": response,
            "cost": cost,
        }

    def budget_remaining(self, agent_id: str) -> float:
        budget = self._agent_budgets.get(agent_id, 0.0)
        spent = self._agent_spent.get(agent_id, 0.0)
        return budget - spent

    def kill_provider(self, provider_id: str) -> ModelProvider:
        provider = self.get_provider(provider_id)
        provider.status = ModelProviderStatus.KILLED
        self._providers[provider_id] = provider
        return provider

    def batch_call(
        self,
        agent_id: str,
        provider_id: str,
        prompts: list[str],
        tokens: int = 1000,
    ) -> list[dict[str, Any]]:
        return [self.call(agent_id, provider_id, p, tokens, batch=True) for p in prompts]
