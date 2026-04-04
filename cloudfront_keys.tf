# RSA key pair used to sign CloudFront URLs
# Private key stored encrypted in SSM — Lambda reads it at runtime to sign URLs
resource "tls_private_key" "cloudfront_signing" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "aws_ssm_parameter" "cloudfront_private_key" {
  name  = "/${var.lambda_function_name}/${var.environment}/cloudfront-signing-key"
  type  = "SecureString"
  value = tls_private_key.cloudfront_signing.private_key_pem

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudfront_public_key" "drive" {
  name        = "${var.lambda_function_name}-drive-pubkey-${var.environment}"
  encoded_key = tls_private_key.cloudfront_signing.public_key_pem
}

resource "aws_cloudfront_key_group" "drive" {
  name    = "${var.lambda_function_name}-drive-keygroup-${var.environment}"
  items   = [aws_cloudfront_public_key.drive.id]
  comment = "NovaDrive signed URL key group"
}
