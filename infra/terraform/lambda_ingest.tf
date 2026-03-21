# ---- IAM role for Lambda ----
resource "aws_iam_role" "ingest_lambda_role" {
  name = "${var.bucket_name}-ingest-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Action    = "sts:AssumeRole",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Basic execution = CloudWatch Logs permissions
resource "aws_iam_role_policy_attachment" "ingest_lambda_basic" {
  role       = aws_iam_role.ingest_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Allow Lambda to write objects to your raw bucket prefix
resource "aws_iam_policy" "ingest_s3_put" {
  name = "${var.bucket_name}-ingest-s3-put"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "PutObjectsToRawPrefix",
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:AbortMultipartUpload"
        ],
        Resource = "arn:aws:s3:::${var.bucket_name}/raw/*"
      },
      {
        Sid    = "ReadBucketLocation",
        Effect = "Allow",
        Action = [
          "s3:GetBucketLocation",
          "s3:ListBucket"
        ],
        Resource = "arn:aws:s3:::${var.bucket_name}"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ingest_s3_put_attach" {
  role       = aws_iam_role.ingest_lambda_role.name
  policy_arn = aws_iam_policy.ingest_s3_put.arn
}

# ---- Lambda function ----
resource "aws_lambda_function" "ingest" {
  function_name = "tx-bid-watch-ingest"
  role          = aws_iam_role.ingest_lambda_role.arn

  runtime = "python3.12"
  handler = "src.handler.lambda_handler"

  filename         = "${path.module}/../../services/ingest/dist/ingest_lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../../services/ingest/dist/ingest_lambda.zip")

  timeout     = 60
  memory_size = 512

  environment {
    variables = {
      RAW_BUCKET     = var.bucket_name
      RAW_PREFIX     = var.raw_prefix
      SODA_DOMAIN    = var.soda_domain
      DATASET_ID     = var.dataset_id
      LOOKBACK_HOURS = tostring(var.lookback_hours)
      PAGE_LIMIT     = tostring(var.page_limit)
      MAX_PAGES      = tostring(var.max_pages)
      SNS_TOPIC_ARN  = aws_sns_topic.ingest_notifications.arn
      CURATE_LAMBDA_NAME = aws_lambda_function.curate.function_name
    }
  }
}