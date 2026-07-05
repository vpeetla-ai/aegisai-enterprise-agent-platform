# --- Logs -----------------------------------------------------------------

resource "aws_cloudwatch_log_group" "aegisai" {
  name              = "/ecs/aegisai-api"
  retention_in_days = 7 # portfolio/demo instance -- keep log storage cost near zero
}

# --- IAM: execution role (pull image, write logs, read secrets) -----------

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "aegisai-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "execution_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.database_url.arn]
  }
}

resource "aws_iam_role_policy" "execution_secrets" {
  name   = "read-database-url-secret"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.execution_secrets.json
}

# --- IAM: task role (least privilege for the running application) ---------

resource "aws_iam_role" "task" {
  name               = "aegisai-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

# --- ECS cluster, task definition, service ---------------------------------

resource "aws_ecs_cluster" "aegisai" {
  name = "aegisai"
}

resource "aws_ecs_task_definition" "aegisai" {
  family                   = "aegisai-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"  # 0.5 vCPU -- smallest Fargate size that runs this API comfortably
  memory                   = "1024" # 1 GB
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "aegisai-api"
      image     = "${aws_ecr_repository.aegisai.repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]
      environment = [
        { name = "AEGISAI_DB_BACKEND", value = "postgres" },
        { name = "AEGISAI_ENFORCE_AUTH", value = var.aegisai_enforce_auth },
      ]
      secrets = [
        { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.aegisai.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "aegisai" {
  name            = "aegisai-api"
  cluster         = aws_ecs_cluster.aegisai.id
  task_definition = aws_ecs_task_definition.aegisai.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_task.id]
    assign_public_ip = true # no NAT Gateway -- tasks need a public IP to reach the internet directly
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.aegisai.arn
    container_name   = "aegisai-api"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.aegisai]
}

# --- ALB ---------------------------------------------------------------

resource "aws_lb" "aegisai" {
  name               = "aegisai"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "aegisai" {
  name        = "aegisai-api"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip" # required for Fargate tasks

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 15
    timeout             = 5
  }
}

resource "aws_lb_listener" "aegisai" {
  load_balancer_arn = aws_lb.aegisai.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.aegisai.arn
  }
}
