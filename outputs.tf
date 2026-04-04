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

output "drive_bucket_name" {
  description = "S3 bucket name for NovaDrive file storage"
  value       = aws_s3_bucket.drive.bucket
}

output "cloudfront_domain" {
  description = "CloudFront domain for serving NovaDrive files"
  value       = aws_cloudfront_distribution.drive.domain_name
}

output "acm_validation_cname_name" {
  description = "STEP 1 — Add this CNAME record NAME in Cloudflare (proxy OFF) to validate ACM cert"
  value       = tolist(aws_acm_certificate.main.domain_validation_options)[0].resource_record_name
}

output "acm_validation_cname_value" {
  description = "STEP 1 — Add this CNAME record VALUE in Cloudflare (proxy OFF) to validate ACM cert"
  value       = tolist(aws_acm_certificate.main.domain_validation_options)[0].resource_record_value
}

output "cloudflare_cname_target" {
  description = "STEP 2 — After cert is validated, point drive CNAME to this in Cloudflare (proxy ON)"
  value       = aws_apigatewayv2_domain_name.main.domain_name_configuration[0].target_domain_name
}
