variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "image_tag" {
  description = "Container image tag to deploy (pushed to ECR before apply)."
  type        = string
  default     = "latest"
}

variable "aegisai_enforce_auth" {
  description = "Value for AEGISAI_ENFORCE_AUTH."
  type        = string
  default     = "false"
}
