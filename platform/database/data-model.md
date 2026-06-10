# Data Model

## Canonical Entities

Current code ownership:

- Domain contracts: `aegisai.domain.models`
- Control-plane persistence adapter: `aegisai.infrastructure.persistence.control_plane_store`
- Approved execution broker: `aegisai.application.execution.broker`
- Product agent registry and policy simulator: `aegisai.product`
- Vector memory reference adapter: `aegisai.application.knowledge.vector_memory`
- Observability trace event contract: `aegisai.observability.models`

### ActionProposal

Represents an agent's requested side effect.

### RegisteredAgent

Represents product inventory for agent sprawl control.

Key fields:

- agent_id
- owner
- business_domain
- risk_tier
- autonomy_level
- status
- model_provider
- allowed_tools
- data_classes
- monthly_cost_usd
- open_incidents
- value_metric

### PolicySimulation

Represents a what-if governance decision.

Key fields:

- simulation_id
- tenant_id
- action_type
- target_system
- amount_usd
- data_classification
- reversible
- customer_impact
- model_confidence
- evaluation_scores
- decision
- risk_score
- approval_role
- reason_codes

### IdentityPrincipal

Represents reviewer, agent, and execution identities.

Key fields:

- principal_id
- tenant_id
- roles
- allowed_tools
- status

### KillSwitchRule

Represents emergency incident control.

Key fields:

- rule_id
- tenant_id
- scope_type
- scope_value
- reason
- created_by
- active
- created_at

### GoldenEvalRun

Represents regression gate result for prompt/model/retrieval/tool releases.

Key fields:

- eval_run_id
- gate
- total_cases
- passed_cases
- average_score
- release_recommendation

Key fields:

- proposal_id
- tenant_id
- correlation_id
- idempotency_key
- actor_user_id
- agent_id
- model_version
- prompt_version
- tool_name
- action_type
- target_system
- data_classification
- amount_usd
- reversible
- customer_impact
- rationale
- evidence_refs
- rollback_plan
- created_at

### EvaluationResult

Represents quality and safety checks for a proposal or model release.

Key fields:

- evaluation_id
- proposal_id
- evaluator_version
- relevance_score
- grounding_score
- safety_score
- policy_compliance_score
- latency_ms
- cost_usd
- passed
- failure_reasons

### RiskDecision

Represents contextual risk scoring.

Key fields:

- risk_id
- proposal_id
- policy_version
- risk_score
- risk_level
- reason_codes
- calculated_at

### ApprovalTask

Represents a human review workflow.

Key fields:

- approval_task_id
- proposal_id
- assigned_role
- assigned_user_id
- status
- due_at
- escalation_path
- decision
- decision_reason
- decided_at

### ExecutionRecord

Represents an approved side effect. Implemented as `action_executions`.

Key fields:

- execution_id
- proposal_id
- case_id
- tenant_id
- idempotency_key
- connector
- target_system
- action_type
- external_reference
- rollback_reference
- message
- status
- executed_at

### AuditEvent

Append-only event for all critical transitions.

Key fields:

- event_id
- tenant_id
- correlation_id
- event_type
- subject_id
- actor_id
- occurred_at
- payload
- previous_hash
- event_hash

## Event Types

- proposal.created
- evaluation.completed
- risk.scored
- policy.evaluated
- approval.requested
- approval.decided
- approval.escalated
- execution.executed
- execution.requires_approval
- execution.blocked
- execution.failed
- feedback.recorded
- policy.updated
- evaluator.updated

## Idempotency Strategy

The idempotency key is derived from tenant, workflow instance, target system, action type, and intended state change. Execution broker retries reuse the same key so downstream calls cannot apply duplicate side effects.
