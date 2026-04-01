resource "aws_sns_topic" "alerts" {
  name = "${var.lambda_function_name}-alerts-${var.environment}"

  tags = {
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "lawrencecaringal5@gmail.com"
}
