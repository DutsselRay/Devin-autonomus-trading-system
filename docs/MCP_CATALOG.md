# MCP Server Catalog for a Fully Autonomous AOIC

This document lists the Model Context Protocol (MCP) servers and external capabilities required for the AOIC to operate as a complete autonomous system. All integrations are gated by the `SourceAdapter`, `VendorRegister`, `ModelGateway`, `CommercialReadiness` and `B2BGate` mechanisms and run in shadow mode until explicitly approved.

## 1. Market data and opportunity sources

| MCP / API | Purpose | Rights and cost checks | Quality checks |
|---|---|---|---|
| SEC EDGAR (primary) | Filings, 10-K/Q, ownership | Public domain | PIT filing date, schema validation |
| FRED / ALFRED (primary) | Macro-economic time series | Public | Observation date, revision status |
| Norgate Data-like vendor | Survivorship-aware price history | Commercial license, redistribution rights | Split/dividend adjustment, delisted metadata |
| Financial Modeling Prep-like | Fundamentals, earnings calendars | Commercial terms, display rights | Delay verification, field completeness |
| I/B/E/S, FactSet, LSEG, Capital IQ, Bloomberg | Advanced estimates and institutional data | Purchase only after material-value proof | License scope, subprocessor list |
| Web search (Tavily-like) | News, transcripts, public documents | Respect robots, copyright, terms | Source attribution, date extraction |
| Investor relations transcript feeds | Earnings calls, guidance | Public or licensed | Speaker identification, material statements |

## 2. Execution and brokerage

| MCP / API | Purpose | Authority gate | Controls |
|---|---|---|---|
| Broker / exchange order API | Place/modify/cancel orders | A3/A4 approval, budget, policy | Kill switch, position limits, pre-trade compliance |
| Clearing and settlement API | Confirm trades, settlement | Read-only in shadow mode | Reconciliation, unmatched-trade alerts |
| Custodian / portfolio API | Holdings, cash, margin | A2/A3 read access | PIT snapshot, multi-source reconciliation |
| Prime brokerage / PB API | Financing, locates, shorts | A4, legal pre-approval | Cost attribution, exposure limits |

## 3. Model providers and inference

| Provider type | Use case | Gateway controls |
|---|---|---|
| Frontier LLM (OpenAI, Anthropic, Google, etc.) | Research summarization, committee drafts, report generation | Per-agent budget, RPM, caching, kill switch |
| Open-source / self-hosted models | Sensitive analysis, zero-external-data workflows | On-prem routing, batch support, version pinning |
| Embedding / RAG providers | Memory, semantic search, retrieval | Cost per 1k tokens, cache lifetime |
| Specialized finance models | Earnings call sentiment, numeric extraction | Adversarial eval, calibration check |
| Coding / agent execution models | Code generation, tool use, skill execution | Sandboxed execution, no direct external action |

## 4. Compliance, legal and risk

| MCP / API | Purpose | Gate |
|---|---|---|
| Legal research service | Jurisdiction, advice vs. recommendation boundaries | Legal review gate |
| Sanctions / PEP / KYC API | Counterparty and customer screening | AML/compliance gate |
| Market-abuse surveillance API | Wash trade, layering, insider-list checks | Pre-trade, post-trade |
| Regulatory filing API | Notify regulators where required | A5 human approval |
| Trademark / IP search | Name, brand, copyright checks | Claims review gate |

## 5. Customer and commercial

| MCP / API | Purpose | Gate |
|---|---|---|
| Payment provider (Stripe-like) | Subscriptions, invoicing, VAT | PSP gate |
| CRM | Leads, support tickets, customer communication | GDPR/privacy gate |
| Email / messaging | Transactional and marketing comms | Unsubscribe, non-manipulative copy gate |
| Authentication / identity | Customer accounts, SSO, MFA | Security gate |

## 6. Infrastructure and operations

| MCP / API | Purpose | Controls |
|---|---|---|
| Cloud compute / container orchestration | Workload execution | Spend budget, autoscaling limits |
| Secret manager | API keys, credentials | Just-in-time delivery, rotation, audit |
| Object storage | Immutable artifacts, backups | Encryption, retention, legal hold |
| Postgres / metadata database | Bitemporal facts, decisions, policies | Encryption, access review, backups |
| CI / CD and artifact registry | Reproducible builds, SBOM | Signed artifacts, dependency pinning |
| Telemetry and observability | Logs, metrics, tracing | Sanitized logs, no secrets, cost budget |

## 7. Security and red-team automation

| MCP / API | Purpose | Cadence |
|---|---|---|
| Vulnerability scanner | Dependency and container CVEs | Continuous |
| Penetration-test / red-team platform | External adversarial exercises | Quarterly |
| SIEM / SOAR | Incident detection and response | Real-time |
| Key rotation service | Short-lived workload credentials | Automated rotation |

## 8. Replacement and exit principles

Every MCP server in this catalog is abstracted behind `SourceAdapter` or `ModelGateway` interfaces. No component hard-codes a vendor endpoint; each declares:

- Purpose and fallback connector/provider.
- Cost per call or per 1k tokens.
- Rights, provenance and PIT semantics.
- Quality checks and schema validation.
- Vendor register entry with alternatives, SLA, exit plan and data classification.

This enables the organization to replace any model, vendor or agent without losing institutional knowledge, satisfying Section 40 criterion C12.
