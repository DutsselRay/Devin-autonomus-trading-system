from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.models import CostEstimate


def test_kernel_exposes_mcp_components():
    kernel = CompanyKernel()
    assert kernel.source_adapter is not None
    assert kernel.vendor_register is not None
    assert kernel.model_gateway is not None


def test_source_adapter_registers_connector():
    kernel = CompanyKernel()
    cost = CostEstimate(one_off=0.0, monthly=100.0, unit="EUR")
    conn = kernel.source_adapter.register(
        "SEC EDGAR",
        "SEC",
        "filings",
        "none",
        "10/min",
        "public domain",
        "edgar",
        "as_of_filing_date",
        ["schema", "date-range"],
        cost,
    )
    assert conn.connector_id in kernel.source_adapter.list_connectors()[0].connector_id
    assert conn.status == "ACTIVE"


def test_source_adapter_call_shadow_mode():
    kernel = CompanyKernel()
    conn = kernel.source_adapter.register(
        "FRED",
        "St. Louis Fed",
        "macro",
        "api_key",
        "100/hr",
        "public",
        "fred_series_id",
        "observation_date",
        ["non-empty", "date-range"],
        CostEstimate(monthly=0.0, unit="USD"),
    )
    result = kernel.source_adapter.call(conn.connector_id, {"series_id": "GDP", "as_of": "2024-01-01"})
    assert result["status"] == "SHADOW"
    assert result["provenance"] == "fred_series_id"


def test_source_adapter_fallback_works():
    kernel = CompanyKernel()
    primary = kernel.source_adapter.register(
        "Primary News",
        "NewsCo",
        "news",
        "api_key",
        "100/hr",
        "commercial",
        "newsfeed",
        "published_at",
        ["non-empty"],
        CostEstimate(monthly=50.0, unit="EUR"),
    )
    _fallback = kernel.source_adapter.register(
        "Fallback News",
        "AltNews",
        "news",
        "api_key",
        "50/hr",
        "commercial",
        "newsfeed",
        "published_at",
        ["non-empty"],
        CostEstimate(monthly=30.0, unit="EUR"),
        fallback_connector=primary.connector_id,
    )
    # Primary is disabled; calling it should fail because fallback is itself only set to primary.
    kernel.source_adapter.disable(primary.connector_id, "outage")
    with pytest.raises(RuntimeError):
        kernel.source_adapter.call(primary.connector_id, {"query": "earnings"})


def test_source_adapter_requires_quality_checks():
    kernel = CompanyKernel()
    conn = kernel.source_adapter.register(
        "NoCheck",
        "Bad",
        "data",
        "none",
        "1/min",
        "unknown",
        "none",
        "none",
        [],
        CostEstimate(monthly=0.0, unit="EUR"),
    )
    with pytest.raises(ValueError, match="quality checks"):
        kernel.source_adapter.call(conn.connector_id, {"x": 1})


def test_vendor_register_requires_exit_plan():
    kernel = CompanyKernel()
    with pytest.raises(ValueError, match="exit plan"):
        kernel.vendor_register.register(
            "DataCo",
            "market data",
            "cio",
            datetime.now(timezone.utc) + timedelta(days=365),
            ["AltData"],
            exit_plan="",
        )


def test_vendor_register_tracks_spend_and_alternatives():
    kernel = CompanyKernel()
    v = kernel.vendor_register.register(
        "DataCo",
        "market data",
        "cio",
        datetime.now(timezone.utc) + timedelta(days=365),
        ["AltData"],
        exit_plan="export to parquet and re-ingest from AltData",
    )
    updated = kernel.vendor_register.add_spend(v.vendor_id, 500.0)
    assert updated.spend == 500.0


def test_vendor_register_exit_requires_alternative():
    kernel = CompanyKernel()
    a = kernel.vendor_register.register(
        "AltData",
        "market data",
        "cio",
        datetime.now(timezone.utc) + timedelta(days=365),
        [],
        exit_plan="open source ingest",
    )
    v = kernel.vendor_register.register(
        "DataCo",
        "market data",
        "cio",
        datetime.now(timezone.utc) + timedelta(days=365),
        [a.vendor_id],
        exit_plan="switch to AltData",
    )
    exited = kernel.vendor_register.exit(v.vendor_id, a.vendor_id)
    assert exited.status == "EXITED"


def test_vendor_register_exit_rejects_unknown_alternative():
    kernel = CompanyKernel()
    v = kernel.vendor_register.register(
        "DataCo",
        "market data",
        "cio",
        datetime.now(timezone.utc) + timedelta(days=365),
        ["Unknown"],
        exit_plan="switch",
    )
    with pytest.raises(ValueError):
        kernel.vendor_register.exit(v.vendor_id, "Unknown")


def test_model_gateway_registers_and_calls():
    kernel = CompanyKernel()
    prov = kernel.model_gateway.register_provider("gpt-4o", "openai", 0.005)
    kernel.model_gateway.set_budget("agent-1", 1.0)
    result = kernel.model_gateway.call("agent-1", prov.provider_id, "summarize")
    assert result["cached"] is False
    assert result["cost"] == 0.005


def test_model_gateway_caches():
    kernel = CompanyKernel()
    prov = kernel.model_gateway.register_provider("gpt-4o", "openai", 0.005)
    kernel.model_gateway.set_budget("agent-1", 1.0)
    r1 = kernel.model_gateway.call("agent-1", prov.provider_id, "same")
    r2 = kernel.model_gateway.call("agent-1", prov.provider_id, "same")
    assert r2["cached"] is True
    assert r1["response"] == r2["response"]


def test_model_gateway_budget_enforced():
    kernel = CompanyKernel()
    prov = kernel.model_gateway.register_provider("expensive", "llm", 1.0)
    kernel.model_gateway.set_budget("agent-1", 0.5)
    with pytest.raises(RuntimeError, match="budget"):
        kernel.model_gateway.call("agent-1", prov.provider_id, "prompt", tokens=1000)


def test_model_gateway_kill_switch():
    kernel = CompanyKernel()
    prov = kernel.model_gateway.register_provider("gpt-4o", "openai", 0.005)
    kernel.model_gateway.set_budget("agent-1", 1.0)
    kernel.model_gateway.kill_switch(True)
    with pytest.raises(RuntimeError, match="kill switch"):
        kernel.model_gateway.call("agent-1", prov.provider_id, "x")


def test_model_gateway_batch_call():
    kernel = CompanyKernel()
    prov = kernel.model_gateway.register_provider("gpt-4o", "openai", 0.005)
    kernel.model_gateway.set_budget("agent-1", 1.0)
    results = kernel.model_gateway.batch_call("agent-1", prov.provider_id, ["a", "b", "c"])
    assert len(results) == 3
    assert all(r["batch"] for r in results)


def test_model_gateway_killed_provider_rejected():
    kernel = CompanyKernel()
    prov = kernel.model_gateway.register_provider("bad", "openai", 0.005)
    kernel.model_gateway.kill_provider(prov.provider_id)
    kernel.model_gateway.set_budget("agent-1", 1.0)
    with pytest.raises(RuntimeError, match="killed"):
        kernel.model_gateway.call("agent-1", prov.provider_id, "x")
