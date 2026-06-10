# Security and Compliance

## Security Principles

- Agents can propose actions, but only the execution broker can perform approved side effects.
- All approval authority is explicit and context-aware.
- Sensitive evidence is minimized, masked, and shown only when required.
- Every critical decision is auditable and reproducible.

## Identity and Access

- Human reviewers authenticate through enterprise SSO.
- RBAC grants baseline reviewer capability.
- ABAC constrains approval by tenant, region, data classification, amount, workflow, and escalation level.
- Service identities are scoped per integration and rotated through a secrets manager.

## Data Protection

- PII is classified at proposal ingestion.
- Reviewer packets show redacted fields by default.
- Full evidence access requires elevated permission and is logged.
- Evaluation datasets are de-identified where possible.
- Retention policies are configurable by tenant and regulation.

## Audit and Evidence

Audit records include:

- Agent, model, prompt, tool, and policy versions.
- Risk score and reason codes.
- Evaluation scores and failure reasons.
- Approver identity, decision, timestamp, and rationale.
- Execution request, response, and outcome.
- Before/after references when legally and technically allowed.

## Compliance Mapping

- **SOC 2:** auditability, access control, change management, incident response.
- **GDPR / CCPA:** data minimization, deletion workflow evidence, access logging.
- **FINRA / financial controls:** approval evidence for payment and customer-impacting decisions.
- **HIPAA-style controls:** sensitive data masking, least privilege, access trails for healthcare workflows.

## Threat Model Highlights

- Prompt injection attempts to bypass approval: mitigated by separating agent output from policy enforcement.
- Malicious or mistaken approver: mitigated by role constraints, dual approval for critical actions, and audit review.
- Policy misconfiguration: mitigated by policy tests, simulation, staged rollout, and rollback.
- Model drift: mitigated by online evaluation, canary gates, and drift alerts.
- Duplicate execution: mitigated by idempotency keys and execution broker enforcement.

