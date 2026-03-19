output "lambda_function_name" {
  value       = aws_lambda_function.ingest.function_name
  description = "Ingest Lambda function name."
}

output "lambda_function_arn" {
  value       = aws_lambda_function.ingest.arn
  description = "Ingest Lambda function ARN."
}

output "eventbridge_rule_name" {
  value       = aws_cloudwatch_event_rule.ingest_daily.name
  description = "EventBridge rule name for scheduling ingest."
}

output "sns_topic_arn" {
  value       = aws_sns_topic.ingest_notifications.arn
  description = "SNS topic ARN for ingest notifications."
}

output "bucket_name" {
  value       = aws_s3_bucket.this.bucket
  description = "Raw S3 bucket name."
}

output "bucket_arn" {
  value       = aws_s3_bucket.this.arn
  description = "Raw S3 bucket ARN."
}

