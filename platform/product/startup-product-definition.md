# AegisAI Startup Product Definition

## Product Thesis

Enterprises are adopting AI agents faster than they can govern them. The winning product is not another agent builder; it is the runtime control plane that lets enterprises safely discover, govern, approve, evaluate, execute, and audit agentic work.

**AegisAI is the Agent Governance Gateway and Control Plane for governed agentic work.**

The main product surface is the control plane. Reference multi-agent workflows are included to prove how the platform governs real agent behavior, but the commercial product is the layer enterprises use to discover, govern, evaluate, monitor, approve, execute, and audit agents across frameworks.

## One-Line Positioning

AegisAI stops unsafe AI agent actions before they hit production systems, then proves every allow, block, approval, freeze, execution, and audit decision with signed evidence.

## Problem We Solve

Enterprise AI teams are facing five converging problems:

1. **Agent sprawl:** teams create agents in different tools without a central inventory.
2. **Tool risk:** agents can request refunds, data changes, access grants, messages, and operational changes without consistent controls.
3. **Policy opacity:** business owners cannot easily see why an action auto-approved, escalated, or blocked.
4. **Audit gaps:** compliance teams cannot reconstruct who approved what, why, and what was executed.
5. **Unclear ROI:** leaders cannot tell which agents reduce cycle time, protect money, or create risk.

## Who It Helps

| Persona | Pain | AegisAI Outcome |
| --- | --- | --- |
| VP Enterprise AI / AI Platform Lead | Agents are moving from experiments to production without standard controls | Central runtime governance, registry, policy simulation, and release evidence |
| CIO / CTO | AI initiatives lack operational accountability and measurable value | Business-value dashboards, agent ownership, deployment posture, and cost visibility |
| CISO / Security Architect | Agent identities and tool access are hard to control | Agent inventory, least-privilege tool permissions, and kill-switch paths |
| Risk / Compliance / Audit | Cannot prove why an AI action happened | Hash-chained audit packets with policy, evidence, reviewer, and execution trail |
| Operations Leader | Manual approvals are slow but full autonomy is unsafe | Graduated autonomy, HITL queues, and approval-gated execution |
| Support / Finance Ops Manager | Refunds, disputes, and data requests are repetitive and risky | Faster cycle time with governed automation and exception handling |

## Initial Wedge

Start with **Regulated Customer Operations**:

- Refunds and credits
- Payment disputes and chargebacks
- Fee reversals
- Customer complaints
- Account corrections
- Data deletion/export requests
- Fraud or compliance escalations

This wedge is strong because it has clear money movement, data sensitivity, approval thresholds, audit needs, and measurable operational value.

## Highest-Value Product Additions Implemented

1. **Gateway-first product story:** `/api/platform/gateway-story` and the main UI now lead with the runtime intercept flow: agent tool request, gateway check, policy/eval/HITL decision, execution token, and signed evidence.
2. **15-minute developer integration:** `/api/platform/developer-quickstart` explains how external LangGraph, OpenAI Agents SDK, Bedrock, MCP, Copilot Studio, Agentforce, or custom agents plug into AegisAI.
3. **Regulated customer-ops demo:** `/api/product/regulatory-customer-ops-demo` gives a concrete buyer-understandable scenario across RAG, refund, CRM, customer communication, and audit.
4. **Policy Studio dry-run:** `/api/policy/studio/dry-run` returns generated policy preview, dry-run decision, blast radius, and promotion checklist.
5. **Agent identity graph:** `/api/identity/graph` shows agents, owners, principals, tools, tool grants, and highest-risk paths.
6. **Assurance Vault:** `/api/audit-vault/posture` defines evidence types, retention posture, compliance mapping, and export formats.
7. **FinOps ROI:** `/api/finops/dashboard` includes workflow-level ROI metrics, estimated loss prevented, review minutes saved, and autonomy ROI score.
8. **Product consolidation UI:** the control plane exposes these buyer-facing modules before reference examples so the commercial platform is obvious.
9. **Gateway SDK contracts:** `/api/platform/gateway-sdks` defines Python, TypeScript, and MCP proxy adoption contracts.
10. **Historical policy replay:** `/api/policy/replay` shows what a candidate policy would have changed across prior agent actions.
11. **Agent lifecycle:** `/api/agent-registry/lifecycle` registers and promotes agents through shadow, pilot, restricted, approved, revoked, and deprecated states.
12. **Permission matrix:** `/api/identity/permission-matrix` shows each agent-to-tool permission posture.
13. **Release promotion gates:** `/api/release-gates/promote` gates prompt, model, retrieval, and tool releases before production.
14. **Incident timeline:** `/api/incidents/timeline` explains freeze, investigation, remediation, and unfreeze operations.
15. **Deployment posture:** `/api/platform/deployment-posture` separates local demo, low-cost cloud, and AWS enterprise paths.
16. **Flagship demo flow:** `/api/demo/flagship-flow` gives a single buyer-ready walkthrough from refund request to signed audit.

## Product Modules

### 1. Discover

Inventory every agent and its operational posture.

- Agent registry
- Owner and domain
- Model/provider/version
- Tools allowed
- Data classification allowed
- Risk tier
- Autonomy level
- Status and last run
- Monthly cost and incident posture

### 2. Govern

Decide whether agent work can proceed.

- Policy simulator
- Risk scoring
- Evaluation gates
- HITL approval routing
- Reviewer packet
- Role and tenant boundary
- Langfuse/LangSmith telemetry posture

### 3. Execute

Run only approved side effects.

- Tool gateway
- Execution broker
- Idempotency
- Connector allowlist
- External reference
- Rollback reference
- Audit event
- Incident and kill switch

### 4. Assure

Prove what happened for audit and compliance.

- JSON audit packet
- PDF audit packet
- Agent trace evidence
- Governance decisions
- Reviewer actions
- Execution result
- Audit-chain validity

### 5. Secure

Control agent identities, reviewer authority, and tool grants.

- Mock enterprise principal registry
- Reviewer role enforcement
- Tenant boundary checks
- Tool permission enforcement
- Least-privilege posture

### 6. Evaluate

Prevent prompt, model, retrieval, and tool regressions.

- Golden dataset cases
- Release gate
- Average score
- Category-level results
- Promotion recommendation

### 7. Enforce

Control every side-effecting tool call at runtime.

- Governance gateway
- Agent identity check
- Kill-switch check
- Policy and risk simulation
- Evaluation gate result
- HITL routing
- Execution token or block decision

### 8. Onboard

Move agents from shadow/pilot to production with explicit launch controls.

- Agent owner
- Business domain
- Autonomy level
- Tool scopes
- Data classes
- Policy attachment
- Eval suite attachment
- Observability and kill-switch readiness

### 9. Readiness

Give every agent a production posture score.

- Production readiness score
- Missing controls
- Launch decision
- Required approver
- Remediation checklist

### 10. Integrate

Govern agents built outside the platform.

- LangGraph native reference workload
- OpenAI Agents/API gateway adapter
- AWS Bedrock Agents adapter path
- Copilot Studio / Agentforce registry posture
- Langfuse / LangSmith trace export
- Slack/Teams approvals and ServiceNow/Jira incidents

### 11. Gateway Developer Experience

Make the runtime gateway easy to adopt.

- Agent registration path
- Production-readiness scoring
- Gateway SDK quickstart
- Scoped execution token contract
- OpenAI/LangGraph/Bedrock/MCP integration guidance
- Local demo path and AWS enterprise path

### 12. Policy Studio

Let platform, risk, and operations teams change policy safely.

- Natural-language business rule framing
- Generated policy preview
- Dry-run decision
- Historical blast-radius estimate
- Promotion checklist
- Versioned rollback posture

### 13. Identity Graph

Show the blast radius of agent identities and tool authority.

- Agents
- Owners
- Tenants
- Principals
- Tools
- Tool grants
- Highest-risk paths
- Recommended controls

### 14. Assurance Vault

Package governance evidence for compliance, risk, and leadership.

- Signed JSON/PDF/GRC export bundle
- Retention policy
- Trace, policy, eval, reviewer, execution, and cost evidence
- NIST AI RMF, SOC 2, and EU AI Act-style control mapping

## Differentiation

| Existing Category | Gap | AegisAI Differentiation |
| --- | --- | --- |
| Agent frameworks | Build agents, but do not govern enterprise execution | Runtime control plane across agents, tools, approvals, and audit |
| LLM observability | Great traces, weak approval authority | Observability plus source-of-truth HITL, policy, and execution state |
| Workflow automation | Automates tasks, but not LLM uncertainty and agent behavior | Evaluation gates, risk scoring, autonomy levels, and agent identity |
| GRC tools | Track compliance, but not live agent runtime behavior | Real-time agent action governance and execution control |

## MVP Definition

The MVP should prove:

1. Executive user sees enterprise agent posture: inventory, risk, cost, incidents, freezes, and next actions.
2. AI platform user onboards a new agent and sees whether it can launch.
3. Runtime gateway evaluates a high-risk tool request before side effects happen.
4. Business user runs reference multi-agent scenarios that prove policy, RAG, evals, HITL, and audit.
5. Agent registry shows ownership, allowed tools, risk tier, autonomy level, and production readiness.
6. HITL reviewer approves or blocks with evidence.
7. Execution broker performs only approved actions.
8. Audit trail records the complete chain.

## Success Metrics

- Time to approve high-risk action
- Auto-approval rate for low-risk actions
- Reviewer override rate
- Blocked risky-action count
- Tool execution success rate
- Cost per resolved workflow
- Audit packet completeness
- Policy simulation usage
- Agent inventory coverage
- Gateway SDK adoption by agent team
- Historical policy replay coverage before promotion
- Agent release promotion pass rate
- Incident freeze and unfreeze cycle time

## Next Product Milestones

1. **Agent Registry:** central inventory of agents, owners, tools, risk, and autonomy. Implemented.
2. **Policy Simulator:** what-if interface for risk, evaluation, approval, and block decisions. Implemented.
3. **Audit Packet Export:** PDF/JSON export for case evidence. Implemented.
4. **Agent Identity + RBAC:** tenant, reviewer, and tool-permission enforcement. Implemented.
5. **Incident Kill Switch:** freeze an agent, tool, tenant, or workflow. Implemented.
6. **Golden Dataset Eval Center:** regression gates for prompts, models, retrieval, and tools. Implemented.
7. **Governance Gateway:** runtime control point for side-effecting tool calls. Implemented.
8. **Agent Onboarding:** launch-control workflow for new agents. Implemented.
9. **Production Readiness Score:** score registered agents against required controls. Implemented.
10. **Integration Posture:** explain how AegisAI governs LangGraph, OpenAI, Bedrock, Copilot Studio, Agentforce, and custom agents. Implemented.

## Next Strategic Milestones

1. Make Postgres the default production system of record with migrations, tenant isolation, and deployment smoke tests.
2. Convert the quickstart into real Python and TypeScript gateway SDK packages.
3. Add sidecar/proxy adapters for OpenAI Agents SDK, LangGraph, Bedrock Agents, MCP servers, and generic OpenAPI tools.
4. Add real SSO/OIDC integration and policy-driven reviewer assignment.
5. Add connector marketplace and live Salesforce, ServiceNow, Stripe, Jira, Slack, and Teams adapters.
6. Add historical policy replay against stored audit packets.
7. Add workflow-level cost anomaly detection by agent, tool, tenant, and release version.
