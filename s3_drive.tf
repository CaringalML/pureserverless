resource "aws_s3_bucket" "drive" {
  bucket = "${var.lambda_function_name}-drive-${var.environment}"

  tags = {
    Environment = var.environment
    Purpose     = "strawdrive-file-storage"
  }
}

resource "aws_s3_bucket_public_access_block" "drive" {
  bucket                  = aws_s3_bucket.drive.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "drive" {
  bucket = aws_s3_bucket.drive.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["https://${var.custom_domain}"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_versioning" "drive" {
  bucket = aws_s3_bucket.drive.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Automatic tiering: Standard → Standard-IA → Glacier Instant Retrieval
resource "aws_s3_bucket_lifecycle_configuration" "drive" {
  bucket = aws_s3_bucket.drive.id

  rule {
    id     = "auto-tiering"
    status = "Enabled"

    filter {}

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }
  }
}

# Only CloudFront (via OAC) can read objects — no direct S3 access
resource "aws_s3_bucket_policy" "drive" {
  bucket = aws_s3_bucket.drive.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAC"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.drive.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.drive.arn
          }
        }
      }
    ]
  })

  depends_on = [aws_cloudfront_distribution.drive]
}
