resource "aws_sns_topic" "ingest_notifications" {
  name = "tx-bid-watch-ingest-notifications"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.ingest_notifications.arn
  protocol  = "email"
  endpoint  = "rileymcnair3@gmail.com"
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