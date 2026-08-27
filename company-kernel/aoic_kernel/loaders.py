from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from aoic_kernel.models import AgentCharter, SkillContract


def _coerce_datetime(value: Any) -> Any:
    if isinstance(value, str) and len(value) >= 10 and value[4] == "-" and value[7] == "-":
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt
        except ValueError:
            pass
    return value


def _deep_convert(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deep_convert(_coerce_datetime(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_convert(_coerce_datetime(v)) for v in obj]
    return _coerce_datetime(obj)


def load_agent_charter(path: str | Path) -> AgentCharter:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    data = _deep_convert(data)
    return AgentCharter(**data)


def load_skill_contract(path: str | Path) -> SkillContract:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    data = _deep_convert(data)
    return SkillContract(**data)
