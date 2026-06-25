# Business Rules

> **System architecture (canonical):** [`ARCHITECTURE.md`](ARCHITECTURE.md)

## Rule Strategy

Business rules are split into two layers:

- **Agent business rules:** determine what each specialized agent is allowed to reason about, propose, or reject.
- **Control-plane policies:** determine whether proposed actions are auto-approved, human-reviewed, escalated, or blocked.

This separation is important. Agents can recommend actions, but the control plane owns execution authority.

Implementation ownership:

- Agent business rules live in `aegisai.application.orchestration.multi_agent`.
- Risk scoring and evaluation gates live in `aegisai.application.guardrails`.
- Stable rule inputs and outputs live in `aegisai.domain`.
- Persisted rule outcomes live in `aegisai.infrastructure.persistence`.
- Approved side effects live in `aegisai.application.execution`.
- Observability/export posture lives in `aegisai.observability` and must not change the decision.

## Workflow Classification Rules

| Signal | Workflow | Required Agents |
| --- | --- | --- |
| Refund, cancellation, credit | Refund | Intake, Evidence, Refund, Compliance, Communication |
| Dispute, chargeback | Payment Dispute | Intake, Evidence, Dispute, Compliance, Communication |
| Delete, export, modify data | Data Operations | Intake, Evidence, Data Operations, Compliance |
| Access grant, deployment, config | IT Operations | Intake, Evidence, IT Operations, Compliance |
| Customer-facing response | Communication | Intake, Evidence, Communication, Compliance when regulated |

## Agent-Level Rules

### Planner Agent

- Must choose the minimum set of agents needed for the workflow.
- Must stop when required evidence is missing.
- Must not directly execute tools.

### Evidence Retrieval Agent

- Must attach evidence references before any side-effect proposal.
- Must label evidence confidence.
- Must mark stale or missing evidence.

### Refund Agent

- Can propose refund actions only when payment evidence exists.
- Must include amount, reason, customer impact, and reversibility.
- Must mark fraud, legal, or policy exception cases for escalation.

### Customer Communication Agent

- Can draft messages before approval.
- Must not send messages until the underlying business action is approved.
- Must pass safety, tone, grounding, and policy-compliance checks.

### Compliance Agent

- Can recommend escalation or block.
- Must flag restricted data, irreversible actions, and regulated topics.
- Must provide reason codes for every compliance finding.

## Control-Plane Approval Rules

| Condition | Routing Decision |
| --- | --- |
| Low risk and evaluation passes | Auto-approve |
| Medium risk | Workflow-owner approval |
| Failed evaluation on low or medium risk | Human approval |
| High risk | Senior domain approver |
| Critical risk | Block |
| High risk plus failed evaluation | Block |
| Restricted data plus irreversible action | Block or compliance approval depending on policy |

## Evaluation Rules

Blocking proposal-level checks:

- Grounding score must meet threshold.
- Safety score must meet threshold.
- Policy-compliance score must meet threshold.
- Model confidence must meet threshold.

Release-level checks:

- Prompt changes must pass golden dataset regression.
- Retrieval changes must pass context precision and grounding tests.
- Tool changes must pass schema and side-effect simulation tests.
- Model changes must pass quality, safety, latency, and cost gates.

## Audit Rules

Every case must capture:

- Agents selected by the orchestrator.
- Shared context writes by each agent.
- Evidence references.
- Proposed actions.
- Risk and evaluation results.
- Policy version.
- Human reviewer decisions.
- Execution outcome.
- Feedback used for improvement.

## Execution Rules

The execution broker is the only component allowed to perform side effects:

- Agents may only create `ActionProposal` records.
- `block` decisions can never execute.
- `human_approval` and `escalate` decisions require an approved approval task.
- `auto_approve` decisions can execute without reviewer action.
- Every execution attempt must use an idempotency key.
- Every successful connector call must return an external reference.
- Reversible actions must record a rollback reference.
- Every execution result, including blocked and requires-approval attempts, must append an audit event.
