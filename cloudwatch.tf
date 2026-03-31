# Imports the log group if Lambda already auto-created it on first invocation.
# Once it's in state this block is a no-op on subsequent applies.
import {
  to = aws_cloudwatch_log_group.lambda
  id = "/aws/lambda/serverless-web-app-dev"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.lambda_function_name}-${var.environment}"
  retention_in_days = 14

  tags = {
    Environment = var.environment
  }
}
