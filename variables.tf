variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "ap-southeast-2"
}

variable "lambda_function_name" {
  description = "Base name for the Lambda function"
  type        = string
  default     = "serverless-web-app"
}

variable "environment" {
  description = "Deployment environment (e.g. dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "database_url" {
  description = "Neon Postgres connection string (set via TF_VAR_database_url in GitHub secrets)"
  type        = string
  sensitive   = true
}
