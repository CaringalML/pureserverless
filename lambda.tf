data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/serverless_web_app"
  output_path = "${path.module}/lambda/serverless_web_app.zip"
}

resource "aws_lambda_function" "serverless_web_app" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.lambda_function_name}-${var.environment}"
  role             = aws_iam_role.lambda_role.arn
  handler          = "wsgi.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 30

  depends_on = [aws_cloudwatch_log_group.lambda]

  environment {
    variables = {
      ENVIRONMENT            = var.environment
      DJANGO_SETTINGS_MODULE = "config.settings.prod"
      # DB credentials fetched from SSM at runtime — not stored as plain text here
      SSM_DATABASE_URL_NAME  = aws_ssm_parameter.database_url.name
      # Cognito — IDs are not secrets, but the actual auth is enforced by Cognito itself
      COGNITO_USER_POOL_ID   = aws_cognito_user_pool.main.id
      COGNITO_CLIENT_ID      = aws_cognito_user_pool_client.main.id
    }
  }

  tags = {
    Environment = var.environment
  }
}
