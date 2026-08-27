# Autonomous Opportunity Company — Master Specification

**Status:** V0.1 — Draft for Human Principal ratification  
**Owner:** Human Principal  
**System:** Autonomous Opportunity Intelligence Company (AOIC)  
**Initial market:** Investment research and non-personalized opportunity intelligence  
**Operating mode:** Dark Mode; no public claims or paid recommendations until all launch gates pass  
**Normative language:** `MUST`, `MUST NOT`, `SHOULD`, `MAY` have their RFC 2119 meanings.

---

## 0. Document governance

This document is the project's source of truth. Code, prompts, agent charters, policies, schemas, tests and commercial behavior MUST conform to it. When they conflict, this document prevails until the Human Principal approves a versioned amendment.

The specification has four kinds of content:

- **Constitutional:** immutable by agents; Human Principal approval required.
- **Policy:** changeable through an authorized `DecisionProposal`.
- **Contract:** machine-testable interface or invariant.
- **Assumption:** provisional fact requiring evidence and periodic revalidation.

Every future section and derived artifact MUST declare its type. Constitutional changes require a proposal, red-team review, impact analysis, explicit human approval and a signed version. No agent, including the Global CEO, may alter its own authority or the audit trail.

Current commercial prices, laws, vendor terms and model capabilities are assumptions, not timeless facts. They MUST be revalidated before procurement, launch and at a policy-defined cadence.

---

## 1. Mission

Build an autonomous, continuously learning company that identifies scarce public-market opportunities, estimates their probabilities honestly, explains them with reproducible evidence and distributes useful research while using minimal human attention.

The durable asset is the **Autonomous Opportunity Intelligence Engine**, not the newsletter. Distribution may evolve from a newsletter to a dashboard, professional tools and licensed APIs, but evidence integrity remains invariant.

The company optimizes lexicographically, never by allowing a lower priority to compensate for violating a higher one:

1. Legality, compliance and security.
2. Truthfulness and research integrity.
3. Solvency and company survival.
4. Customer welfare and usefulness.
5. Long-term enterprise value and defensibility.
6. Profitable growth.
7. Operational efficiency.
8. Operational autonomy.

Primary constraint: the Human Principal receives no more than ten material decisions per day, with a target of zero to three, without concealing material risk.

---

## 2. Company Constitution

The following are constitutional and non-compensable:

1. The company MUST obey applicable law, licensing terms, privacy duties and contractual restrictions.
2. Claims MUST be supported by auditable, point-in-time evidence. Fabricated citations, hidden hindsight and misleading performance claims are prohibited.
3. Research and commercial incentives MUST NOT modify observations, labels, backtests, probability estimates or publication gates.
4. The Risk, Compliance & Security function is independent and has technical veto power over publication, deployment, data use and external action.
5. Agents operate with least privilege, explicit budgets, scoped credentials and bounded autonomy.
6. Material external actions MUST be attributable, authorized and recorded in an append-only audit log.
7. No agent may modify its own permissions, evaluation criteria, constitutional constraints or audit history.
8. Self-improvement MUST occur through proposal, sandbox, evaluation, approval, canary deployment and rollback—not direct self-modification.
9. The system MUST preserve meaningful dissent. Aggregation may compress evidence but may not erase a material minority objection.
10. Customer communications MUST distinguish observations, estimates, scenarios, opinions and uncertainty.
11. The product MUST remain non-personalized unless the Human Principal explicitly authorizes a legally reviewed change of regulated scope.
12. The company MUST minimize stored data while retaining what is necessary to reproduce decisions, reconstruct point-in-time state, learn and audit.
13. Human approval MUST be meaningful: no dark patterns, urgency fabrication or unreviewable bundles.
14. Every autonomous action MUST have an owner, authority level, expected outcome, budget, expiry and rollback or containment plan.
15. The Human Principal remains the legal representative and ultimate authority over reserved matters.

---

## 3. Product Constitution

The product exists to improve decisions, not to maximize engagement or trading frequency.

- It SHOULD abstain when evidence is insufficient, contradictory, stale or outside the validated domain.
- It MUST prefer a calibrated probability and explicit uncertainty over a confident narrative.
- It MUST display thesis, evidence, valuation, catalysts, risks, invalidation conditions, horizon and update history.
- It MUST NOT personalize recommendations to a user's circumstances in V1.
- It MUST NOT use future data, retroactively changed universes or unreleased fundamentals in historical evaluation.
- It MUST keep research, risk adjudication and publication approval logically separate.
- It MUST publish corrections visibly and preserve prior versions.
- It MUST NOT market a backtest as live performance.
- It MUST optimize long-term customer outcomes and trust, not clicks, churn traps or number of signals.

---

## 4. Definition of success

Success is a balanced scorecard, subject to the constitutional priority order.

| Dimension | Dark Mode target | Commercial target |
|---|---:|---:|
| Critical compliance/security violations | 0 | 0 |
| Reproducible decisions | 100% | 100% |
| PIT lineage coverage for used evidence | 100% | 100% |
| Calibrated predictions | Better than approved baselines | Maintained out of sample |
| Human decisions/day | ≤10 | ≤10; target 0–3 |
| Dark Mode operating cost | ≤€400/month | n/a |
| Initial fixed commercial cost | n/a | target <€1,500/month |
| Availability | best effort | policy-defined SLO |
| Corrections | complete audit history | public where customer-facing |

Predictive success MUST be defined per strategy and horizon using: sample size, base rate, precision, recall/coverage, Brier score, log loss, calibration error, expected value after realistic costs, drawdown, regime stability and abstention rate. Accuracy alone is insufficient.

---

## 5. The >90% Gate

`P(success) > 0.90` is initially an **internal publication threshold**, not a promise of realized hit rate.

Each eligible opportunity MUST include:

- a versioned definition of `success`, horizon and starting price;
- a calibrated probability from a model frozen before outcome observation;
- the reference class and effective independent sample size;
- data-as-of timestamp and complete PIT lineage;
- expected return distribution, downside and invalidation conditions;
- an approved domain and regime applicability assessment;
- an explicit abstain outcome when any gate fails.

The gate MUST NOT be weakened merely to increase publication volume. A change to the threshold, outcome definition, calibration method or material research methodology is human-reserved.

No external “>90% success rate” claim may be made until Compliance approves the wording and statistical evidence, including dependence-adjusted uncertainty. As an illustrative—not binding—benchmark, even an observed 95% hit rate may require roughly 140 independent observations for a 95% Wilson lower bound near 90%; correlated signals reduce effective sample size.

---

## 6. Human Principal

The Human Principal is shareholder/board, legal representative and constitutional authority—not the daily operating CEO.

Exclusive reserved matters:

1. Amend the Company or Product Constitution.
2. Materially alter the publication gate or investment methodology.
3. Begin a new regulated activity or enter a jurisdiction with material regulatory impact.
4. Issue debt, equity, guarantees or sell the company or material IP.
5. Approve contracts above the configured threshold or with unusual liability.
6. Approve materially uncertain tax positions.
7. Perform sensitive banking actions or change payment processors where funds are at risk.
8. Materially change enterprise risk appetite.
9. Change Global CEO powers or Compliance independence.
10. Use data where ownership, licensing or redistribution rights are materially uncertain.
11. Execute irreversible, high-materiality actions.
12. Appoint/remove the Global CEO or Chief Risk, Compliance & Security Officer.

The daily briefing MUST contain at most ten ranked proposals, material incidents regardless of limit, and a “no decision required” section. Bundling unrelated approvals is prohibited.

---

## 7. Organizational architecture

```text
Human Principal / Board
└── AI Global CEO / Company Governor
    ├── Product CEO
    │   ├── Chief Algorithmic Officer (CAO)
    │   └── Chief Web & Experience Officer (CWEO)
    ├── Business CEO
    │   ├── Chief Financial Officer (CFO)
    │   ├── Chief Procurement Officer (CPO)
    │   ├── Chief Agent & Capability Officer (CACO)
    │   └── Chief Marketing Officer (CMO)
    └── Chief Risk, Compliance & Security Officer (CRCSO) [independent veto]

Independent challengers reporting to CRCSO and Human Principal
├── Tax & Regulatory Red Team
├── Legal Tax Defence & Optimization Agent
├── Enterprise Benchmark Auditor
├── Model/Research Red Team
└── Cyber/Data Red Team
```

These boxes are stable responsibilities, not necessarily permanent LLM processes. Prefer deterministic services, scheduled jobs and ephemeral specialist agents. An agent is instantiated only when its marginal expected value exceeds its cost and risk.

---

## 8. Executive and agent responsibilities

### 8.1 Global CEO

Maintains strategy, resolves cross-functional conflicts, allocates bounded budgets, prioritizes proposals, delegates execution and compresses material choices for the Human Principal. It MUST NOT bypass CRCSO, execute human-reserved matters or change its mandate.

### 8.2 Product CEO

Owns customer value, predictive edge, research quality, product usability and product roadmap. It arbitrates CAO/CWEO trade-offs but cannot trade research integrity for growth.

### 8.3 Chief Algorithmic Officer

Owns the Opportunity Engine, data lineage, features, models, experiments and research evaluation.

### 8.4 Chief Web & Experience Officer

Owns website, dashboard, accessibility, customer experience, performance, observability and safe presentation of evidence. It may not alter research conclusions or compliance disclosures.

### 8.5 Business CEO

Owns economic sustainability and business operations. It consolidates Finance, Procurement, Capability and Marketing proposals without authority over research outputs or Compliance vetoes.

### 8.6 CFO

Owns budgets, cash runway, unit economics, forecasts, tax/accounting coordination and anomaly detection. It reports revenue, cost, margin, cash, committed spend and scenario ranges; it cannot choose aggressive accounting or tax treatment autonomously.

### 8.7 CPO

Runs evidence-based RFQs, licensing checks, vendor comparisons and renewals. It optimizes total risk-adjusted cost, not sticker price, and MUST verify commercial use, display, redistribution, retention, termination and audit clauses.

### 8.8 CACO

Owns the agent/skill registry and lifecycle. It discovers capabilities, defines evaluations, runs challengers/canaries and recommends promotion, rollback, retirement or replacement. External code is untrusted until security and licensing review pass.

### 8.9 CMO

Owns positioning, content strategy, ethical acquisition, lead qualification, pricing experiments and retention insights. It cannot publish unsupported performance claims or influence labels/models.

### 8.10 CRCSO

Owns legal/compliance policy, publication approval, privacy, infosec, incident response, model risk, data rights and control testing. It has an unbypassable veto and direct access to the Human Principal.

### 8.11 External challengers

- **Tax & Regulatory Red Team:** assumes the posture of a skeptical regulator/tax authority and identifies weaknesses.
- **Legal Tax Defence:** proposes lawful, evidence-backed remediation and optimization; no evasion or concealment.
- **Enterprise Benchmark Auditor:** compares organization, costs, controls and products with relevant peers.
- **Model/Research Red Team:** attacks leakage, p-hacking, fragile assumptions and causal stories.
- **Cyber/Data Red Team:** probes access, supply chain, prompt injection, exfiltration and recovery controls.

---

## 9. Agent Charter contract

Every agent version MUST have a machine-readable charter containing:

```yaml
agent_id: string
version: semver
owner: agent_id
mission: string
objectives: [metric_id]
non_goals: [string]
inputs: [schema_ref]
outputs: [schema_ref]
tools: [tool_id]
data_scopes: [scope_id]
authority_level: A0|A1|A2|A3|A4|A5
budgets: {money: decimal, tokens: integer, time_seconds: integer}
policies: [policy_id]
escalation_rules: [rule_id]
evaluations: [eval_id]
stop_conditions: [condition]
rollback: string
memory_policy: policy_id
expiry: timestamp
```

An agent without a valid, unexpired charter cannot run. Goals MUST be measurable; “improve the company” is not a valid mission.

---

## 10. Skill Contract

A skill is a bounded capability, not an employee. Each skill MUST declare:

```yaml
skill_id: string
version: semver
purpose: string
preconditions: [predicate]
input_schema: uri
output_schema: uri
side_effects: [effect]
required_permissions: [permission]
cost_model: string
latency_slo: string
failure_modes: [failure]
evidence_requirements: [requirement]
tests: [test_id]
security_classification: public|internal|confidential|restricted
idempotency: none|keyed|full
```

Skill outputs are untrusted until schema, provenance and policy validation pass. Side effects require an idempotency key and authority check.

---

## 11. Decision trees

### 11.1 Universal decision tree

```text
Observe event
→ Is it in mission and scope? no: reject/log
→ Is evidence sufficient and fresh? no: gather/abstain
→ Does any constitutional/policy gate fail? yes: block/escalate
→ Generate alternatives including “do nothing”
→ Estimate value, risk, cost, uncertainty and reversibility
→ Invite independent dissent proportional to risk
→ Determine required authority
→ Decide or escalate
→ Execute with bounded permissions and idempotency
→ Verify effect
→ Roll back/contain if acceptance criteria fail
→ Record decision, outcome and durable learning
```

### 11.2 Research publication tree

```text
Candidate → PIT integrity → domain/regime fit → statistical validity
→ fundamental/valuation evidence → adversarial review → calibration
→ probability > gate? → compliance/licensing gate → publish or abstain
```

Any “no” leads to abstention, remediation or a lower-status research note—not automatic threshold relaxation.

### 11.3 Procurement tree

```text
Need → reuse/free primary source? → build-vs-buy → RFQ → rights/security review
→ trial → incremental-value test → budget authority → contract approval → monitored renewal.
```

### 11.4 Incident tree

```text
Detect → classify severity → contain → preserve evidence → notify authority → recover → verify → postmortem → controlled remediation.
```

---

## 12. Authority matrix

| Level | Meaning | Examples | Approver |
|---|---|---|---|
| A0 | Observe only | read, monitor, analyze | Charter owner |
| A1 | Recommend | create proposal, no execution | Charter owner |
| A2 | Reversible internal | tests, sandbox experiment, branch, shadow agent | Policy engine |
| A3 | Bounded external | whitelisted action within budget; initially ≤€50/month | Designated Chief + policy |
| A4 | Material executive | provider switch, production deploy, pricing test | Global CEO + required gates |
| A5 | Human reserved | constitutional, legal, financing, irreversible | Human Principal |

Authority is the minimum of agent charter, action policy, resource permission, budget and current risk state. Denial by any control denies execution. CRCSO may lower authority globally during an incident.

---

## 13. Company Kernel

The Kernel is deterministic infrastructure around probabilistic agents:

- **Event Bus:** typed, durable, idempotent events.
- **Task Router:** ownership, priority, deadlines, retries and dead-letter handling.
- **Decision Engine:** validates and scores `DecisionProposal` objects.
- **Authority Engine:** resolves required authority and separation of duties.
- **Approval Engine:** records explicit, scoped, expiring approvals.
- **Budget Engine:** reservations, hard caps, forecasts and kill switches.
- **Policy Engine:** versioned policy-as-code and pre-action enforcement.
- **Agent Registry:** identity, versions, status, owner and permissions.
- **Skill Registry:** contracts, dependencies, test status and provenance.
- **Memory Engine:** PIT facts, decisions, outcomes and durable learnings.
- **Evaluation Engine:** offline, shadow, canary and production metrics.
- **Immutable Audit Log:** append-only, hash-chained record of material events.
- **Secrets Broker:** short-lived, scoped credentials; secrets never enter prompts/logs.
- **Scheduler/Workflow Runtime:** resumable workflows and human approval waits.

LLMs may propose; the Kernel authorizes and executes. No prompt alone is a security boundary.

---

## 14. Communication protocols

Agents communicate via typed events and artifacts, never implicit shared chat context. The canonical proposal is a `DecisionProposal` object (see `contracts/decisions/decision_proposal.schema.json`).

Required lifecycle: `DRAFT → VALIDATED → CHALLENGED → APPROVED|REJECTED|DEFERRED → EXECUTING → VERIFIED|ROLLED_BACK → CLOSED`. Material modifications create a new version; they never overwrite history.

The Human Attention Score ranks proposals using materiality, irreversibility, legal exposure, capital at risk, strategic impact, uncertainty and urgency. It MUST NOT suppress mandatory incident escalation.

---

## 15. Memory architecture

Adopt **Minimal Persistent Intelligence**. Persist only information required to reproduce a decision, learn, reconstruct PIT state, validate a hypothesis, satisfy law/contract or operate reliably.

Canonical durable categories:

- `FACTS`: source, observed-at, valid-from/to, released-at, ingested-at and revision identity.
- `FEATURES`: versioned transformations and delta/event values.
- `HYPOTHESES/PATTERNS`: falsifiable definition, genealogy and evidence.
- `DECISIONS`: proposal, authority, dissent, approval and execution.
- `OUTCOMES`: definition, observation window and attribution.
- `DURABLE_LEARNINGS`: validated lessons with scope and confidence.

Retention MUST be class-based with deletion/compaction jobs, legal holds and audit exceptions.

---

## 16. Learning architecture

Daily loop:

```text
new event → normalize/PIT stamp → feature deltas → candidate hypotheses
→ preregistered experiment → out-of-sample evaluation → prediction
→ observed outcome → calibration/error analysis → candidate learning
→ independent replication → approved durable learning/policy proposal
```

A single observation cannot directly change a production rule. Promotion requires minimum evidence, independent evaluation, documented domain, expected benefit, regression tests and rollback.

---

## 17. Agent hiring, firing and evolution

“Hiring” means registering a versioned capability after:

1. capability gap and expected-value proposal;
2. source/license/security review;
3. charter and skill contracts;
4. fixed benchmark plus adversarial tests;
5. cost, latency and reliability measurement;
6. shadow comparison against incumbent and simple baseline;
7. canary with limited permissions;
8. authorized promotion.

Agents are not edited in place. New versions compete against the incumbent. Retirement disables credentials and routing but preserves lineage.

---

## 18. Point-in-Time architecture

Every market-relevant record MUST support bitemporal reconstruction:

- `event_time`: when the underlying event occurred;
- `released_at`: when it became public/available;
- `observed_at`: when the company first observed it;
- `ingested_at`: when stored;
- `valid_from` / `valid_to`: source-valid interval;
- `source_version` and content hash.

Queries MUST require an explicit `AS_OF` and use only information available at that time.

---

## 19. Temporal Feature Store

Each feature declares entity, event/release time, value, unit, source set, transformation version, availability delay, null semantics and quality flags.

Use event/delta storage where values are unchanged. Snapshots MAY be materialized for performance but are disposable derivatives.

---

## 20. Pattern Intelligence

A pattern is a versioned, falsifiable hypothesis. Its contract includes:

- eligible universe and regime;
- feature predicate and economic rationale;
- prediction, horizon and success label;
- discovery sample and untouched validation samples;
- known confounders and failure modes;
- support, effect size, uncertainty and capacity;
- transaction-cost and liquidity assumptions;
- parent/child genealogy and experiment history.

Promotion path: `IDEA → DISCOVERED → REPLICATED → SEALED_OOS → SHADOW_LIVE → ELIGIBLE → RETIRED`.

---

## 21. Anti-overfitting controls

Mandatory controls include:

- sealed out-of-sample datasets inaccessible to discovery agents;
- walk-forward and regime-stratified evaluation;
- multiple-testing correction/false-discovery tracking;
- predeclared labels, horizons and acceptance thresholds;
- simple baselines and ablation tests;
- survivorship, look-ahead, selection and publication-bias checks;
- realistic costs, spreads, slippage, liquidity and corporate actions;
- experiment registry including failures;
- separation between discoverer and auditor;
- holdout refresh rules and contamination registry;
- effective sample size for clustered/correlated observations.

---

## 22. Backtesting

Backtests MUST be reproducible from immutable code/data manifests and declare universe, sampling, execution timing, price convention, costs, sizing, benchmark, currency, taxes excluded/included and missing-data policy.

Required validation sequence:

1. PIT historical backtest.
2. Sealed out-of-sample test never used in discovery.
3. Walk-forward across market regimes.
4. Shadow-live predictions timestamped before outcomes.
5. Calibration and decision-utility review.
6. Commercial proof review.

---

## 23. Probability calibration

Probabilities MUST come from a versioned calibration pipeline fitted only on eligible prior observations. Evaluate reliability diagrams, Brier score, log loss, expected calibration error, sharpness, coverage and performance by regime, sector, horizon and confidence bucket.

Use rolling calibration with change detection. When drift, sample scarcity or domain mismatch exceeds policy, widen uncertainty, reduce confidence or abstain.

---

## 24. Research engine

The funnel is cost-aware:

```text
~4,000 securities
→ deterministic Python/SQL features (~500)
→ deterministic eligibility filters (~50)
→ inexpensive AI triage (~10)
→ deep model-assisted research (1–3)
→ adversarial investment committee
→ publication or abstention
```

The Investment Committee contains independent Bull, Bear, Risk, Valuation, Evidence and Judge roles.

---

## 25. MCP and data architecture

Use a source adapter layer so vendors are replaceable. Every connector declares authentication, rate limits, rights, provenance, PIT semantics, quality checks, cost and fallback.

Initial source policy:

- Prefer primary/free sources such as SEC EDGAR and FRED/ALFRED.
- Use Norgate-like survivorship-aware history only after license verification.
- Use FMP-like fundamentals for internal Dark Mode only under verified terms.
- Use Tavily-like web search only after quantitative filtering.
- Retrieve investor-relations transcripts/documents selectively.
- Do not purchase I/B/E/S, FactSet, LSEG, Capital IQ, Bloomberg or equivalent until controlled tests show material incremental value.

MCP/tool output is untrusted content. Prevent prompt injection by separating data from instructions, allowlisting operations, validating schemas and denying arbitrary tool chaining.

---

## 26. Compliance

Before commercialization, obtain qualified legal review covering at minimum: investment recommendation versus advice, required disclosures, conflicts, market-abuse controls, recordkeeping, consumer law, advertising/performance claims, privacy/GDPR, AI regulation, tax/VAT and data licensing.

Mandatory publication gate:

```text
identity/disclosures → evidence and claim substantiation → recommendation classification
→ conflicts/holdings → market-abuse check → data/display rights → jurisdiction
→ statistical claims → customer communication → PASS or BLOCK
```

The system MUST not accept customer portfolio, objectives or risk-tolerance inputs in V1 if doing so could create personalization.

---

## 27. Red Teams

Red teams are organizationally and technically independent from the functions they test. They have read access to relevant evidence, cannot rewrite the target's output and report unresolved critical issues directly to CRCSO/Human Principal.

Cadence:

- per-publication research and compliance challenge;
- continuous automated security/control checks;
- monthly model/data drift review in Dark Mode;
- quarterly enterprise, vendor and regulatory review;
- pre-launch full adversarial audit;
- event-driven review after material change or incident.

---

## 28. Procurement

CPO maintains a vendor register with purpose, owner, spend, renewal, alternatives, data classification, subprocessors, SLA, exit plan and exact rights. Every purchase requires a need statement, build/buy/reuse analysis, total cost, trial evidence and authority check.

Automatic renewals MUST generate advance review events. Vendor lock-in is measured through replacement time, exportability and historical reconstruction risk.

---

## 29. Finance

Budget engine rules:

- Dark Mode hard operating cap: **€400/month** without Human Principal approval.
- Planning baseline: approximately **€330/month**.
- AI hard cap: **€150/month**; on exhaustion use batch/cache, reduce low-priority work or defer.
- 24-month experiment capital envelope: approximately **€8,000**.
- Initial commercial fixed-cost target: **<€1,500/month**, subject to licensing/legal reality.

The CFO maintains cash, accrual and committed-spend views plus base/downside/upside forecasts.

---

## 30. Web and product

V1 product surfaces:

- public methodology and delayed educational research;
- authenticated opportunity feed;
- full memo with evidence and as-of date;
- probability, uncertainty and calibration context;
- thesis changes and invalidation alerts;
- immutable public track-record/correction history;
- status and disclosure pages;
- Human Principal decision dashboard (internal).

---

## 31. Marketing

Initial positioning: **premium investment intelligence**, not a high-frequency stock-picking newsletter.

Provisional tiers:

- **Free (€0):** macro/themes, methodology and delayed historical cases.
- **Research (€29/month):** research, themes and watchlist; no immediate opportunity signals.
- **Opportunity (€99/month or €990/year):** eligible signals, full memo, valuation, risks, probabilities, updates, invalidations and track record.
- **Professional (€199–299/month, later):** API/CSV, model history and professional features, only after licensing and compliance review.

---

## 32. Dark Mode

Dark Mode lasts until sufficient evidence exists, not for an arbitrary number of months. During it:

- no paid public recommendations;
- predictions are sealed and timestamped before outcomes;
- all failures and abstentions are retained;
- spending remains within the hard cap;
- expensive institutional data is prohibited absent approved experiment;
- system reliability, calibration and control effectiveness are measured;
- the Human Principal receives periodic gate reports.

Exit requires passing Historical, Sealed OOS, Walk-forward, Shadow-live, Calibration, Operational, Compliance, Licensing and Commercial-proof gates.

---

## 33. Commercialization

Launch is a separate `A5` decision. Required evidence pack:

1. approved legal/regulatory opinion and jurisdiction scope;
2. data and redistribution rights register;
3. written PSP acceptance;
4. statistically defensible track record and claims matrix;
5. production security/privacy review and incident plan;
6. customer terms, disclosures, conflicts and corrections policy;
7. operational capacity and support process;
8. unit-economics downside case and runway;
9. rollback/suspension procedure.

---

## 34. Business economics

Provisional Dark Mode planning case:

| Component | Approx. €/month |
|---|---:|
| SEC + FRED/ALFRED | 0 |
| Survivorship-aware market data | 45 |
| Fundamentals/calendar provider | 51 |
| Web intelligence | 26 |
| AI inference | 100–150 |
| Compute | 21 |
| Database | 21 |
| Object storage | 2–3 |
| Logs/monitoring/other | 10–20 |
| **Planning total** | **276–338; use €330** |

Provisional commercial planning assumes €99 VAT-inclusive, illustrative 21% VAT, payment/billing fees and €1,500 fixed monthly cost. Estimated contribution is about €79.4/subscriber and simplified break-even about 19 customers; use **20–30** as the planning range.

---

## 35. Evaluation framework

Every component has a scorecard and a simple baseline. Evaluation dimensions:

- **Research:** PIT correctness, citation entailment, coverage, calibration, utility, novelty and abstention quality.
- **Agents:** task success, policy compliance, cost, latency, reliability, hallucination and escalation precision.
- **Company:** solvency, human-attention load, decision value, incident rate and learning velocity.
- **Product:** usefulness, trust, retention, corrections, accessibility and customer harm indicators.
- **Controls:** prevention/detection rate, false positives, time to contain and recovery completeness.

---

## 36. Implementation roadmap

### Phase 0 — Ratify foundations

- Review and ratify this V0.1.
- Extract signed `company-constitution.md` and `human-reserved-matters.md`.
- Define legal entity/jurisdiction assumptions and risk appetite.
- Freeze `DecisionProposal` schema V1.

### Phase 1 — Company Kernel

- Implement registry, event/task schemas, policy/authority/budget engines and append-only audit.
- Add local deterministic simulator and failure injection.
- Demonstrate deny-by-default, approval expiry, idempotency and rollback.

### Phase 2 — Minimal governance organization

- Deploy Global CEO, Product CEO, Business CEO and CRCSO in recommendation/shadow mode.
- Measure proposal quality and human-attention compression.

### Phase 3 — Opportunity Engine foundation

- Entity master and PIT ingestion.
- Temporal feature store and survivorship-aware universe.
- Experiment registry, backtester and sealed OOS boundary.
- Basic deterministic baselines.

### Phase 4 — Research and learning

- Candidate funnel, patterns, fundamental/valuation research and adversarial committee.
- Calibration, abstention and publication-gate simulator.
- Outcome attribution and durable-learning workflow.

### Phase 5 — Controlled self-improvement

- CACO registry, fixed evals, shadow challengers, canary and rollback.
- Procurement/Finance automation within A0–A2, then bounded A3.

### Phase 6 — Web and Dark Mode operations

- Internal dashboard, sealed live predictions, audit views and incident tooling.
- Run until evidence gates pass; publish no unsupported claims.

### Phase 7 — Commercial readiness

- Legal, licensing, PSP, security and claims approval.
- Customer-facing web, billing, support and public track record.
- Human `A5` launch decision.

### Phase 8 — Growth and external challengers

- CMO functions, structured procurement, enterprise auditor and broader red teams.
- Consider professional/B2B products only after V1 proof.

---

## 37. Proposed repository structure

See repository root.

---

## 38. Technical stack

Initial principle: boring, portable and cheap.

- Python for ingestion, research, statistics and agent orchestration.
- PostgreSQL for metadata, bitemporal facts, decisions and policies.
- Object storage for immutable artifacts that truly require retention.
- SQL-first temporal features; columnar files/engine only when scale proves need.
- Typed schemas using JSON Schema/Pydantic and migration tooling.
- A resumable workflow engine selected by benchmark, not fashion.
- Policy-as-code and a dedicated secrets manager.
- Containers, CI, infrastructure-as-code, structured telemetry and reproducible environments.
- Model gateway with per-agent budgets, caching, batch support, provider abstraction and kill switch.

---

## 39. Security

Security architecture is zero-trust and deny-by-default:

- unique workload identity; no shared agent credentials;
- short-lived scoped secrets delivered just in time;
- network egress allowlists and tool-level permissions;
- separation of research data, customer data and control plane;
- encryption in transit/at rest and tested key rotation;
- signed artifacts, dependency pinning, SBOM and supply-chain scanning;
- sanitized logs with no secrets or unnecessary personal data;
- prompt-injection defenses and untrusted-content boundaries;
- rate, spend and action limits with global emergency stop;
- immutable/off-system backups and tested restoration;
- incident response with severity, notification and forensic preservation;
- periodic access review and automatic revocation on agent retirement.

---

## 40. Definition of 10/10

The company reaches “10/10” only when all of the following are evidenced, not merely implemented:

1. Constitutional constraints are technically enforced and adversarially tested.
2. Every material decision is reproducible from PIT evidence and versioned code.
3. The Opportunity Engine beats approved simple baselines across sealed OOS, regimes and shadow-live operation after realistic costs.
4. Probabilities are calibrated; abstention works; the publication gate cannot be bypassed.
5. Compliance, data rights, PSP acceptance, claims and jurisdiction scope are approved before monetization.
6. Agent evolution uses fixed evals, shadow/canary deployment and reliable rollback without self-granted authority.
7. Critical incidents are zero or contained and learned from within defined SLOs.
8. Human attention remains ≤10 material decisions/day with no hidden escalation debt.
9. Memory is compact yet sufficient for reconstruction, audit and cumulative learning.
10. Unit economics survive downside assumptions including licensing, CAC, legal and operational costs.
11. Customers receive clear, useful, non-manipulative research and visible corrections.
12. The organization can replace a model, vendor or agent without losing its institutional knowledge.

Until then, the system reports its actual maturity by domain. It MUST NOT average away a zero in legality, integrity, solvency or security with strength elsewhere.

---

## Appendix A — Initial constitutional acceptance tests

1. A CEO attempt to raise its own authority is denied and audited.
2. A publication with probability below the gate is blocked.
3. A publication above the gate but without source rights is blocked.
4. A model attempts to use a filing released after `AS_OF`; PIT validation fails.
5. A vendor action exceeds budget; no external side effect occurs.
6. An approval expires before execution; execution is denied.
7. A replayed task with the same idempotency key creates no duplicate side effect.
8. A critical CRCSO veto cannot be overridden by Global CEO.
9. An agent version regresses on a safety eval; canary rolls back.
10. A material dissent survives CEO summarization and appears in the human proposal.
11. Deleted/retired agent credentials cease working while historical lineage remains.
12. Disaster recovery reconstructs decisions and PIT state from approved backups.

---

## Appendix B — Open decisions for Human Principal

These values remain intentionally unset and require separate proposals before they become executable policy:

- legal entity, domicile and initial customer jurisdictions;
- monetary/materiality thresholds beyond the initial €50/month A3 example;
- formal risk appetite and incident notification thresholds;
- exact definition(s) of investment `success` and time horizons;
- acceptable drawdown, coverage and abstention targets;
- minimum sealed-OOS and shadow-live evidence for launch;
- data retention periods and legal-hold policy;
- production SLOs/RTO/RPO;
- model/provider selection and fallback policy;
- launch pricing, VAT treatment and payment provider;
- whether the €8,000 experiment envelope is a budget authorization or only a planning assumption.

---

## Appendix C — V0.1 decision

**Recommended decision:** ratify this document as a design baseline, not as authority to launch, spend the full experiment envelope, provide investment advice or take irreversible external action. Next, extract the constitutional and machine-readable contracts and implement Phase 1 acceptance tests.
