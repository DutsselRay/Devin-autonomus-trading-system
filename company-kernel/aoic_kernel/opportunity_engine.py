from __future__ import annotations

from datetime import datetime
from typing import Any

from aoic_kernel.backtester import Backtester
from aoic_kernel.calibration import CalibrationEngine
from aoic_kernel.entity_master import EntityMaster
from aoic_kernel.experiment_registry import ExperimentRegistry
from aoic_kernel.feature_store import TemporalFeatureStore
from aoic_kernel.oosset import SealedOOSSetManager
from aoic_kernel.outcome_engine import OutcomeEngine
from aoic_kernel.pattern_engine import PatternEngine
from aoic_kernel.research_engine import ResearchEngine
from aoic_kernel.research_publication_gate import ResearchPublicationGate
from aoic_kernel.universe import SurvivorshipAwareUniverse


class OpportunityEngine:
    """Phase 3 economic/financial opportunity engine."""

    def __init__(self) -> None:
        self.entity_master = EntityMaster()
        self.feature_store = TemporalFeatureStore()
        self.universe = SurvivorshipAwareUniverse(
            self.entity_master,
            self.feature_store,
        )
        self.oos_manager = SealedOOSSetManager()
        self.experiments = ExperimentRegistry(oos_manager=self.oos_manager)
        self.backtester = Backtester(self.feature_store)
        self.patterns = PatternEngine()
        self.research = ResearchEngine(self.patterns, self.feature_store)
        self.calibration = CalibrationEngine()
        self.publication = ResearchPublicationGate(self.calibration)
        self.outcomes = OutcomeEngine()

    def ingest_feature(self, record: Any) -> None:
        self.feature_store.store(record)

    def ingest_fact(self, record: Any) -> None:
        self.entity_master.ingest(record)

    def evaluate_oos(
        self,
        experiment_id: str,
        agent_id: str,
    ) -> Any:
        experiment = self.experiments.get(experiment_id)
        if experiment is None or experiment.oos_set_id is None:
            raise ValueError(f"Experiment {experiment_id} has no sealed OOS set")
        return self.oos_manager.access(experiment.oos_set_id, agent_id)
