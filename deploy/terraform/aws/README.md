# AWS deploy — ECS Fargate + RDS + ALB

A real, alternative deploy path to the Render PaaS in the root `render.yaml` — the classic
enterprise AWS pattern (VPC, ECS Fargate, ALB, RDS, IAM). See
[adr/00XX-paas-vs-iac-deploy-tradeoffs.md](../../../adr/) for when this earns its complexity
over the PaaS path.

**Cost while running:** the ALB is the dominant fixed cost at roughly $16/month whether or not
it's serving traffic; the Fargate task (0.5 vCPU / 1GB) and RDS `db.t4g.micro` add roughly
$20–30/month combined. **Operating model: stand up, verify, tear down** —
`terraform destroy` (or at minimum `aws ecs update-service --desired-count 0` and stop the RDS
instance) when not actively verifying, not left running 24/7.

## Prerequisites

- `aws configure` (run this yourself — this repo never handles your raw credentials)
- An AWS account with billing enabled
- `terraform`, `aws` CLI, `docker` installed locally

## Deploy

```bash
cd deploy/terraform/aws
terraform init

# 1. Create the ECR repo first (needed before the image can be pushed)
terraform apply -target=aws_ecr_repository.aegisai

# 2. Build and push the image
REPO_URL=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin "${REPO_URL%/*}"
docker build -t "$REPO_URL:latest" -f ../../../services/api/Dockerfile ../../..
docker push "$REPO_URL:latest"

# 3. Apply everything else (VPC, RDS, ECS, ALB)
terraform apply
```

## Verify

```bash
curl -s "$(terraform output -raw alb_url)/health"
```

## Tear down

```bash
terraform destroy
```
