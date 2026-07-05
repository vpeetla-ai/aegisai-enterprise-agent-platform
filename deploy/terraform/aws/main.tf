# Real, running AWS infra for the flagship governance control plane — a
# genuine alternative to the Render/Vercel PaaS path every other repo in this
# org uses, and the most narratively important service to show on a classic
# enterprise AWS pattern (VPC/ECS/ALB/IAM). See
# adr/0006-paas-vs-iac-deploy-tradeoffs.md for when this earns its
# complexity over PaaS. Lowest-cost configuration on purpose: public subnets
# only (no NAT Gateway, saves ~$32/mo), RDS single-AZ smallest burstable
# tier. Intended to be stood up, verified, and torn down per session
# (terraform apply -> verify -> terraform destroy), not left running — the
# ALB (~$16/mo) is the one fixed cost that accrues whether or not it serves
# traffic.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_availability_zones" "available" {
  state = "available"
}

# --- Networking: public subnets only, no NAT Gateway ------------------------

resource "aws_vpc" "main" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "aegisai" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "aegisai" }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.20.${count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = { Name = "aegisai-public-${count.index}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "aegisai-public" }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# --- Security groups ---------------------------------------------------

resource "aws_security_group" "alb" {
  name        = "aegisai-alb"
  description = "Public HTTP ingress to the ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_task" {
  name        = "aegisai-ecs-task"
  description = "ECS task ingress from the ALB only"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name        = "aegisai-rds"
  description = "Postgres ingress from ECS tasks only"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_task.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- ECR ---------------------------------------------------------------

resource "aws_ecr_repository" "aegisai" {
  name                 = "aegisai-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # this repo is meant to be torn down between sessions, images and all
}
