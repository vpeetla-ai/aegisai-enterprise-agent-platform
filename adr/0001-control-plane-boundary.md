# ADR 0001: Put Approval Authority In A Separate Control Plane

## Status

Accepted

## Context

AI agents need to interact with enterprise systems, but direct tool execution creates risks around compliance, safety, duplicate side effects, and auditability. Each agent team could build its own approval logic, but that would lead to inconsistent controls and duplicated effort.

## Decision

Agents may propose actions, but the AegisAI Control Plane owns risk scoring, policy evaluation, human approval workflow, approval token issuance, execution authorization, and audit logging.

## Consequences

Positive:

- Consistent governance across agents.
- Reusable approval and evaluation infrastructure.
- Stronger audit and compliance posture.
- Lower burden on individual agent teams.

Negative:

- Requires integration with all agent runtimes and enterprise systems.
- Adds a platform dependency to agent execution.
- Needs careful latency and reliability engineering.

## Mitigations

- Provide SDKs and a stable proposal API.
- Keep low-risk synchronous path fast.
- Use async workflows for human approval and deep evaluation.
- Design the execution broker for idempotency, retries, and graceful degradation.

