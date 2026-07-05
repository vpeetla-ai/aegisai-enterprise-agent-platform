resource "aws_secretsmanager_secret" "database_url" {
  name                    = "aegisai/database-url"
  recovery_window_in_days = 0 # portfolio/demo instance -- allow immediate deletion on teardown
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql://${aws_db_instance.aegisai.username}:${random_password.db_password.result}@${aws_db_instance.aegisai.endpoint}/${aws_db_instance.aegisai.db_name}"
}
