# ADR 0002: Use Supervised Multi-Agent Orchestration

## Status

Accepted

## In one breath (panel)

I'd run specialists under a supervised orchestrator that owns the plan and the stop conditions — peer-to-peer swarms are fun demos; regulated workflows need a clear owner of the handoff.

## Context

We needed multiple specialized agents for business workflows. A fully decentralized swarm looks flexible in a slide deck. In practice it breaks traceability: who decided the next tool call, who held shared context, and who submitted the side-effect proposal?

What I refused: open-ended peer collaboration with no supervisor for paths that can publish, deploy, or spend.

## Decision

Use a supervised orchestrator. It owns workflow planning, agent selection, shared context, stop conditions, and submission of action proposals to the AgentOps Control Plane.

Specialized agents own narrow capabilities. They can update their slice of shared context and propose actions — they cannot execute side effects directly. Side effects go through the gateway (ADR-0001).

## Consequences

**What we gained**

- A responsibility chain a reviewer can follow
- Per-agent eval instead of one opaque swarm score
- Cleaner control of cost, latency, and tool access

**What we gave up**

- Less open-ended than peer-to-peer collaboration
- The orchestrator is a critical component — design it like one
- Workflows need explicit agent contracts (typed, small)

## Mitigations

- Keep agent contracts small and typed
- Make orchestration plans explainable and auditable
- Durable workflow state for resumability
- Evaluate orchestrator routing accuracy as its own metric (when gated — not invented here)
