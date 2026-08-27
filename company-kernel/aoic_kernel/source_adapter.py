from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from aoic_kernel.models import ConnectorStatus, CostEstimate, SourceConnector


class SourceAdapter:
    """Replaceable vendor connector registry with schema validation and fallback."""

    def __init__(self) -> None:
        self._connectors: dict[str, SourceConnector] = {}

    def register(
        self,
        name: str,
        vendor: str,
        purpose: str,
        auth_type: str,
        rate_limit: str,
        rights: str,
        provenance: str,
        pit_semantics: str,
        quality_checks: list[str],
        cost: CostEstimate,
        fallback_connector: Optional[str] = None,
        connector_id: Optional[str] = None,
    ) -> SourceConnector:
        if fallback_connector and fallback_connector not in self._connectors:
            raise ValueError("fallback connector must be registered first")
        connector = SourceConnector(
            connector_id=connector_id or f"CONN-{uuid4().hex[:8].upper()}",
            name=name,
            vendor=vendor,
            purpose=purpose,
            auth_type=auth_type,
            rate_limit=rate_limit,
            rights=rights,
            provenance=provenance,
            pit_semantics=pit_semantics,
            quality_checks=quality_checks,
            cost=cost,
            fallback_connector=fallback_connector,
            registered_at=datetime.now(timezone.utc),
        )
        self._connectors[connector.connector_id] = connector
        return connector

    def get(self, connector_id: str) -> SourceConnector:
        if connector_id not in self._connectors:
            raise KeyError(connector_id)
        return self._connectors[connector_id]

    def list_connectors(self) -> list[SourceConnector]:
        return list(self._connectors.values())

    def disable(self, connector_id: str, reason: str) -> SourceConnector:
        connector = self.get(connector_id)
        connector.status = ConnectorStatus.DISABLED
        self._connectors[connector_id] = connector
        return connector

    def call(
        self,
        connector_id: str,
        payload: dict[str, Any],
        expected_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        connector = self.get(connector_id)
        if connector.status != ConnectorStatus.ACTIVE:
            if connector.fallback_connector:
                return self.call(connector.fallback_connector, payload, expected_schema)
            raise RuntimeError(f"connector {connector_id} is not ACTIVE and has no fallback")

        if not connector.quality_checks:
            raise ValueError("connector has no quality checks configured")

        if expected_schema:
            missing = expected_schema.keys() - payload.keys()
            if missing:
                raise ValueError(f"payload missing required fields: {missing}")

        # Shadow-mode stub: do not perform real external calls.
        return {
            "connector_id": connector.connector_id,
            "vendor": connector.vendor,
            "provenance": connector.provenance,
            "pit_semantics": connector.pit_semantics,
            "payload_keys": list(payload.keys()),
            "quality_checks_passed": connector.quality_checks,
            "status": "SHADOW",
        }
