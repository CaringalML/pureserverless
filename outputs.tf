output "api_endpoint" {
  description = "Base URL of the API Gateway endpoint"
  value       = "${aws_apigatewayv2_stage.hello_world.invoke_url}/"
}

output "lambda_function_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.hello_world.function_name
}

output "lambda_function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = aws_lambda_function.hello_world.arn
}
