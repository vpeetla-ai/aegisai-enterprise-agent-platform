# Tradeoff Discussion

## 0. Layered Backend vs Flat Demo Package

**Decision:** Use layered bounded contexts.

**Why:** A flat package is easy for demos but weak for enterprise storytelling. Separating `domain`, `application`, `infrastructure`, `interfaces`, and `observability` makes ownership, test boundaries, and future replacement paths clearer.

**Tradeoff:** More folders and import paths. The mitigation is a single stable `aegisai.api` entrypoint while implementation code uses layered packages.

## 1. Centralized Control Plane vs Embedded Governance In Each Agent

**Decision:** Use a centralized control plane.

**Why:** Enterprise teams need consistent approval, audit, and evaluation across many agents. Embedding governance separately into each agent creates policy drift and inconsistent evidence.

**Tradeoff:** A central platform adds integration work and can become a bottleneck if poorly designed. The mitigation is a stable proposal API, low-latency synchronous checks, async deep evaluations, and reusable SDKs.

## 2. Risk-Based HITL vs Approval For Every Action

**Decision:** Use risk-based approvals.

**Why:** Approving every action destroys automation value. Approving no actions creates unacceptable enterprise risk. Risk-based HITL preserves speed for low-risk work and accountability for consequential actions.

**Tradeoff:** Risk scoring can be wrong. The mitigation is policy simulation, conservative defaults, evaluation feedback, threshold monitoring, and periodic human review of auto-approved samples.

## 3. Policy-as-Code vs Admin UI Rules Only

**Decision:** Use policy-as-code with an admin UI as a controlled front end.

**Why:** Approval logic must be versioned, reviewed, tested, and reproducible. Pure UI configuration often lacks peer review and regression testing.

**Tradeoff:** Policy-as-code requires engineering discipline. The mitigation is templates, linting, dry-run simulation, and business-readable reason codes.

## 4. Synchronous Evaluation Gates vs Asynchronous Evaluation

**Decision:** Use both.

**Why:** Blocking gates should catch severe safety, compliance, grounding, or schema failures before execution. Broader trend analysis, drift detection, and LLM-judge review can run asynchronously.

**Tradeoff:** Synchronous gates increase latency. The mitigation is to keep blocking gates narrow and deterministic where possible, with budgeted LLM calls only for high-risk actions.

## 5. Immutable Event Ledger vs Mutable Audit Tables

**Decision:** Use append-only audit events with queryable read models.

**Why:** Auditors need trustworthy evidence. Mutable audit tables are easier to query but weaker for tamper evidence.

**Tradeoff:** Event sourcing adds operational complexity. The mitigation is to separate write-optimized immutable events from read-optimized projections.

## 6. LLM-as-Judge vs Human Evaluation

**Decision:** Combine LLM-as-judge, rule-based checks, and human evaluation.

**Why:** No single method captures quality. LLM judges scale semantic assessment, rules catch deterministic violations, and humans remain necessary for high-impact subjective decisions.

**Tradeoff:** LLM-as-judge can be biased or inconsistent. The mitigation is calibration sets, judge versioning, multi-metric scoring, and spot-checking by humans.

## 7. Auto-Approve Low-Risk Actions vs Require Reviewer Sampling

**Decision:** Auto-approve low-risk actions but sample a percentage for post-hoc review.

**Why:** This keeps operations fast while giving the organization a quality signal on what the system is silently approving.

**Tradeoff:** Sampling can miss rare failures. The mitigation is targeted sampling for new workflows, new models, high-volume actions, and actions near policy thresholds.

## 8. One Generic Risk Model vs Domain-Specific Risk Models

**Decision:** Use a common scoring framework with domain-specific weights and policies.

**Why:** Common structure makes the platform reusable, while domain-specific weights capture differences between payments, data access, customer communication, and operations.

**Tradeoff:** Too much customization can fragment the platform. The mitigation is a shared canonical risk contract and a policy registry with review governance.

## 9. Native Control Plane Observability vs Langfuse/LangSmith as Source of Truth

**Decision:** Keep AegisAI as the system of record and integrate Langfuse/LangSmith as optional exporters.

**Why:** HITL, audit, policy routing, and regulated workflow state must remain inside the enterprise control plane. Langfuse and LangSmith are excellent for LLM trace analysis, evals, prompt iteration, and debugging, but they should not own approval authority.

**Tradeoff:** The product maintains its own observability schema and adapters. The mitigation is a neutral `ObservabilityService` and exporter status endpoint.
