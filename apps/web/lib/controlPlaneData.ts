import {
  Activity,
  AlertTriangle,
  Archive,
  Bot,
  CheckCircle2,
  ClipboardCheck,
  Database,
  Fingerprint,
  FileSearch,
  GitBranch,
  KeyRound,
  MemoryStick,
  MessageSquareText,
  Network,
  Rocket,
  ShieldCheck,
  UserCheck,
  WalletCards,
  Wrench
} from "lucide-react";

export type CaseStatus =
  | "auto-approved"
  | "human-review"
  | "escalated"
  | "blocked"
  | "approved"
  | "rejected"
  | "info-requested";

export type AgentKey =
  | "intake"
  | "planner"
  | "evidence"
  | "refund"
  | "compliance"
  | "comms"
  | "control";

export const kpis = [
  { label: "Open Agent Cases", value: "128", change: "+14 today" },
  { label: "Auto-Approval Rate", value: "67%", change: "within guardrail" },
  { label: "High-Risk Reviews", value: "19", change: "p95 18 min" },
  { label: "Eval Gate Pass Rate", value: "94.2%", change: "-1.1 drift" }
];

export const startupProductModules = [
  {
    label: "Discover",
    headline: "Know every agent before it acts",
    detail: "Inventory agent owner, model, tools, data class, risk tier, autonomy, cost, and incident posture."
  },
  {
    label: "Govern",
    headline: "Explain every decision before execution",
    detail: "Simulate policy, score risk, evaluate quality, route HITL, and prove which rule fired."
  },
  {
    label: "Execute",
    headline: "Run only approved side effects",
    detail: "Use an execution broker for idempotency, connector allowlists, rollback references, and audit events."
  }
] as const;

export const marketProblemCoverage = [
  {
    problem: "Agent sprawl",
    capability: "Agent Registry",
    proof: "Central inventory of owners, domains, model posture, autonomy, risk, cost, and incidents."
  },
  {
    problem: "Identity sprawl",
    capability: "Agent Identity + RBAC",
    proof: "Reviewer roles and execution identities are checked before approval or tool execution."
  },
  {
    problem: "Tool sprawl",
    capability: "Governed Tool Gateway",
    proof: "Side-effecting tools require policy, approval, idempotency, and execution broker routing."
  },
  {
    problem: "Audit gaps",
    capability: "Audit Packet Export",
    proof: "JSON/PDF packets reconstruct request, agents, decisions, approvals, execution, and hash-chain status."
  },
  {
    problem: "Unmanaged cost",
    capability: "Registry + Golden Evals",
    proof: "Agent monthly cost, eval gates, and release recommendations expose cost and quality posture."
  }
] as const;

export const startupMilestones = [
  { label: "Agent Registry", status: "Implemented", module: "Discover" },
  { label: "Policy Simulator", status: "Implemented", module: "Govern" },
  { label: "Audit Packet Export", status: "Implemented", module: "Assure" },
  { label: "Agent Identity + RBAC", status: "Implemented", module: "Secure" },
  { label: "Incident Kill Switch", status: "Implemented", module: "Respond" },
  { label: "Golden Dataset Eval Center", status: "Implemented", module: "Evaluate" },
  { label: "Governance Gateway", status: "Implemented", module: "Enforce" },
  { label: "Agent Onboarding", status: "Implemented", module: "Onboard" },
  { label: "Production Readiness Score", status: "Implemented", module: "Assure" },
  { label: "Integration Posture", status: "Implemented", module: "Scale" }
] as const;

export const platformCommandModules = [
  {
    label: "Command",
    headline: "Executive risk posture",
    detail: "A board-ready view of agent inventory, high-risk autonomy, spend, incidents, freezes, and next actions."
  },
  {
    label: "Onboard",
    headline: "Agent launch control",
    detail: "New agents cannot move to production until ownership, policy, evals, observability, tool scopes, data classes, and kill switches are ready."
  },
  {
    label: "Enforce",
    headline: "Runtime governance gateway",
    detail: "Every high-impact tool call is authorized, risk-scored, evaluated, paused, approved, blocked, or audited before execution."
  },
  {
    label: "Integrate",
    headline: "Govern any agent framework",
    detail: "AegisAI can govern native LangGraph workflows plus OpenAI, Bedrock, Copilot Studio, Agentforce, and custom agents."
  }
] as const;

export const referenceExampleMenu = [
  {
    label: "Refund agent example",
    detail: "Shows a customer-impacting money movement that needs policy, evidence, HITL, audit, and execution gating."
  },
  {
    label: "Data deletion example",
    detail: "Shows how irreversible restricted-data actions are blocked or routed to privacy/compliance before execution."
  },
  {
    label: "Low-risk credit example",
    detail: "Shows how safe, reversible work can move quickly while still producing trace and audit evidence."
  },
  {
    label: "Golden eval example",
    detail: "Shows how prompt, model, retrieval, and tool changes are regression-tested before release."
  }
] as const;

export const policySimulatorScenarios = [
  {
    label: "High-value refund",
    actionType: "issue_refund",
    targetSystem: "payments",
    amountUsd: 2500,
    dataClassification: "confidential",
    reversible: true,
    customerImpact: true,
    expected: "Escalate"
  },
  {
    label: "Low-risk credit",
    actionType: "issue_refund",
    targetSystem: "payments",
    amountUsd: 25,
    dataClassification: "internal",
    reversible: true,
    customerImpact: false,
    expected: "Auto-approve"
  },
  {
    label: "Restricted deletion",
    actionType: "modify_or_delete_data",
    targetSystem: "customer_data_platform",
    amountUsd: 0,
    dataClassification: "restricted",
    reversible: false,
    customerImpact: true,
    expected: "Block"
  }
] as const;

export const agents = [
  {
    key: "intake",
    name: "Intake & Triage",
    owner: "Case classification",
    icon: ClipboardCheck,
    status: "complete",
    rule: "Classify workflow, urgency, data sensitivity, and customer impact."
  },
  {
    key: "planner",
    name: "Planner",
    owner: "Task sequencing",
    icon: GitBranch,
    status: "complete",
    rule: "Select minimum agents, enforce stop conditions, require evidence."
  },
  {
    key: "evidence",
    name: "Evidence Retrieval",
    owner: "Grounding",
    icon: FileSearch,
    status: "complete",
    rule: "Attach fresh evidence references before action proposals."
  },
  {
    key: "refund",
    name: "Refund Agent",
    owner: "Payment action",
    icon: WalletCards,
    status: "complete",
    rule: "Calculate refund eligibility, amount, and reversibility."
  },
  {
    key: "compliance",
    name: "Risk & Compliance",
    owner: "Policy findings",
    icon: ShieldCheck,
    status: "running",
    rule: "Flag restricted data, irreversible actions, fraud, legal, and thresholds."
  },
  {
    key: "comms",
    name: "Customer Communication",
    owner: "Response quality",
    icon: MessageSquareText,
    status: "queued",
    rule: "Draft customer response only after business action is approved."
  },
  {
    key: "control",
    name: "Execution Broker",
    owner: "Approved side effects",
    icon: Rocket,
    status: "queued",
    rule: "Execute only approved or auto-approved proposals with idempotency and rollback metadata."
  }
] as const;

export const cases = [
  {
    id: "CASE-1048",
    title: "Refund failed booking",
    tenant: "Bank Demo",
    amount: "$2,500",
    workflow: "Refund",
    status: "escalated" as CaseStatus,
    risk: 55,
    decision: "Senior domain approver",
    activeAgent: "compliance" as AgentKey
  },
  {
    id: "CASE-1051",
    title: "Delete customer data",
    tenant: "Bank Demo",
    amount: "$0",
    workflow: "Data Operations",
    status: "blocked" as CaseStatus,
    risk: 90,
    decision: "Blocked by restricted irreversible rule",
    activeAgent: "control" as AgentKey
  },
  {
    id: "CASE-1057",
    title: "Duplicate fee credit",
    tenant: "Bank Demo",
    amount: "$25",
    workflow: "Refund",
    status: "auto-approved" as CaseStatus,
    risk: 5,
    decision: "Auto-approved",
    activeAgent: "control" as AgentKey
  },
  {
    id: "CASE-1060",
    title: "Chargeback evidence response",
    tenant: "Bank Demo",
    amount: "$890",
    workflow: "Dispute",
    status: "human-review" as CaseStatus,
    risk: 45,
    decision: "Workflow owner review",
    activeAgent: "evidence" as AgentKey
  }
] as const;

export const sharedContext = [
  { label: "Request", value: "Customer requests refund after failed booking confirmation." },
  { label: "Evidence", value: "crm://cases/CASE-1048, payments://transactions/CASE-1048" },
  { label: "Policy", value: "Refund over $1,000 and customer-impacting requires senior review." },
  { label: "Proposed Action", value: "issue_refund amount=$2,500 target=payments reversible=true" },
  { label: "Reviewer Packet", value: "Risk reasons, grounding score, refund rationale, customer draft." }
];

export const evaluationMetrics = [
  { label: "Grounding", value: 90, state: "pass" },
  { label: "Safety", value: 95, state: "pass" },
  { label: "Policy Compliance", value: 88, state: "pass" },
  { label: "Model Confidence", value: 86, state: "pass" }
];

export const governanceTimeline = [
  { label: "Proposal Created", detail: "Refund Agent proposed issue_refund", icon: Bot },
  { label: "Evaluation Passed", detail: "All blocking gates above 0.75", icon: CheckCircle2 },
  { label: "Risk Scored", detail: "55 high: amount, confidential data, customer impact", icon: AlertTriangle },
  { label: "Policy Routed", detail: "Senior domain approval required", icon: UserCheck },
  { label: "Audit Written", detail: "Append-only event stored with policy-2026.05", icon: Archive }
];

export const systemLayers = [
  {
    name: "Experience + Guardrails",
    description: "Enterprise workspace, test console, HITL review queue, policy checks, and safety gates.",
    nodes: ["Workspace", "Test UI", "HITL", "Policy", "Safety"]
  },
  {
    name: "AI Orchestration + Knowledge",
    description: "LangGraph agents grounded by hybrid retrieval, vector memory, and shared case context.",
    nodes: ["LangGraph", "RAG", "Vector DB", "BM25", "Agents"]
  },
  {
    name: "Infrastructure + Telemetry",
    description: "FastAPI, Bedrock, Postgres, event bus, audit ledger, metrics, traces, and feedback.",
    nodes: ["FastAPI", "Bedrock", "Postgres", "Events", "Telemetry"]
  }
];

export const statusMeta: Record<CaseStatus, { label: string; tone: string }> = {
  "auto-approved": { label: "Auto-approved", tone: "green" },
  "human-review": { label: "Human review", tone: "blue" },
  escalated: { label: "Escalated", tone: "amber" },
  blocked: { label: "Blocked", tone: "red" },
  approved: { label: "Approved", tone: "green" },
  rejected: { label: "Rejected", tone: "red" },
  "info-requested": { label: "Info requested", tone: "blue" }
};

export const operatingQueues = [
  { label: "Reviewer SLA", value: "18m p95", icon: UserCheck },
  { label: "Policy Version", value: "2026.05", icon: ShieldCheck },
  { label: "Audit Events", value: "42.8k", icon: Database },
  { label: "Tool Failures", value: "0.4%", icon: Wrench }
];

export const productionControls = [
  {
    label: "Tenant Isolation",
    value: "ABAC + row policy",
    detail: "Every case, proposal, trace, decision, and audit event carries tenant_id.",
    icon: KeyRound
  },
  {
    label: "Audit Integrity",
    value: "Hash chained",
    detail: "Append-only event hashes link every governance transition to prior state.",
    icon: Fingerprint
  },
  {
    label: "DB Durability",
    value: "SQLite ref / Postgres prod",
    detail: "Portfolio uses SQLite; production target is Postgres with RLS and backups.",
    icon: Database
  },
  {
    label: "Trace Coverage",
    value: "7 agent steps",
    detail: "Planner, evidence, domain, compliance, comms, and decision traces are persisted.",
    icon: Network
  },
  {
    label: "Execution Broker",
    value: "Approval-gated",
    detail: "Approved actions use connector contracts, idempotency keys, external references, and rollback handles.",
    icon: Rocket
  }
];

export const reviewerActions = [
  { label: "Approve", tone: "green", description: "Issue signed approval token for broker." },
  { label: "Reject", tone: "red", description: "Return to orchestrator with reason code." },
  { label: "Request Info", tone: "blue", description: "Resume workflow at evidence agent." },
  { label: "Escalate", tone: "amber", description: "Route to senior approver or compliance." }
];

export const dataContracts = [
  { table: "cases", count: "128", purpose: "Workflow state and tenant boundary" },
  { table: "agent_traces", count: "896", purpose: "Agent handoffs, outputs, findings" },
  { table: "action_proposals", count: "214", purpose: "Side-effect intent and idempotency" },
  { table: "governance_decisions", count: "214", purpose: "Risk, eval, policy, routing result" },
  { table: "approval_tasks", count: "42", purpose: "Reviewer queue, SLA, escalation, decision reason" },
  { table: "action_executions", count: "31", purpose: "Approved connector calls, idempotency, rollback reference" },
  { table: "audit_events", count: "42.8k", purpose: "Tamper-evident evidence chain" }
];

export const memoryContracts = [
  {
    namespace: "refund_policy",
    source: "policy://refund/thresholds",
    score: "0.82",
    content: "Refunds over $1,000 require workflow-owner approval; over $10,000 requires senior approval."
  },
  {
    namespace: "case_history",
    source: "prior://refunds/high-value-approved",
    score: "0.76",
    content: "Similar high-value refund required evidence, reviewer rationale, and signed execution token."
  },
  {
    namespace: "communication_policy",
    source: "policy://customer-communications/regulated-topics",
    score: "0.69",
    content: "Do not promise refund completion before approval and payment-system confirmation."
  }
];

export const dataPlaneComponents = [
  { name: "Postgres OLTP", role: "Cases, approvals, proposals, decisions", health: "Healthy", icon: Database },
  { name: "Vector Memory", role: "Policy, evidence, prior decisions, templates", health: "Fresh", icon: MemoryStick },
  { name: "Audit Ledger", role: "Hash-chained immutable governance events", health: "Verified", icon: Fingerprint },
  { name: "Event Bus", role: "Agent traces, workflow resumes, execution outcomes", health: "Nominal", icon: Network }
];

export const requestTemplates = [
  {
    label: "High-value refund",
    text: "Customer requests a refund above 2500 for a failed booking",
    amountUsd: 2500,
    classification: "confidential",
    impact: "Customer money movement",
    expectedDecision: "Escalate to senior domain approver"
  },
  {
    label: "Low-risk fee credit",
    text: "Customer asks for a 25 dollar duplicate fee credit after a billing error",
    amountUsd: 25,
    classification: "internal",
    impact: "Reversible customer credit",
    expectedDecision: "Auto-approve if evidence matches policy"
  },
  {
    label: "Data deletion",
    text: "Employee requests deletion of all customer profile data after an account closure",
    amountUsd: 0,
    classification: "restricted",
    impact: "Irreversible data operation",
    expectedDecision: "Block or route to privacy officer"
  }
] as const;

export const experienceJourney = [
  {
    step: "1",
    title: "Capture",
    layer: "User + Experience",
    question: "What is the user asking the AI system to do?",
    rule: "Collect tenant, channel, data class, amount, customer impact, and business intent.",
    output: "Normalized business request"
  },
  {
    step: "2",
    title: "Classify",
    layer: "Guardrails",
    question: "Is this a safe request, a risky request, or a blocked request?",
    rule: "Policy checks run before any agent can call tools or propose side effects.",
    output: "Workflow type + risk inputs"
  },
  {
    step: "3",
    title: "Ground",
    layer: "Data + Knowledge",
    question: "What policy, case history, and evidence should the agents trust?",
    rule: "Hybrid retrieval must attach source references before the domain agent proposes action.",
    output: "Evidence packet with scores"
  },
  {
    step: "4",
    title: "Orchestrate",
    layer: "AI Orchestration",
    question: "Which specialized agents need to run, and in what order?",
    rule: "Planner selects the minimum agent path and enforces stop conditions.",
    output: "Agent trace + proposed action"
  },
  {
    step: "5",
    title: "Evaluate",
    layer: "Evaluation",
    question: "Is the proposed answer grounded, safe, complete, and compliant?",
    rule: "Blocking gates must pass before execution or human review.",
    output: "Eval scores + policy finding"
  },
  {
    step: "6",
    title: "Approve",
    layer: "HITL + Control Plane",
    question: "Can the system execute, or does a human need to decide?",
    rule: "High-impact or irreversible actions require reviewer approval and audit evidence.",
    output: "Approve, reject, request info, escalate, or block"
  }
] as const;

export const businessRulePlaybook = [
  {
    name: "Money movement threshold",
    trigger: "Refund or payment action above $1,000",
    decision: "Route to workflow owner; senior approver for very high value.",
    why: "Prevents financial loss and creates accountable approval evidence.",
    tone: "amber"
  },
  {
    name: "Restricted data operation",
    trigger: "PII deletion, export, or irreversible data modification",
    decision: "Block automation or require privacy/compliance approval.",
    why: "Protects regulated data and avoids irreversible policy violations.",
    tone: "red"
  },
  {
    name: "Evidence-before-action",
    trigger: "Agent proposes customer-impacting side effect",
    decision: "Require retrieved policy and source-backed case evidence.",
    why: "Keeps agents grounded and makes decisions reviewable.",
    tone: "blue"
  },
  {
    name: "Communication safety",
    trigger: "Customer-facing response before execution is confirmed",
    decision: "Draft only; do not promise completion until approval and tool success.",
    why: "Avoids misleading regulated communications.",
    tone: "green"
  }
] as const;

export const outcomePacket = [
  { label: "Business decision", value: "Escalate", detail: "Risk score 55, high-impact refund, confidential data." },
  { label: "Reviewer role", value: "Senior domain approver", detail: "Approval needed before payment execution token is issued." },
  { label: "Execution broker", value: "Approval-gated", detail: "Connector runs only after HITL or auto-approval creates an execution token." },
  { label: "Audit evidence", value: "Hash chained", detail: "Request, policy, traces, evals, and reviewer decision are persisted." }
] as const;

export const executionBrokerSteps = [
  {
    label: "1. Read proposal",
    detail: "Load persisted proposal, decision, approval task, target system, reversibility, and idempotency key."
  },
  {
    label: "2. Enforce gate",
    detail: "Block if policy says block; pause if human approval is pending; continue only when approved."
  },
  {
    label: "3. Call connector",
    detail: "Route to payments, data, CRM, or change-management connector with tenant-scoped credentials."
  },
  {
    label: "4. Persist outcome",
    detail: "Write execution status, external reference, rollback reference, and hash-chained audit event."
  }
] as const;

export const observabilitySignals = [
  {
    label: "Trace Health",
    value: "99.2%",
    detail: "Agent, retrieval, eval, approval, and execution spans captured.",
    icon: Network
  },
  {
    label: "Quality Score",
    value: "94.2%",
    detail: "Grounding, policy, safety, and completion evals above threshold.",
    icon: ClipboardCheck
  },
  {
    label: "P95 Latency",
    value: "2.8s",
    detail: "End-to-end orchestration latency across successful runs.",
    icon: Activity
  },
  {
    label: "LLM Cost",
    value: "$18.42",
    detail: "Daily model and embedding cost attributed by tenant and workflow.",
    icon: WalletCards
  },
  {
    label: "Drift Alerts",
    value: "2",
    detail: "Policy-compliance and retrieval-grounding monitors need review.",
    icon: AlertTriangle
  },
  {
    label: "Audit Status",
    value: "Verified",
    detail: "Hash-chain validation passed for control-plane decision events.",
    icon: Fingerprint
  }
] as const;

export const traceTimeline = [
  { step: "01", span: "request.received", owner: "Experience Layer", signal: "tenant, actor, channel, request payload" },
  { step: "02", span: "policy.precheck", owner: "Guardrails", signal: "data class, amount threshold, restricted action checks" },
  { step: "03", span: "retrieval.search", owner: "Hybrid Retrieval", signal: "namespace, source URI, score, freshness" },
  { step: "04", span: "agent.graph", owner: "LangGraph", signal: "node path, handoffs, stop condition, state snapshot" },
  { step: "05", span: "eval.gates", owner: "Evaluation", signal: "grounding, safety, policy, confidence, regression tags" },
  { step: "06", span: "hitl.routing", owner: "Control Plane", signal: "decision, reviewer role, SLA, audit event hash" }
] as const;

export const observabilityAdapters = [
  {
    name: "Native AegisAI Control Plane",
    stance: "System of record",
    fit: "Best for portfolio demo, HITL state, policy decisions, audit, and enterprise workflow context.",
    tradeoff: "You own the UI and schema; needs adapters for richer external trace analysis."
  },
  {
    name: "Langfuse",
    stance: "Open-source LLM observability adapter",
    fit: "Great for self-hosted traces, prompt management, evals, datasets, cost tracking, and annotation workflows.",
    tradeoff: "Add it as an export target; do not make your enterprise control plane depend on it."
  },
  {
    name: "LangSmith",
    stance: "LangGraph-native tracing adapter",
    fit: "Strong choice for LangChain/LangGraph traces, datasets, evaluations, debugging, and hosted workflow analysis.",
    tradeoff: "Excellent developer observability; keep HITL/audit source of truth inside AegisAI."
  }
] as const;
