from __future__ import annotations

import pytest

from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.models import MaturityLevel


def test_kernel_exposes_maturity_evaluator():
    kernel = CompanyKernel()
    assert kernel.maturity is not None


def test_maturity_has_twelve_criteria():
    kernel = CompanyKernel()
    criteria = kernel.maturity.list_criteria()
    assert len(criteria) == 12
    assert {c.criterion_id for c in criteria} == {f"C{i}" for i in range(1, 13)}


def test_maturity_defaults_all_fail():
    kernel = CompanyKernel()
    score = kernel.maturity.evaluate()
    assert score.overall_10_of_10 is False
    assert score.average == 0.0


def test_maturity_partial_is_not_10_of_10():
    kernel = CompanyKernel()
    for i, criterion in enumerate(kernel.maturity.list_criteria(), start=1):
        level = MaturityLevel.PASS if i < 12 else MaturityLevel.PARTIAL
        kernel.maturity.submit_evidence(criterion.criterion_id, level, ["evidence"])
    score = kernel.maturity.evaluate()
    assert score.overall_10_of_10 is False
    assert score.average == (11 + 0.5) / 12


def test_maturity_10_of_10_requires_all_pass():
    kernel = CompanyKernel()
    for criterion in kernel.maturity.list_criteria():
        kernel.maturity.submit_evidence(criterion.criterion_id, MaturityLevel.PASS, ["evidence"])
    score = kernel.maturity.evaluate()
    assert score.overall_10_of_10 is True
    assert score.average == 1.0


def test_maturity_no_averaging_away_fail():
    kernel = CompanyKernel()
    for i, criterion in enumerate(kernel.maturity.list_criteria(), start=1):
        if i == 1:
            level = MaturityLevel.FAIL
        else:
            level = MaturityLevel.PASS
        kernel.maturity.submit_evidence(criterion.criterion_id, level, ["evidence"])
    score = kernel.maturity.evaluate()
    assert score.overall_10_of_10 is False


def test_maturity_evidence_required():
    kernel = CompanyKernel()
    with pytest.raises(ValueError, match="evidence"):
        kernel.maturity.submit_evidence("C1", MaturityLevel.PASS, [])


def test_maturity_criterion_evidence_preserved():
    kernel = CompanyKernel()
    kernel.maturity.submit_evidence("C1", MaturityLevel.PASS, ["audit-log", "test-report"])
    criterion = kernel.maturity.get("C1")
    assert "audit-log" in criterion.evidence
    assert "test-report" in criterion.evidence
    assert criterion.level == MaturityLevel.PASS


def test_maturity_passed_then_partial_updates():
    kernel = CompanyKernel()
    kernel.maturity.submit_evidence("C1", MaturityLevel.PASS, ["a"])
    kernel.maturity.submit_evidence("C1", MaturityLevel.PARTIAL, ["b"])
    assert kernel.maturity.get("C1").level == MaturityLevel.PARTIAL


def test_maturity_scorecard_includes_criteria():
    kernel = CompanyKernel()
    score = kernel.maturity.evaluate()
    assert score.criteria[0].criterion_id == "C1"


def test_maturity_score_average_with_mixed_levels():
    kernel = CompanyKernel()
    for criterion in kernel.maturity.list_criteria()[:6]:
        kernel.maturity.submit_evidence(criterion.criterion_id, MaturityLevel.PASS, ["x"])
    for criterion in kernel.maturity.list_criteria()[6:]:
        kernel.maturity.submit_evidence(criterion.criterion_id, MaturityLevel.PARTIAL, ["y"])
    score = kernel.maturity.evaluate()
    assert score.average == (6 + 3) / 12


def test_maturity_unknown_criterion_raises():
    kernel = CompanyKernel()
    with pytest.raises(KeyError):
        kernel.maturity.get("C99")


def test_maturity_replaces_model_criterion_with_evidence():
    kernel = CompanyKernel()
    kernel.maturity.submit_evidence("C12", MaturityLevel.PASS, ["model-versioned", "vendor-independent", "lineage-preserved"])
    score = kernel.maturity.evaluate()
    assert not score.overall_10_of_10
    c12 = next(c for c in score.criteria if c.criterion_id == "C12")
    assert c12.level == MaturityLevel.PASS
