from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from aoic_kernel.exceptions import OOSAccessDenied
from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.models import (
    Entity,
    Experiment,
    ExperimentStatus,
    FeatureRecord,
    PITRecord,
)


def _day(n: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=n)


def _entity(
    entity_id: str,
    list_offset: int = 0,
    delist_offset: int | None = None,
) -> Entity:
    return Entity(
        entity_id=entity_id,
        symbol=entity_id.split("_")[0],
        name=entity_id,
        asset_class="equity",
        list_date=_day(list_offset),
        delist_date=_day(delist_offset) if delist_offset is not None else None,
    )


def _pit_record(
    record_id: str,
    entity_id: str,
    released_at: datetime,
    value: float,
) -> PITRecord:
    return PITRecord(
        record_id=record_id,
        entity_id=entity_id,
        event_time=released_at,
        released_at=released_at,
        observed_at=released_at,
        ingested_at=released_at,
        valid_from=released_at,
        source="sec_edgar",
        data={"value": value},
    )


def _price(
    entity_id: str,
    event_time: datetime,
    released_at: datetime,
    price: float,
    valid_to: datetime | None = None,
    delay: float = 0.0,
    ingested_at: datetime | None = None,
) -> FeatureRecord:
    return FeatureRecord(
        record_id=f"FEAT-{entity_id}-{event_time:%Y%m%d}-{released_at:%Y%m%d}",
        entity_id=entity_id,
        feature_name="price",
        event_time=event_time,
        released_at=released_at,
        observed_at=released_at,
        ingested_at=ingested_at or datetime.now(timezone.utc),
        valid_from=event_time,
        valid_to=valid_to,
        value=price,
        unit="USD",
        source="test",
        availability_delay=delay,
    )


def _experiment(
    experiment_id: str = "EXP-000001",
    discoverer: str = "cao",
) -> Experiment:
    return Experiment(
        experiment_id=experiment_id,
        name="momentum pilot",
        hypothesis="positive prior-day returns persist short term",
        discoverer=discoverer,
        discovery_start=_day(0),
        discovery_end=_day(5),
    )


# 1. Entity lifecycle: active only between list and delist dates.
def test_entity_lifecycle(kernel: CompanyKernel) -> None:
    entity = _entity("AAPL_US", list_offset=1, delist_offset=5)
    kernel.opportunity.entity_master.register(entity)

    assert not entity.is_active_as_of(_day(0))
    assert entity.is_active_as_of(_day(1))
    assert entity.is_active_as_of(_day(4))
    assert not entity.is_active_as_of(_day(5))


# 2. PIT ingestion reconstructs state as-of a given timestamp.
def test_pit_ingestion_reconstructs_as_of(kernel: CompanyKernel) -> None:
    entity = _entity("AAPL_US")
    kernel.opportunity.entity_master.register(entity)
    kernel.opportunity.entity_master.ingest(_pit_record("PIT-001", "AAPL_US", _day(0), 100.0))
    kernel.opportunity.entity_master.ingest(_pit_record("PIT-002", "AAPL_US", _day(2), 110.0))

    history = kernel.opportunity.entity_master.pit_history("AAPL_US", _day(1))
    assert len(history) == 1
    assert history[0].data["value"] == 100.0

    history_later = kernel.opportunity.entity_master.pit_history("AAPL_US", _day(3))
    assert len(history_later) == 2


# 3. Feature store returns the latest value available as-of a date.
def test_feature_store_as_of_returns_latest(kernel: CompanyKernel) -> None:
    kernel.opportunity.feature_store.store(_price("AAPL_US", _day(0), _day(0), 100.0))
    kernel.opportunity.feature_store.store(_price("AAPL_US", _day(0), _day(0), 105.0, valid_to=_day(2)))
    kernel.opportunity.feature_store.store(_price("AAPL_US", _day(1), _day(1), 110.0))

    record = kernel.opportunity.feature_store.get("AAPL_US", "price", _day(1))
    assert record is not None
    assert record.value == 110.0

    old_record = kernel.opportunity.feature_store.get("AAPL_US", "price", _day(0))
    assert old_record is not None
    assert old_record.value == 105.0

    stale_record = kernel.opportunity.feature_store.get("AAPL_US", "price", _day(2))
    assert stale_record is None or stale_record.value == 110.0


# 4. Feature availability delay is respected.
def test_feature_availability_delay_respected(kernel: CompanyKernel) -> None:
    kernel.opportunity.feature_store.store(_price("AAPL_US", _day(0), _day(0), 100.0, delay=86400.0))

    assert kernel.opportunity.feature_store.get("AAPL_US", "price", _day(0)) is None
    record = kernel.opportunity.feature_store.get("AAPL_US", "price", _day(1))
    assert record is not None
    assert record.value == 100.0


# 5. Feature store refuses to serve data not yet released as-of the query time.
def test_feature_store_no_future_data(kernel: CompanyKernel) -> None:
    kernel.opportunity.feature_store.store(_price("AAPL_US", _day(2), _day(2), 120.0))

    assert kernel.opportunity.feature_store.get("AAPL_US", "price", _day(1)) is None
    assert kernel.opportunity.feature_store.get("AAPL_US", "price", _day(2)) is not None


# 6. Survivorship-aware universe excludes delisted entities.
def test_survivorship_universe_excludes_delisted(kernel: CompanyKernel) -> None:
    active = _entity("AAPL_US", list_offset=0)
    delisted = _entity("ENRON_US", list_offset=0, delist_offset=3)
    kernel.opportunity.entity_master.register(active)
    kernel.opportunity.entity_master.register(delisted)

    universe = kernel.opportunity.universe.build(_day(3))
    assert "AAPL_US" in universe
    assert "ENRON_US" not in universe


# 7. Universe includes active entities and excludes not-yet-listed ones.
def test_universe_active_and_not_yet_listed(kernel: CompanyKernel) -> None:
    current = _entity("AAPL_US", list_offset=0)
    future = _entity("FUTURE_CO", list_offset=5)
    kernel.opportunity.entity_master.register(current)
    kernel.opportunity.entity_master.register(future)

    universe = kernel.opportunity.universe.build(_day(2))
    assert "AAPL_US" in universe
    assert "FUTURE_CO" not in universe


# 8. Sealed OOS set denies access to discovery agents.
def test_sealed_oos_denies_discovery(kernel: CompanyKernel) -> None:
    oos_id = kernel.opportunity.oos_manager.create({"holdout": [1, 2, 3]})
    with pytest.raises(OOSAccessDenied):
        kernel.opportunity.oos_manager.access(oos_id, "cao")


# 9. Sealed OOS set is accessible to the auditor.
def test_sealed_oos_allows_auditor(kernel: CompanyKernel) -> None:
    data = {"holdout": [1, 2, 3]}
    oos_id = kernel.opportunity.oos_manager.create(data)
    accessed = kernel.opportunity.oos_manager.access(oos_id, "cao_auditor")
    assert accessed == data


# 10. Experiment lifecycle with OOS seal and contamination tracking.
def test_experiment_lifecycle_and_contamination(kernel: CompanyKernel) -> None:
    exp = _experiment()
    kernel.opportunity.experiments.preregister(exp)
    assert exp.status == ExperimentStatus.PREREGISTERED

    kernel.opportunity.experiments.start(exp.experiment_id)
    assert exp.status == ExperimentStatus.RUNNING

    oos_id = kernel.opportunity.oos_manager.create({"labels": [0, 1]})
    kernel.opportunity.experiments.seal_oos(exp.experiment_id, oos_id)
    assert exp.status == ExperimentStatus.SEALED_OOS
    assert exp.oos_set_id == oos_id

    kernel.opportunity.experiments.log_contamination(exp.experiment_id, "cao", "looked at OOS during discovery")
    assert "cao: looked at OOS during discovery" in exp.contamination_log
    assert kernel.opportunity.oos_manager.is_contaminated(oos_id, "cao")

    kernel.opportunity.experiments.complete(exp.experiment_id, "BT-001")
    assert exp.status == ExperimentStatus.COMPLETED


# 11. Backtest produces deterministic buy-and-hold baseline.
def test_backtest_buy_and_hold_baseline(kernel: CompanyKernel) -> None:
    aapl = _entity("AAPL_US")
    msft = _entity("MSFT_US")
    kernel.opportunity.entity_master.register(aapl)
    kernel.opportunity.entity_master.register(msft)

    for i in range(6):
        kernel.opportunity.feature_store.store(_price("AAPL_US", _day(i), _day(i), 100.0 + i))
        kernel.opportunity.feature_store.store(_price("MSFT_US", _day(i), _day(i), 200.0 + i))

    universe = ["AAPL_US", "MSFT_US"]
    result = kernel.opportunity.backtester.run(
        experiment_id="EXP-000002",
        strategy="buy_and_hold",
        universe=universe,
        start_date=_day(0),
        end_date=_day(5),
        capital=10000.0,
        cost_rate=0.001,
    )

    assert result.total_return > 0
    assert result.start_value == 10000.0
    assert result.end_value > result.start_value
    assert result.costs > 0
    assert result.metrics["num_observations"] == 7


# 12. Random baseline is deterministic when seeded.
def test_backtest_random_baseline_deterministic(kernel: CompanyKernel) -> None:
    aapl = _entity("AAPL_US")
    msft = _entity("MSFT_US")
    kernel.opportunity.entity_master.register(aapl)
    kernel.opportunity.entity_master.register(msft)

    for i in range(4):
        kernel.opportunity.feature_store.store(_price("AAPL_US", _day(i), _day(i), 100.0 + i))
        kernel.opportunity.feature_store.store(_price("MSFT_US", _day(i), _day(i), 200.0 + i))

    universe = ["AAPL_US", "MSFT_US"]
    result_a = kernel.opportunity.backtester.run(
        experiment_id="EXP-000003",
        strategy="random",
        universe=universe,
        start_date=_day(0),
        end_date=_day(3),
        seed=123,
    )
    result_b = kernel.opportunity.backtester.run(
        experiment_id="EXP-000003",
        strategy="random",
        universe=universe,
        start_date=_day(0),
        end_date=_day(3),
        seed=123,
    )

    assert result_a.end_value == result_b.end_value
    assert result_a.total_return == result_b.total_return


# 13. Backtest cannot use prices released after the simulation date.
def test_backtest_no_lookahead(kernel: CompanyKernel) -> None:
    entity = _entity("AAPL_US")
    kernel.opportunity.entity_master.register(entity)

    # Day 0 and day 1 prices are released immediately.
    kernel.opportunity.feature_store.store(_price("AAPL_US", _day(0), _day(0), 100.0))
    kernel.opportunity.feature_store.store(_price("AAPL_US", _day(1), _day(1), 101.0))
    # Day 2 price is released one day late; it must not be used on day 2.
    kernel.opportunity.feature_store.store(_price("AAPL_US", _day(2), _day(3), 150.0))

    day2_record = kernel.opportunity.feature_store.get("AAPL_US", "price", _day(2))
    assert day2_record is not None
    assert day2_record.value == 101.0

    result = kernel.opportunity.backtester.run(
        experiment_id="EXP-000004",
        strategy="buy_and_hold",
        universe=["AAPL_US"],
        start_date=_day(0),
        end_date=_day(2),
        cost_rate=0.0,
    )

    # The backtest must stop at the last PIT price available on each simulation date.
    expected_return = (101.0 / 100.0) - 1.0
    assert abs(result.total_return - expected_return) < 1e-9


# 14. Cash baseline produces zero return and zero costs.
def test_backtest_cash_baseline(kernel: CompanyKernel) -> None:
    entity = _entity("AAPL_US")
    kernel.opportunity.entity_master.register(entity)
    kernel.opportunity.feature_store.store(_price("AAPL_US", _day(0), _day(0), 100.0))
    kernel.opportunity.feature_store.store(_price("AAPL_US", _day(1), _day(1), 200.0))

    result = kernel.opportunity.backtester.run(
        experiment_id="EXP-000005",
        strategy="cash",
        universe=["AAPL_US"],
        start_date=_day(0),
        end_date=_day(1),
        capital=5000.0,
    )

    assert result.end_value == 5000.0
    assert result.total_return == 0.0
    assert result.costs == 0.0
