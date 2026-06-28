-- AegisAI Postgres migration — production system of record (full read/write)
-- Apply: psql "$AEGISAI_DATABASE_URL" -f platform/database/postgres-migration.sql

CREATE TABLE IF NOT EXISTS cases (
  case_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  requester_user_id TEXT NOT NULL,
  workflow_type TEXT NOT NULL,
  status TEXT NOT NULL,
  data_classification TEXT NOT NULL,
  customer_impact BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_traces (
  trace_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL,
  agent_name TEXT NOT NULL,
  step_name TEXT NOT NULL,
  status TEXT NOT NULL,
  input_ref TEXT NOT NULL,
  output_ref TEXT NOT NULL,
  policy_findings TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS action_proposals (
  proposal_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  action_type TEXT NOT NULL,
  target_system TEXT NOT NULL,
  amount_usd DOUBLE PRECISION NOT NULL,
  data_classification TEXT NOT NULL,
  reversible BOOLEAN NOT NULL,
  customer_impact BOOLEAN NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS governance_decisions (
  decision_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL REFERENCES action_proposals(proposal_id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  risk_score INTEGER NOT NULL,
  risk_level TEXT NOT NULL,
  reason_codes TEXT NOT NULL,
  evaluation_passed BOOLEAN NOT NULL,
  failed_checks TEXT NOT NULL,
  approval_role TEXT,
  policy_version TEXT NOT NULL,
  decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approval_tasks (
  approval_task_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL REFERENCES action_proposals(proposal_id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL,
  assigned_role TEXT NOT NULL,
  status TEXT NOT NULL,
  due_at TEXT NOT NULL,
  escalation_path TEXT NOT NULL,
  decision_reason TEXT,
  decided_by TEXT,
  decided_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS action_executions (
  execution_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  status TEXT NOT NULL,
  target_system TEXT NOT NULL,
  action_type TEXT NOT NULL,
  connector TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  external_reference TEXT,
  rollback_reference TEXT,
  message TEXT NOT NULL,
  executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
  event_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  previous_hash TEXT NOT NULL,
  event_hash TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cases_tenant ON cases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_tenant_time ON audit_events(tenant_id, occurred_at ASC);
CREATE INDEX IF NOT EXISTS idx_proposals_tenant ON action_proposals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_traces_case ON agent_traces(case_id, tenant_id);

CREATE TABLE IF NOT EXISTS agent_registry (
  agent_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL DEFAULT 'bank-demo',
  name TEXT NOT NULL,
  owner TEXT NOT NULL,
  business_domain TEXT NOT NULL,
  risk_tier TEXT NOT NULL,
  autonomy_level INTEGER NOT NULL,
  status TEXT NOT NULL,
  model_provider TEXT NOT NULL,
  allowed_tools TEXT NOT NULL,
  data_classes TEXT NOT NULL,
  last_run_at TEXT NOT NULL DEFAULT 'not_run_yet',
  monthly_cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0,
  open_incidents INTEGER NOT NULL DEFAULT 0,
  value_metric TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_registry_tenant ON agent_registry(tenant_id);
