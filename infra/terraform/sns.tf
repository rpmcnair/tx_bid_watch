resource "aws_sns_topic" "ingest_notifications" {
  name = "tx-bid-watch-ingest-notifications"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.notification_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.ingest_notifications.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

resource "aws_iam_policy" "lambda_sns_publish" {
  name = "tx-bid-watch-lambda-sns-publish"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = ["sns:Publish"],
      Resource = aws_sns_topic.ingest_notifications.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sns_publish_attach" {
  role       = aws_iam_role.ingest_lambda_role.name
  policy_arn = aws_iam_policy.lambda_sns_publish.arn
}