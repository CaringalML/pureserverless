output "api_endpoint" {
  description = "Base URL of the API Gateway endpoint"
  value       = "${aws_apigatewayv2_stage.serverless_web_app.invoke_url}/"
}

output "lambda_function_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.serverless_web_app.function_name
}

output "lambda_function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = aws_lambda_function.serverless_web_app.arn
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_client_id" {
  description = "Cognito User Pool App Client ID"
  value       = aws_cognito_user_pool_client.main.id
}
