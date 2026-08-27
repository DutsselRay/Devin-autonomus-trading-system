# Autonomous Opportunity Intelligence Company (AOIC)

This repository contains the Phase 1 implementation of the Autonomous Opportunity Company, starting with the **Company Kernel** and the constitutional acceptance tests from Appendix A of the master specification.

## Structure

- `AUTONOMOUS_OPPORTUNITY_COMPANY_MASTER_SPEC.md` — source-of-truth specification
- `company/` — constitutional documents and agent charters
- `contracts/` — JSON Schema contracts for decisions, events, agents and skills
- `company-kernel/aoic_kernel/` — deterministic kernel engines
- `opportunity-engine/` — placeholder for Phase 3+ research engines
- `tests/` — constitutional acceptance tests

## Quick start

```bash
pip install -e .
python3 -m pytest tests/test_constitutional_acceptance.py -v
```

## Status

Phase 1 complete:
- Repository skeleton per Section 37
- Normative contracts (DecisionProposal, agent charter, skill contract, event, PIT record)
- Company Kernel: Event Bus, Task Router, Decision Engine, Authority Engine, Approval Engine, Budget Engine, Policy Engine, Registries, Memory Engine, Evaluation Engine, Audit Log
- 12/12 Appendix A acceptance tests passing

## Next steps

- Phase 2: minimal governance organization (shadow-mode CEO agents)
- Phase 3: Opportunity Engine foundation (entity master, PIT ingestion, temporal feature store)
- Phase 4: research and learning funnel

See `AUTONOMOUS_OPPORTUNITY_COMPANY_MASTER_SPEC.md` for full governance, architecture and roadmap.
