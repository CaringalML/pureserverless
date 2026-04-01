resource "aws_apigatewayv2_api" "serverless_web_app" {
  name          = "${var.lambda_function_name}-api-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type"]
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_apigatewayv2_stage" "serverless_web_app" {
  api_id      = aws_apigatewayv2_api.serverless_web_app.id
  name        = var.environment
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "serverless_web_app" {
  api_id             = aws_apigatewayv2_api.serverless_web_app.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.serverless_web_app.invoke_arn
  integration_method = "POST"
}

# Catch-all route — forwards every method and path to Lambda.
# Django + WhiteNoise handle routing internally (pages, static files, 404s).
resource "aws_apigatewayv2_route" "serverless_web_app" {
  api_id    = aws_apigatewayv2_api.serverless_web_app.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.serverless_web_app.id}"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.serverless_web_app.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.serverless_web_app.execution_arn}/*/*"
}
