import type { CaseStatus } from "@/lib/controlPlaneData";

export type MutableCase = {
  id: string;
  title: string;
  tenant: string;
  amount: string;
  workflow: string;
  status: CaseStatus;
  risk: number;
  decision: string;
  activeAgent: string;
};

export type AgentRunPayload = {
  request_id: string;
  workflow_type: string;
  agents_run: string[];
  decision: string;
  risk_score: number;
  risk_level: string;
  approval_role: string | null;
  agent_trace_count: number;
  proposal_id: string | null;
  retrieved_context: Array<{
    source_uri: string;
    namespace: string;
    score: number;
    content: string;
  }>;
  llm: {
    provider: string;
    model: string;
    confidence: number;
    content: string;
  };
  tools_available: Array<{
    name: string;
    owner: string;
    side_effecting: boolean;
    approval_required: boolean;
    description: string;
  }>;
  observability: Array<{
    name: string;
    state: string;
    detail: string;
    environment_keys: string[];
  }>;
};

export type ExecutionPayload = {
  execution_id: string;
  status: string;
  target_system: string;
  action_type: string;
  connector: string;
  external_reference: string | null;
  rollback_reference: string | null;
  message: string;
  audit_chain_valid: boolean;
};

export type AgentRegistryPayload = {
  product_module: string;
  summary: {
    total_agents: number;
    approved_agents: number;
    restricted_agents: number;
    pilot_agents: number;
    monthly_cost_usd: number;
    open_incidents: number;
    high_or_critical_risk: number;
  };
  agents: Array<{
    agent_id: string;
    name: string;
    owner: string;
    business_domain: string;
    risk_tier: string;
    autonomy_level: number;
    status: string;
    model_provider: string;
    allowed_tools: string[];
    data_classes: string[];
    last_run_at: string;
    monthly_cost_usd: number;
    open_incidents: number;
    value_metric: string;
  }>;
};

export type AgentLifecyclePayload = {
  product_module: string;
  headline: string;
  allowed_statuses: string[];
  agents: AgentRegistryPayload["agents"];
  controls: string[];
};

export type PolicySimulationPayload = {
  simulation_id: string;
  decision: string;
  risk_score: number;
  risk_level: string;
  approval_role: string | null;
  policy_version: string;
  evaluation_passed: boolean;
  failed_checks: string[];
  reason_codes: string[];
  explanation: string;
};

export type PolicyStudioPayload = {
  product_module: string;
  policy_name: string;
  draft_rule: string;
  dry_run_decision: string;
  generated_policy_preview: {
    engine: string;
    version: string;
    conditions: string[];
    effect: string;
  };
  blast_radius: {
    agents_impacted: string[];
    tools_impacted: string[];
    estimated_monthly_intercepts: number;
    expected_review_increase_percent: number;
  };
  promotion_checklist: string[];
  gateway_result: GatewayPayload;
};

export type PolicyReplayPayload = {
  product_module: string;
  headline: string;
  policy_name: string;
  lookback_window: string;
  cases_replayed: number;
  changed_decisions: number;
  review_load_delta_percent: number;
  recommendation: string;
  cases: Array<{
    case_id: string;
    historical_decision: string;
    new_decision: string;
    changed: boolean;
    business_impact: string;
  }>;
};

export type RegulatedOpsDemoPayload = {
  product_module: string;
  scenario: string;
  story: string;
  business_problem: string[];
  governed_steps: Array<{
    action: string;
    decision: string;
    why: string;
  }>;
  buyer_value: string[];
};

export type AuditPacketPayload = {
  packet_type: string;
  generated_at: string;
  case: { case_id: string; status: string } | null;
  agent_traces: unknown[];
  action_proposals: unknown[];
  governance_decisions: unknown[];
  approval_tasks: unknown[];
  action_executions: unknown[];
  audit_events: unknown[];
  audit_chain_valid: boolean;
};

export type IdentityPosturePayload = {
  product_module: string;
  principal_count: number;
  tenant_count: number;
  tool_grants: number;
  principals: Array<{
    principal_id: string;
    tenant_id: string;
    roles: string[];
    allowed_tools: string[];
  }>;
};

export type IdentityGraphPayload = {
  product_module: string;
  headline: string;
  nodes: Array<{
    id: string;
    label: string;
    kind: string;
    risk: string;
    detail: string;
  }>;
  edges: Array<{
    from: string;
    to: string;
    relationship: string;
  }>;
  blast_radius: {
    privileged_principals: number;
    side_effecting_tools: number;
    highest_risk_paths: string[];
    recommended_controls: string[];
  };
};

export type PermissionMatrixPayload = {
  product_module: string;
  headline: string;
  columns: string[];
  rows: Array<{
    agent_id: string;
    name: string;
    owner: string;
    status: string;
    risk_tier: string;
    permissions: Array<{
      tool: string;
      permission: string;
      requires_gateway: boolean;
      requires_human_approval: boolean;
    }>;
  }>;
  legend: Record<string, string>;
  recommended_controls: string[];
};

export type KillSwitchPayload = {
  product_module?: string;
  active_rule_count?: number;
  status?: string;
  rule?: {
    rule_id: string;
    scope_type: string;
    scope_value: string;
    reason: string;
    active: boolean;
  };
  posture?: {
    active_rule_count: number;
  };
  rules?: Array<{
    rule_id: string;
    scope_type: string;
    scope_value: string;
    reason: string;
    active: boolean;
  }>;
};

export type IncidentTimelinePayload = {
  product_module: string;
  headline: string;
  active_incidents: number;
  events: Array<{
    event: string;
    time: string;
    detail: string;
  }>;
  operating_procedure: string[];
};

export type GoldenEvalPayload = {
  product_module: string;
  gate: string;
  total_cases: number;
  passed_cases: number;
  average_score: number;
  release_recommendation: string;
  cases: Array<{
    case_id: string;
    category: string;
    expected_decision: string;
    actual_decision: string;
    score: number;
    passed: boolean;
  }>;
};

export type GovernanceMetricsPayload = {
  product_module: string;
  headline: string;
  tenant_id: string;
  pilot_target_pct: number;
  gateway_coverage_pct: number;
  gateway_tool_calls: number;
  broker_executions: number;
  executions_with_token: number;
  executions_without_token: number;
  bypass_attempts_blocked: number;
  audit_packets_available: number;
  mean_time_to_approve_minutes: number | null;
  board_metrics: Array<{
    label: string;
    value: string | number;
    meaning: string;
  }>;
  recommended_actions: string[];
};

export type PlatformPosturePayload = {
  product_module: string;
  headline: string;
  posture_score: number;
  board_metrics: Array<{
    label: string;
    value: string | number;
    meaning: string;
  }>;
  executive_summary: string;
  recommended_actions: string[];
};

export type GatewayStoryPayload = {
  product_module: string;
  headline: string;
  category: string;
  buyer_promise: string;
  flow: Array<{
    step: string;
    control: string;
  }>;
  supported_runtimes: string[];
};

export type GatewaySdkPayload = {
  product_module: string;
  headline: string;
  packages: Array<{
    name: string;
    runtime: string;
    status: string;
    install: string;
    adapter: string;
  }>;
  contract: {
    request_endpoint: string;
    execution_token_header: string;
    required_fields: string[];
  };
  definition_of_done: string[];
};

export type DeveloperQuickstartPayload = {
  product_module: string;
  headline: string;
  steps: string[];
  python: string;
  typescript: string;
  production_requirements: string[];
};

export type ReleaseGatePayload = {
  product_module: string;
  headline: string;
  agent_id: string;
  release_version: string;
  requested_by: string;
  decision: string;
  readiness_score: number;
  gates: Record<string, string>;
  required_approver: string;
  promotion_steps: string[];
};

export type DeploymentPosturePayload = {
  product_module: string;
  headline: string;
  tracks: Array<{
    name: string;
    fit: string;
    runtime: string;
    monthly_cost: string;
    controls: string[];
  }>;
  production_line: string;
};

export type FlagshipDemoPayload = {
  product_module: string;
  headline: string;
  talk_track: string;
  steps: Array<{
    step: string;
    buyer_message: string;
  }>;
  success_criteria: string[];
};

export type AgentOnboardingPayload = {
  product_module: string;
  agent_id: string;
  name: string;
  risk_tier: string;
  readiness_score: number;
  launch_decision: string;
  missing_controls: string[];
  required_approver: string;
  control_checklist: Array<{
    control: string;
    passed: boolean;
    why_it_matters: string;
  }>;
};

export type GatewayPayload = {
  product_module: string;
  gateway_decision: string;
  tool_name: string;
  agent_id: string;
  business_explanation: string;
  enforcement_steps: string[];
  execution_token?: string | null;
  policy_result?: PolicySimulationPayload;
};

export type AuditSignatureBlock = {
  algorithm: string;
  key_id: string;
  signed_at: string;
  content_digest: string;
  signature: string;
  signing_mode: string;
};

export type SignedAuditPayload = {
  packet_type: string;
  generated_at: string;
  audit_chain_valid: boolean;
  signature: AuditSignatureBlock;
  assurance?: {
    tamper_evident: boolean;
    verification_endpoint: string;
    instructions: string;
  };
  [key: string]: unknown;
};

export type AuditVaultPayload = {
  product_module: string;
  headline: string;
  retention_policy: string;
  evidence_types: string[];
  compliance_mapping: Array<{
    framework: string;
    controls: string[];
  }>;
  export_formats: string[];
};

export type AuditVerificationPayload = {
  valid: boolean;
  reason: string;
  algorithm?: string;
  signing_mode?: string;
};

export type ConnectorCatalogEntry = {
  connector_id: string;
  provider: string;
  supported_tools: string[];
  kind?: "builtin" | "http";
  display_name?: string;
  target_system?: string;
  base_url?: string;
  base_url_host?: string;
  http_method?: string;
  execute_path?: string;
  health_path?: string;
  auth_mode?: string;
  demo_mode?: boolean;
};

export type ConnectorCatalogPayload = {
  product_module: string;
  strategy: string;
  connectors: ConnectorCatalogEntry[];
  total: number;
  http_connectors_registered?: number;
};

export type HttpConnectorListPayload = {
  product_module: string;
  connectors: Array<{
    connector_id: string;
    display_name: string;
    base_url: string;
    target_system: string;
    tool_names?: string[];
    supported_tools?: string[];
    demo_mode: boolean;
    auth_mode: string;
  }>;
  total: number;
  guidance: string;
};

export type HttpConnectorRegisterPayload = {
  status: string;
  connector: {
    connector_id: string;
    display_name: string;
    base_url: string;
    target_system: string;
    demo_mode: boolean;
  };
  catalog_total: number;
};

export type HttpConnectorTestPayload = {
  success: boolean;
  status_code: number | null;
  latency_ms: number;
  message: string;
  url: string;
};

export type McpProxyPayload = {
  product_module: string;
  mcp_server: string;
  tool_name: string;
  canonical_tool_name: string;
  gateway_decision: string;
  execution_token?: string | null;
  mcp_invocation_status: string;
  mcp_external_reference?: string | null;
  message: string;
};

export type FinOpsDashboardPayload = {
  product_module: string;
  total_monthly_cost_usd: number;
  average_cost_per_agent_usd: number;
  agent_count: number;
  anomaly_count: number;
  executive_summary: string;
  roi?: {
    estimated_review_minutes_saved: number;
    estimated_loss_prevented_usd: number;
    average_cost_per_governed_workflow_usd: number;
    autonomy_roi_score: number;
    business_value_summary: string;
  };
  cost_by_agent: Array<{
    agent_id: string;
    name: string;
    owner: string;
    monthly_cost_usd: number;
    risk_tier: string;
    value_metric: string;
  }>;
  anomalies: Array<{
    agent_id: string;
    name: string;
    monthly_cost_usd: number;
    severity: string;
    reason: string;
    recommended_action: string;
  }>;
};

export type ReadinessPayload = {
  product_module: string;
  agent_id: string;
  name?: string;
  readiness_score: number;
  launch_decision: string;
  missing_controls: string[];
  controls: Array<{
    control: string;
    passed: boolean;
    why_it_matters: string;
  }>;
};

export type IntegrationsPayload = {
  product_module: string;
  integration_strategy: string;
  agent_frameworks: Array<{
    name: string;
    mode: string;
    value: string;
  }>;
  enterprise_connectors: string[];
};

export type UseCaseRun = {
  id: string;
  label: string;
  status: "running" | "complete" | "error";
  requestText: string;
  payload?: AgentRunPayload;
  error?: string;
};

export type PlatformActionKey = "posture" | "gateway" | "onboarding" | "readiness" | "integrations";
