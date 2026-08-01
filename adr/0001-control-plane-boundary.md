# ADR 0001: Put Approval Authority In A Separate Control Plane

## Status

Accepted

## In one breath (panel)

I'd put an independent control plane in front of irreversible tools — agents propose, the gateway decides with policy + HITL + audit, and the agent graph never gets a back door.

## Context

Agents that can deploy, notify, or call money APIs without a shared approval path are a compliance and safety scar waiting to happen. Every team reinventing its own "are we sure?" check produces soft multi-tenancy theater: different rules, no common audit, and nobody who can answer "who approved this?" under pressure.

I refused merging governance into each LangGraph. Orchestration owns *what to try*; a separate plane owns *whether it may execute*.

## Decision

Agents may propose actions. The AegisAI Control Plane owns risk scoring, policy evaluation, human approval, approval-token issuance, execution authorization, and audit logging.

Demo vs Strict: the gateway path is Implemented. OPA can still fail open (advisory → HITL) when unavailable — that is labeled, not sold as hard enterprise fail-closed.

## Consequences

**What we gained**

- One governance contract across orchestrators and consumers
- Reusable approval + evaluation instead of per-agent snowflakes
- Audit you can actually hand a reviewer

**What we gave up**

- Every runtime must integrate the gateway — that's a platform dependency, not a library import
- Latency and reliability of the control plane become part of the agent SLO story (we don't invent numbers here; we design for idempotency and graceful degradation)

## Mitigations

- SDKs + a stable proposal API
- Keep the low-risk synchronous path fast
- Async workflows for HITL and deep evaluation
- Execution broker designed for idempotency, retries, and degradation
