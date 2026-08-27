from __future__ import annotations

from aoic_kernel.exceptions import CharterInvalid
from aoic_kernel.models import SkillContract


class SkillRegistry:
    """Contracts, dependencies, test status and provenance."""

    def __init__(self) -> None:
        self._skills: dict[str, SkillContract] = {}

    def register(self, contract: SkillContract) -> None:
        if contract.status == "DEPRECATED":
            raise CharterInvalid(f"Skill {contract.skill_id} is deprecated")
        self._skills[contract.skill_id] = contract

    def get(self, skill_id: str) -> SkillContract:
        if skill_id not in self._skills:
            raise CharterInvalid(f"Skill {skill_id} not found")
        return self._skills[skill_id]

    def deprecate(self, skill_id: str) -> None:
        if skill_id in self._skills:
            self._skills[skill_id].status = "DEPRECATED"
            del self._skills[skill_id]
