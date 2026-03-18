resource "aws_cloudwatch_event_rule" "ingest_daily" {
  name                = "tx-bid-watch-ingest-daily"
  description         = "Run tx-bid-watch ingest Lambda daily"
  schedule_expression = "rate(24 hours)"
}

resource "aws_cloudwatch_event_target" "ingest_daily_target" {
  rule      = aws_cloudwatch_event_rule.ingest_daily.name
  target_id = "tx-bid-watch-ingest"
  arn       = aws_lambda_function.ingest.arn
}

resource "aws_lambda_permission" "allow_eventbridge_invoke" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ingest_daily.arn
}