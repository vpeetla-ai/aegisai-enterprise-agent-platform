# ADR 0002: Use Supervised Multi-Agent Orchestration

## Status

Accepted

## Context

The platform needs multiple specialized agents for regulated business workflows. A fully decentralized agent swarm can be flexible, but enterprise workflows require traceability, predictable handoffs, policy enforcement, and clear ownership.

## Decision

Use a supervised orchestrator. The orchestrator owns workflow planning, agent selection, shared context coordination, stop conditions, and submission of action proposals to the AgentOps Control Plane.

Specialized agents own narrow business capabilities. They can update their section of shared context and propose actions, but cannot execute side effects directly.

## Consequences

Positive:

- Clear responsibility chain for audit and review.
- Easier evaluation of each agent's task quality.
- Better control over cost, latency, and tool access.
- Stronger enforcement of evidence and policy requirements.

Negative:

- Less open-ended than peer-to-peer agent collaboration.
- The orchestrator becomes a critical component.
- Workflow design requires explicit agent contracts.

## Mitigations

- Keep agent contracts small and typed.
- Make orchestration plans explainable and auditable.
- Use durable workflow state for resumability.
- Evaluate orchestrator routing accuracy as its own metric.

