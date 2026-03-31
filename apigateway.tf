resource "aws_apigatewayv2_api" "hello_world" {
  name          = "${var.lambda_function_name}-api-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "OPTIONS"]
    allow_headers = ["Content-Type"]
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_apigatewayv2_stage" "hello_world" {
  api_id      = aws_apigatewayv2_api.hello_world.id
  name        = var.environment
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "hello_world" {
  api_id             = aws_apigatewayv2_api.hello_world.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.hello_world.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "hello_world" {
  api_id    = aws_apigatewayv2_api.hello_world.id
  route_key = "GET /"
  target    = "integrations/${aws_apigatewayv2_integration.hello_world.id}"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hello_world.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.hello_world.execution_arn}/*/*"
}
