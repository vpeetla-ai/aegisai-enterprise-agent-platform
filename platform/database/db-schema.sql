-- AegisAI production reference schema.
-- SQLite-compatible for the portfolio implementation; map to Postgres in production.

CREATE TABLE tenants (
  tenant_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  region TEXT NOT NULL,
  policy_pack_version TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cases (
  case_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
  requester_user_id TEXT NOT NULL,
  workflow_type TEXT NOT NULL,
  status TEXT NOT NULL,
  data_classification TEXT NOT NULL,
  customer_impact INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_traces (
  trace_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  tenant_id TEXT NOT NULL,
  agent_name TEXT NOT NULL,
  step_name TEXT NOT NULL,
  status TEXT NOT NULL,
  input_ref TEXT,
  output_ref TEXT,
  policy_findings TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT NOT NULL
);

CREATE TABLE action_proposals (
  proposal_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  tenant_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  action_type TEXT NOT NULL,
  target_system TEXT NOT NULL,
  amount_usd REAL NOT NULL,
  data_classification TEXT NOT NULL,
  reversible INTEGER NOT NULL,
  customer_impact INTEGER NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE governance_decisions (
  decision_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL REFERENCES action_proposals(proposal_id),
  tenant_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  risk_score INTEGER NOT NULL,
  risk_level TEXT NOT NULL,
  reason_codes TEXT NOT NULL,
  evaluation_passed INTEGER NOT NULL,
  failed_checks TEXT NOT NULL,
  approval_role TEXT,
  policy_version TEXT NOT NULL,
  decided_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE approval_tasks (
  approval_task_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL REFERENCES action_proposals(proposal_id),
  tenant_id TEXT NOT NULL,
  assigned_role TEXT NOT NULL,
  status TEXT NOT NULL,
  due_at TEXT NOT NULL,
  escalation_path TEXT NOT NULL,
  decision_reason TEXT,
  decided_by TEXT,
  decided_at TEXT
);

CREATE TABLE action_executions (
  execution_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL REFERENCES action_proposals(proposal_id),
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  tenant_id TEXT NOT NULL,
  status TEXT NOT NULL,
  target_system TEXT NOT NULL,
  action_type TEXT NOT NULL,
  connector TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  external_reference TEXT,
  rollback_reference TEXT,
  message TEXT NOT NULL,
  executed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_events (
  event_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  previous_hash TEXT NOT NULL,
  event_hash TEXT NOT NULL,
  occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cases_tenant_status ON cases(tenant_id, status);
CREATE INDEX idx_agent_traces_case ON agent_traces(case_id);
CREATE INDEX idx_proposals_case ON action_proposals(case_id);
CREATE INDEX idx_decisions_proposal ON governance_decisions(proposal_id);
CREATE INDEX idx_approval_tasks_proposal ON approval_tasks(proposal_id);
CREATE INDEX idx_action_executions_proposal ON action_executions(proposal_id);
CREATE INDEX idx_audit_case ON audit_events(case_id, occurred_at);

CREATE TABLE memory_documents (
  document_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  namespace TEXT NOT NULL,
  source_uri TEXT NOT NULL,
  content TEXT NOT NULL,
  embedding TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_memory_tenant_namespace ON memory_documents(tenant_id, namespace);

CREATE TABLE agent_registry (
  agent_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  owner TEXT NOT NULL,
  business_domain TEXT NOT NULL,
  risk_tier TEXT NOT NULL,
  autonomy_level INTEGER NOT NULL,
  status TEXT NOT NULL,
  model_provider TEXT NOT NULL,
  allowed_tools TEXT NOT NULL,
  data_classes TEXT NOT NULL,
  monthly_cost_usd REAL NOT NULL,
  open_incidents INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE identity_principals (
  principal_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  roles TEXT NOT NULL,
  allowed_tools TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE kill_switch_rules (
  rule_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  scope_type TEXT NOT NULL,
  scope_value TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_by TEXT NOT NULL,
  active INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deactivated_at TEXT
);

CREATE TABLE golden_eval_runs (
  eval_run_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  gate TEXT NOT NULL,
  total_cases INTEGER NOT NULL,
  passed_cases INTEGER NOT NULL,
  average_score REAL NOT NULL,
  release_recommendation TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
