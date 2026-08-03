# ADR-0006: PaaS (Render) vs. Real IaC (Terraform + ECS Fargate/RDS/ALB)

## Status

Accepted — 2026-07-05

## In one breath (panel)

I'd keep Render as the day-to-day path and prove ECS/RDS/ALB with a real apply → health → tear-down — IaC when you need VPC/IAM control, not because "more infra" sounds Principal.

## Context

Org default is Render/Vercel PaaS ([portfolio ADR-005](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/adr/ADR-005-reference-stack-free-tier.md)) — right for iteration speed. That left zero *operated* evidence of VPC, containers, IAM, ALB, managed DB — despite that being core Architect/MLOps territory.

AegisAI is the flagship governance plane, so Phase C targeted it. What I refused: replacing PaaS with AWS as the permanent second production, or pretending free-tier Render equals enterprise SLOs.

## Decision

Added `deploy/terraform/aws/`: VPC (public subnets only, no NAT), ECS Fargate, ALB, RDS Postgres (`db.t4g.micro`, single-AZ), IAM roles, Secrets Manager for `DATABASE_URL`. Alternative path to `render.yaml`, not a replacement.

**When PaaS wins:** fast iteration, no dedicated ops, traffic fits free/starter, no need for direct networking/IAM. That's normal operating mode today.

**When Terraform + ECS/RDS/ALB earns it:** VPC boundaries, per-service IAM, LB health/routing PaaS hides. Built here to *demonstrate* that capability — AegisAI traffic did not outgrow Render.

## Consequences

### Positive

- Verified cycle: `terraform apply` → live `/health` with `"persistence":{"mode":"postgres"}` → real website-build run on Fargate → `destroy`
- Surfaced real bugs only deploy finds (Dockerfile missing `git` for `git+https` dep; ECR needed `force_delete`)
- Documents the trade-off instead of "infra good, PaaS bad"

### Negative

- Real temporary spend (ALB ~$16/mo whether idle; Fargate+RDS roughly $20–30/mo while up) — mitigated by stand-up/verify/tear-down, not a second always-on prod
- Public subnets only (no NAT) = public task IP — deliberate cost trade-off (~$32/mo saved), not the default private+NAT enterprise topology. Call that out; don't sell it as unqualified best practice.

## References

- `deploy/terraform/aws/`
- `render.yaml` (PaaS path this doesn't replace)
- [agent-finops ADR-0002](https://github.com/vpeetla-ai/agent-finops/blob/main/docs/adr/0002-paas-vs-iac-deploy-tradeoffs.md)
- [ai-architecture-portfolio ADR-015](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/adr/ADR-015-real-aws-gcp-infra-phase-c.md)
