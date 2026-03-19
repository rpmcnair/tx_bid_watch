resource "aws_cloudwatch_metric_alarm" "ingest_lambda_errors" {
  alarm_name          = "tx-bid-watch-ingest-errors"
  alarm_description   = "Alarm if tx-bid-watch ingest Lambda has any errors in the last day."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 288  # 288 * 5min = 24h
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.ingest.function_name
  }

  alarm_actions = [aws_sns_topic.ingest_notifications.arn]
}

resource "aws_cloudwatch_metric_alarm" "ingest_lambda_duration_high" {
  alarm_name          = "tx-bid-watch-ingest-duration-high"
  alarm_description   = "Alarm if tx-bid-watch ingest Lambda duration is unusually high."
  namespace           = "AWS/Lambda"
  metric_name         = "Duration"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 3
  threshold           = 45000
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.ingest.function_name
  }

  alarm_actions = [aws_sns_topic.ingest_notifications.arn]
}