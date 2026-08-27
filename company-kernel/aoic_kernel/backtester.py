from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any

from aoic_kernel.feature_store import TemporalFeatureStore
from aoic_kernel.models import BacktestRun


class Backtester:
    """Deterministic, PIT-only backtester with simple baselines."""

    VALID_STRATEGIES = {"cash", "buy_and_hold", "random", "momentum"}

    def __init__(
        self,
        feature_store: TemporalFeatureStore,
    ) -> None:
        self.feature_store = feature_store

    def run(
        self,
        *,
        experiment_id: str | None = None,
        strategy: str = "buy_and_hold",
        universe: list[str],
        start_date: datetime,
        end_date: datetime,
        capital: float = 10000.0,
        cost_rate: float = 0.001,
        seed: int = 42,
        top_n: int = 1,
        price_feature: str = "price",
    ) -> BacktestRun:
        if strategy not in self.VALID_STRATEGIES:
            raise ValueError(f"Unknown strategy {strategy}")

        dates = self._date_range(start_date, end_date)
        if not dates:
            raise ValueError("start_date must be before or equal to end_date")

        holdings: dict[str, float] = {}
        cash = float(capital)
        costs = 0.0
        values: list[float] = [float(capital)]
        prev_prices: dict[str, float] = {}
        target_weights: dict[str, float] | None = None
        rng = random.Random(seed)
        rebalances = 0

        for idx, date in enumerate(dates):
            prices: dict[str, float] = {}
            for entity_id in universe:
                record = self.feature_store.get(entity_id, price_feature, date)
                if record is not None and record.value is not None:
                    try:
                        prices[entity_id] = float(record.value)
                    except (TypeError, ValueError):
                        continue

            active = list(prices.keys())
            if not active:
                continue

            portfolio_value = cash + sum(
                holdings.get(e, 0.0) * prices[e] for e in active
            )
            if portfolio_value <= 0:
                continue

            current_weights: dict[str, float] = {"__cash__": cash / portfolio_value}
            for e in active:
                weight = holdings.get(e, 0.0) * prices[e] / portfolio_value
                if weight:
                    current_weights[e] = weight

            if strategy == "cash":
                new_target: dict[str, float] = {}
            elif strategy == "buy_and_hold":
                if target_weights is None:
                    weight = 1.0 / len(active)
                    new_target = {e: weight for e in active}
                    target_weights = new_target
                else:
                    new_target = {e: target_weights.get(e, 0.0) for e in active}
            elif strategy == "random":
                if target_weights is None:
                    draws = [rng.random() for _ in active]
                    total = sum(draws) or 1.0
                    new_target = {e: w / total for e, w in zip(active, draws)}
                    target_weights = new_target
                else:
                    new_target = {e: target_weights.get(e, 0.0) for e in active}
            else:  # momentum
                returns: list[tuple[str, float]] = []
                for e in active:
                    if e in prev_prices and prev_prices[e] != 0:
                        ret = prices[e] / prev_prices[e] - 1.0
                        returns.append((e, ret))
                returns.sort(key=lambda x: x[1], reverse=True)
                picks = [e for e, _ in returns[:top_n] if _ > 0]
                if picks and idx > 0:
                    weight = 1.0 / len(picks)
                    new_target = {e: weight for e in picks}
                else:
                    new_target = {}

            cash_weight = 1.0 - sum(new_target.values())
            new_target["__cash__"] = cash_weight

            all_keys = set(current_weights.keys()) | set(new_target.keys())
            turnover = (
                sum(
                    abs(new_target.get(k, 0.0) - current_weights.get(k, 0.0))
                    for k in all_keys
                )
                / 2.0
            )

            trade_cost = portfolio_value * turnover * cost_rate
            costs += trade_cost
            nav = portfolio_value - trade_cost
            rebalances += 1 if turnover > 1e-9 else 0

            cash = nav * cash_weight
            for e in active:
                if e in new_target:
                    holdings[e] = (nav * new_target[e]) / prices[e]
                else:
                    holdings.pop(e, None)

            for e in list(holdings.keys()):
                if e not in active:
                    del holdings[e]

            values.append(nav)
            prev_prices = prices

        end_value = values[-1]
        start_value = values[0]
        metrics = self._compute_metrics(values)

        return BacktestRun(
            backtest_id=f"BT-{experiment_id or 'none'}-{strategy}",
            experiment_id=experiment_id,
            strategy=strategy,
            universe=universe,
            start_date=dates[0],
            end_date=dates[-1],
            start_value=start_value,
            end_value=end_value,
            costs=costs,
            benchmark=strategy,
            metrics=metrics,
        )

    @staticmethod
    def _date_range(start: datetime, end: datetime) -> list[datetime]:
        days = (end - start).days
        if days < 0:
            return []
        return [start + timedelta(days=i) for i in range(days + 1)]

    @staticmethod
    def _compute_metrics(values: list[float]) -> dict[str, Any]:
        total_return = (values[-1] / values[0]) - 1.0 if values[0] else 0.0
        daily_returns = [
            (values[i] / values[i - 1]) - 1.0 for i in range(1, len(values))
        ]
        volatility = 0.0
        sharpe = 0.0
        if len(daily_returns) > 1:
            mean = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean) ** 2 for r in daily_returns) / len(daily_returns)
            volatility = math.sqrt(variance) if variance > 0 else 0.0
            if volatility > 0:
                sharpe = math.sqrt(252) * (mean / volatility)
        max_dd = 0.0
        peak = values[0]
        for v in values:
            if v > peak:
                peak = v
            drawdown = (peak - v) / peak if peak else 0.0
            if drawdown > max_dd:
                max_dd = drawdown
        return {
            "total_return": total_return,
            "daily_returns": daily_returns,
            "volatility": volatility,
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "num_observations": len(values),
        }
