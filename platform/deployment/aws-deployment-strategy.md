# AWS Deployment Strategy

## Recommendation

For this portfolio and an early enterprise pilot, deploy AegisAI on AWS with:

- **Frontend:** AWS Amplify Hosting or S3 + CloudFront.
- **Backend API:** AWS App Runner for the simplest container deployment, or ECS Fargate for more enterprise control.
- **LLM:** Amazon Bedrock on-demand models.
- **Transactional DB + Vector DB:** Amazon RDS PostgreSQL with pgvector.
- **Evidence Store:** S3.
- **Async Workflow Events:** EventBridge and SQS.
- **Secrets:** AWS Secrets Manager.
- **Telemetry:** CloudWatch Logs/Metrics, AWS X-Ray or OpenTelemetry collector.

For the complete implementation sequence, use [AWS E2E Deployment Runbook](aws-e2e-deployment-runbook.md).

## Why RDS PostgreSQL + pgvector First

Use RDS PostgreSQL with pgvector for the first production-grade version because it keeps the transactional database and vector memory close together. AWS supports pgvector on RDS PostgreSQL, including HNSW indexing in supported versions. This is usually better for a portfolio or pilot than introducing OpenSearch Serverless immediately.

Use OpenSearch Serverless only when:

- You need high-scale full-text + vector search.
- You have many collections and search-heavy workloads.
- You can justify the minimum OCU cost.

## Deployment Options

### Option 1: Portfolio / Low-Cost Demo

Best for showing the project publicly.

- Amplify Hosting or S3 + CloudFront for Next.js static UI.
- App Runner for FastAPI container.
- RDS PostgreSQL small instance with pgvector.
- Bedrock on-demand.
- CloudWatch logs.

Pros:

- Simple.
- Looks enterprise enough.
- Low operational burden.

Cons:

- Less control than ECS.
- Not ideal for very complex network/security topologies.

### Option 2: Enterprise Pilot

Best for a serious internal enterprise proof of concept.

- CloudFront + S3 or Amplify for UI.
- ECS Fargate behind ALB for FastAPI.
- RDS PostgreSQL Multi-AZ with pgvector.
- Bedrock on-demand with model routing.
- SQS/EventBridge for async workflow events.
- Secrets Manager and KMS.
- CloudWatch + OpenTelemetry.

Pros:

- Good security and scaling posture.
- Easier VPC/network control.
- Works well with private subnets and enterprise IAM patterns.

Cons:

- Higher cost and more setup than App Runner.

### Option 3: Production at Scale

Best when traffic, audit, and retrieval scale justify more managed services.

- ECS Fargate or EKS.
- Aurora PostgreSQL with pgvector or separate vector DB.
- OpenSearch Serverless for hybrid search if needed.
- Bedrock provisioned throughput or inference profiles if volume is predictable.
- S3 evidence lake.
- EventBridge/SQS/Step Functions.
- OpenTelemetry, CloudWatch, X-Ray, GuardDuty, Security Hub.

## Cost Posture

Exact AWS pricing changes by region and usage. The main cost drivers are:

- LLM token volume in Bedrock.
- Always-on compute for API containers.
- RDS instance size and storage.
- Vector/search service choice.
- Logs, traces, and retained audit evidence.

Cost guidance:

- **Lowest-cost portfolio:** UI on Amplify/S3, FastAPI on App Runner or one small ECS/Fargate service, RDS PostgreSQL + pgvector, Bedrock on-demand.
- **Avoid for portfolio unless needed:** OpenSearch Serverless, because it has minimum OCU capacity even when traffic is low.
- **Best enterprise pilot:** ECS Fargate + RDS PostgreSQL/pgvector + Bedrock + SQS/EventBridge.

## Rough Monthly Ranges

These are directional, not a quote:

- **Portfolio demo:** about $50-$200/month if traffic and token usage are low.
- **Enterprise pilot:** about $300-$1,500/month depending on RDS size, container count, logs, and Bedrock tokens.
- **Production scale:** $2,000+/month and highly usage-dependent.

## AWS Services Mapping

| Architecture Layer | AWS Services |
| --- | --- |
| User Layer | IAM Identity Center, Cognito, enterprise IdP federation |
| Experience Layer | Amplify Hosting, S3, CloudFront, WAF |
| Guardrails / Policy | API Gateway or ALB auth, Cedar/OPA service, Bedrock Guardrails |
| AI Orchestration | ECS Fargate/App Runner FastAPI, LangGraph, SQS, EventBridge |
| Data / Knowledge | RDS PostgreSQL + pgvector, S3, optional OpenSearch Serverless |
| Infrastructure | VPC, ECS/App Runner, ECR, Secrets Manager, KMS |
| Telemetry | CloudWatch, X-Ray, OpenTelemetry, CloudTrail |
| Feedback Loop | S3 golden datasets, scheduled eval jobs, Athena/QuickSight |
| HITL | Next.js review UI, approval tasks in Postgres, Slack/Teams integration |
| Approved Execution | EventBridge, SQS, ECS worker/Lambda connector executor |
| Hybrid Retrieval | pgvector + SQL filters + optional OpenSearch BM25/vector |

## Container Boundaries

For deployment, keep the current code layers in one FastAPI container until traffic justifies service decomposition:

- `interfaces/http`: public API adapter behind App Runner or ALB.
- `application/orchestration`: synchronous LangGraph agent path.
- `application/knowledge`: RAG and model gateway.
- `application/guardrails`: blocking policy/risk/eval checks.
- `application/execution`: approved connector execution and idempotency boundary.
- `infrastructure/persistence`: RDS PostgreSQL adapter in production.
- `observability`: Langfuse/LangSmith exporters plus OpenTelemetry collector export.

Split into separate services only when scaling or compliance forces the separation. Premature microservices would add cost and operational load without improving the portfolio signal.
