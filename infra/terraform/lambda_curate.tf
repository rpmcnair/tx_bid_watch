# ---- IAM role for Curate Lambda ----
resource "aws_iam_role" "curate_lambda_role" {
  name = "${var.bucket_name}-curate-lambda-role"

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
resource "aws_iam_role_policy_attachment" "curate_lambda_basic" {
  role       = aws_iam_role.curate_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "curate_athena_access" {
  name = "${var.bucket_name}-curate-athena-access"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "AthenaQueryAccess",
        Effect = "Allow",
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults"
        ],
        Resource = "*"
      },
      {
        Sid    = "GlueCatalogRead",
        Effect = "Allow",
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions"
        ],
        Resource = "*"
      },
      {
        Sid    = "ListBucket",
        Effect = "Allow",
        Action = [
          "s3:GetBucketLocation",
          "s3:ListBucket"
        ],
        Resource = "arn:aws:s3:::${var.bucket_name}"
      },
      {
        Sid    = "AthenaResultsAndCuratedObjects",
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ],
        Resource = [
          "arn:aws:s3:::${var.bucket_name}/athena-results/*",
          "arn:aws:s3:::${var.bucket_name}/curated/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "curate_athena_access_attach" {
  role       = aws_iam_role.curate_lambda_role.name
  policy_arn = aws_iam_policy.curate_athena_access.arn
}

resource "aws_lambda_function" "curate" {
  function_name = "tx-bid-watch-curate"
  role          = aws_iam_role.curate_lambda_role.arn

  runtime = "python3.12"
  handler = "src.curate_handler.lambda_handler"

  filename         = "${path.module}/../../services/ingest/dist/ingest_lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../../services/ingest/dist/ingest_lambda.zip")

  timeout     = 300
  memory_size = 512

  environment {
    variables = {
      ATHENA_DATABASE = "tx_bid_watch"
      ATHENA_WORKGROUP = "primary"
      ATHENA_OUTPUT   = "s3://${var.bucket_name}/athena-results/"
      SNS_TOPIC_ARN   = aws_sns_topic.ingest_notifications.arn
    }
  }
}

resource "aws_iam_policy" "ingest_invoke_curate" {
  name = "${var.bucket_name}-ingest-invoke-curate"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "InvokeCurateLambda",
        Effect = "Allow",
        Action = [
          "lambda:InvokeFunction"
        ],
        Resource = aws_lambda_function.curate.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ingest_invoke_curate_attach" {
  role       = aws_iam_role.ingest_lambda_role.name
  policy_arn = aws_iam_policy.ingest_invoke_curate.arn
}

resource "aws_iam_role_policy_attachment" "curate_lambda_sns_publish_attach" {
  role       = aws_iam_role.curate_lambda_role.name
  policy_arn = aws_iam_policy.lambda_sns_publish.arn
}