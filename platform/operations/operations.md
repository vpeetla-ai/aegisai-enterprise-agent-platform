# Operations

## Service Level Objectives

- Proposal API availability: 99.9%.
- Risk scoring p95 latency: under 150 ms.
- Policy evaluation p95 latency: under 100 ms.
- Approval notification delivery: under 30 seconds.
- Audit event durability: 99.999%.
- Evaluation dashboard freshness: under 5 minutes for online metrics.

## Key Metrics

- Auto-approval rate by workflow and risk level.
- Human approval latency by team, role, and policy.
- Escalation rate.
- Rejection and request-info rate.
- Evaluation pass/fail rate by model, prompt, retrieval index, and tool.
- Drift score by workflow.
- Cost per successful task.
- Execution failure and retry rate.
- Audit export completeness.

## Alerts

- High-risk action attempted without approval token.
- Audit write failures.
- Approval SLA breach.
- Sudden increase in evaluation failures.
- Drift above threshold.
- Auto-approval rate outside expected band.
- Execution broker downstream failure spike.
- Policy deployment regression.

## Runbooks

### Evaluation Gate Failure Spike

1. Freeze model/prompt rollout.
2. Compare failing examples against previous baseline.
3. Identify whether root cause is model, prompt, retrieval, tool schema, or policy change.
4. Route severe customer-impacting failures to incident process.
5. Patch and rerun regression set before resuming rollout.

### Approval Queue Backlog

1. Identify affected tenant, workflow, and approval role.
2. Check notification delivery and workflow service health.
3. Trigger escalation path if SLA threshold is breached.
4. Temporarily lower auto-approval only if policy owner approves and risk remains acceptable.
5. Capture backlog cause for policy or staffing adjustment.

### Execution Broker Failure

1. Stop new executions for affected target system.
2. Preserve proposal and approval state.
3. Inspect idempotency records before replaying any action.
4. Resume from durable workflow checkpoint.
5. Reconcile outcomes with system of record.

