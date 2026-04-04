# Origin Access Control — CloudFront authenticates to S3 without public bucket
resource "aws_cloudfront_origin_access_control" "drive" {
  name                              = "${var.lambda_function_name}-drive-oac-${var.environment}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "drive" {
  enabled         = true
  comment         = "NovaDrive file delivery — ${var.environment}"
  price_class     = "PriceClass_All"

  origin {
    domain_name              = aws_s3_bucket.drive.bucket_regional_domain_name
    origin_id                = "S3DriveOrigin"
    origin_access_control_id = aws_cloudfront_origin_access_control.drive.id
  }

  default_cache_behavior {
    target_origin_id       = "S3DriveOrigin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    # Require CloudFront signed URLs — anonymous access is denied
    trusted_key_groups = [aws_cloudfront_key_group.drive.id]

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 300   # 5 minutes
    max_ttl     = 3600  # 1 hour
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Environment = var.environment
  }
}
