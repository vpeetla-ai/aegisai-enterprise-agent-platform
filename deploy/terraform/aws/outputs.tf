output "alb_url" {
  description = "Live URL of the deployed aegisai API behind the ALB."
  value       = "http://${aws_lb.aegisai.dns_name}"
}

output "ecr_repository_url" {
  description = "ECR repository to push the container image to before apply."
  value       = aws_ecr_repository.aegisai.repository_url
}

output "rds_endpoint" {
  description = "RDS endpoint (only reachable from ECS tasks in the same VPC)."
  value       = aws_db_instance.aegisai.endpoint
}
