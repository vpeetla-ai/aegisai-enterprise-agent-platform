# Compliance Mapping — EU AI Act & SOC 2 ↔ AegisAI

> **Disclaimer:** This document is a product alignment aid, not legal advice. Engage counsel for formal compliance programs.

## Summary

AegisAI modules map to common enterprise controls for **high-risk AI operations** (human oversight, logging, accuracy, cybersecurity) and SOC 2 **CC** (Common Criteria) themes.

| AegisAI module | Primary control themes |
| --- | --- |
| Agent Registry (Discover) | Asset inventory, ownership, risk classification |
| Governance Gateway (Enforce) | Preventive controls on tool execution |
| Policy Engine + OPA (Govern) | Authorization, change management |
| HITL + Slack (Govern) | Human oversight |
| Evaluation + Red-team (Evaluate) | Testing, monitoring |
| Execution Broker (Execute) | Change execution, idempotency |
| Audit Ledger + Packets (Assure) | Logging, evidence retention |
| Identity / OIDC (Secure) | Access control |
| Kill Switch (Enforce) | Incident response |
| FinOps (Discover) | Monitoring, anomaly detection |

## EU AI Act — high-risk AI system alignment (operational)

| EU AI Act theme | Requirement (simplified) | AegisAI capability | Evidence artifact |
| --- | --- | --- | --- |
| Risk management | Continuous risk management process | Risk scorer, policy simulator, registry risk tier | Policy simulation export |
| Data governance | Training/context data quality | RAG evidence, retrieval scores in eval gates | Agent trace + retrieval citations |
| Technical documentation | System capabilities, limitations | Architecture docs, integration posture API | `GET /api/platform/integrations` |
| Record-keeping | Automatic logs | Hash-chained audit events | Audit packet JSON/PDF |
| Transparency | Information to deployers | Decision reason codes, policy version | Governance decision record |
| Human oversight | Ability to override | HITL reviewer actions, kill switch | Reviewer action + Slack approval |
| Accuracy / robustness | Appropriate metrics | Golden + red-team eval suites | `POST /api/evaluations/*/run` |
| Cybersecurity | Resilience against attacks | Red-team eval pack, gateway deny path | Red-team report |

## SOC 2 Trust Services Criteria (sample mapping)

| TSC | Control objective | AegisAI feature |
| --- | --- | --- |
| CC6.1 | Logical access security | OIDC, RBAC, tenant boundaries |
| CC6.2 | Registration / authorization | Agent registry, tool grants per principal |
| CC6.3 | Role-based access | Reviewer roles, approval_role routing |
| CC6.6 | Boundary protection | Gateway blocks unauthorized tool calls |
| CC7.2 | Detection of anomalies | FinOps cost anomalies, kill switch triggers |
| CC7.3 | Evaluation of incidents | Incident count on registry, freeze rules |
| CC8.1 | Change management | Policy version, OPA Git promotion |
| CC9.2 | Risk mitigation | Risk-based HITL, eval gates before execution |
| A1.2 | Recovery | Execution rollback references, idempotency |

## Audit packet contents (for assessors)

Each case export should include:

1. Case metadata (tenant, workflow, classification)  
2. Action proposal (agent, tool, amount, reversibility)  
3. Evaluation gate results  
4. Risk assessment + reason codes  
5. Governance decision + **policy version**  
6. Human approval (if any) + reviewer identity  
7. Execution result + external reference  
8. Audit chain validity flag  

API: `GET /api/audit-packets/{tenant_id}/{case_id}.pdf`

## Procurement FAQ snippets

**Q: Where is human oversight enforced?**  
A: Policy routes medium/high risk to HITL; gateway pauses tool calls until approval; Slack integration for reviewer actions.

**Q: Can we prove tamper-evident logs?**  
A: Append-only audit events with hash chain verification (`verify_audit_chain`).

**Q: How do you support data minimization?**  
A: Reviewer views can redact PII; traces reference evidence URIs rather than raw payloads (production config).

## Roadmap for formal certifications

| Milestone | Timeline |
| --- | --- |
| SOC 2 Type I readiness | Post-3 paying customers |
| Signed audit packets (KMS) | Enterprise tier |
| EU AI Act annex documentation pack | Q+2 from pilot |
