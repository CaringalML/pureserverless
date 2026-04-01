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
      DATABASE_URL           = var.database_url
    }
  }

  tags = {
    Environment = var.environment
  }
}
