resource "aws_ssm_parameter" "database_url" {
  name        = "/${var.lambda_function_name}/${var.environment}/database-url"
  description = "Neon Postgres connection string for ${var.lambda_function_name}-${var.environment}"
  type        = "SecureString"
  value       = var.database_url

  tags = {
    Environment = var.environment
  }
}
