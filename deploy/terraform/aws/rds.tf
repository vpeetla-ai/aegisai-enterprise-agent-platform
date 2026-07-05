resource "aws_db_subnet_group" "aegisai" {
  name       = "aegisai"
  subnet_ids = aws_subnet.public[*].id
}

resource "random_password" "db_password" {
  length  = 24
  special = false # keep the URL-safe for a libpq connection string
}

resource "aws_db_instance" "aegisai" {
  identifier     = "aegisai-db"
  engine         = "postgres"
  engine_version = "16"

  instance_class      = "db.t4g.micro" # smallest burstable tier -- lowest cost
  allocated_storage   = 20             # smallest billable size, GB
  storage_type        = "gp3"
  multi_az            = false # no HA replica -- lowest cost, matches this phase's operating model
  publicly_accessible = false # reachable only from ECS tasks in the same VPC, via security group

  db_name  = "aegisai"
  username = "aegisai"
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.aegisai.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 0 # portfolio/demo instance, not a production data store
  skip_final_snapshot     = true
  deletion_protection     = false # this instance is meant to be torn down between sessions
}
