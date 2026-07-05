# ADR-0006: PaaS (Render) vs. Real IaC (Terraform + ECS Fargate/RDS/ALB)

## Status

Accepted — 2026-07-05

## Context

Every repo in this org deploys to Render/Vercel PaaS ([ADR-005 in ai-architecture-portfolio](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/adr/ADR-005-reference-stack-free-tier.md)),
which is the right default for iteration speed and near-zero ops overhead — but it left the
whole org with zero evidence of real cloud infrastructure ownership (VPC design, container
orchestration, IAM, load balancing, managed database provisioning), despite that being core
Principal AI Architect / MLOps territory. AegisAI is the flagship governance control plane —
the most narratively important service in the org to show running on a classic enterprise AWS
pattern, so Phase C of the top-1% AI Architect program targeted it specifically.

## Decision

Added `deploy/terraform/aws/`: VPC (public subnets only, no NAT Gateway), ECS Fargate, an
Application Load Balancer, RDS Postgres (`db.t4g.micro`, single-AZ), IAM execution/task roles,
and Secrets Manager for `DATABASE_URL` — a real, alternative deploy path to `render.yaml`, not
a replacement for it.

**When Render/Vercel PaaS is the right call:** fast iteration, no dedicated ops capacity,
traffic low enough that PaaS free/starter tiers cover it, and the team doesn't need direct
control over networking or IAM boundaries. This describes AegisAI's normal operating mode
today.

**When Terraform + ECS/RDS/ALB earns its complexity:** when you need direct control over VPC
network boundaries, IAM roles scoped per-service (an execution role that can only pull this
image and read this one secret, a task role separate from that), or load-balancer-level
routing/health-check behavior PaaS abstracts away. None of that was needed here — this was
built to gain and demonstrate that operational capability, not because AegisAI's traffic or ops
needs outgrew Render.

## Consequences

### Positive
- Real, verified deploy: `terraform apply` created 26 real AWS resources; the live service's
  `/health` endpoint confirmed `"persistence":{"mode":"postgres"}` (genuinely connected to
  RDS, not falling back to SQLite); a real `POST /api/orchestrators/website-build/run` call
  completed successfully against the live ECS Fargate task; `terraform destroy` cleanly removed
  everything — a genuine stand-up/verify/tear-down cycle.
- Found and fixed two real bugs only real deployment could surface: the `Dockerfile` couldn't
  build at all (the `python:3.13-slim` base has no `git`, and `requirements.txt` depends on
  `agent-finops` via a `git+https` source — this had apparently never been built as a real
  container image since that dependency was added), and the ECR repository couldn't be torn
  down without `force_delete = true` since it still held the pushed image.
- A transient AWS eventual-consistency issue (ECS tried to read a just-created Secrets Manager
  value before it fully propagated) resolved itself on `aws ecs update-service --force-new-
  deployment` — documented here as an operational note, not a Terraform bug.
- Documents a genuine engineering trade-off (when to reach for IaC vs. PaaS) rather than
  reflexively treating "more infrastructure" as inherently better.

### Negative
- Real, if temporary, cloud spend: the ALB costs roughly $16/month whether or not it's serving
  traffic, and the Fargate task + RDS add roughly $20–30/month combined while running.
  Mitigated by the stand-up/verify/tear-down operating model — this is not left running as a
  second production deployment of AegisAI.
- Public subnets only (no NAT Gateway) means the ECS task gets a public IP directly, rather
  than the more common private-subnet-plus-NAT pattern — a deliberate cost trade-off (~$32/mo
  saved), not the default enterprise topology; worth calling out explicitly rather than
  presenting it as unqualified best practice.

## References
- `deploy/terraform/aws/` (main.tf, ecs.tf, rds.tf, secrets.tf, variables.tf, outputs.tf, README.md)
- `render.yaml` (the PaaS path this doesn't replace)
- [agent-finops ADR-0002](https://github.com/vpeetla-ai/agent-finops/blob/main/docs/adr/0002-paas-vs-iac-deploy-tradeoffs.md) (the equivalent decision on GCP for agent-finops)
- [ai-architecture-portfolio ADR-015](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/adr/ADR-015-real-aws-gcp-infra-phase-c.md)
