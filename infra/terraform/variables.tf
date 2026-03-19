variable "aws_region" {
  description = "AWS region for resources."
  type        = string
  default     = "us-east-2"
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name."
  type        = string
}

variable "enable_versioning" {
  description = "Enable S3 object versioning."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags applied to resources."
  type        = map(string)
  default     = {}
}

variable "project_name" {
  description = "Project name prefix used for AWS resource names."
  type        = string
  default     = "tx-bid-watch"
}

variable "env" {
  description = "Environment name (dev/prod)."
  type        = string
  default     = "dev"
}

variable "raw_prefix" {
  description = "S3 prefix for raw zone objects."
  type        = string
  default     = "raw"
}

variable "dataset_id" {
  description = "Socrata dataset id."
  type        = string
  default     = "qh8x-rm8r"
}

variable "soda_domain" {
  description = "Socrata domain host."
  type        = string
  default     = "data.texas.gov"
}

variable "lookback_hours" {
  description = "How many hours back to fetch updated rows."
  type        = number
  default     = 24
}

variable "page_limit" {
  description = "Socrata paging $limit."
  type        = number
  default     = 1000
}

variable "max_pages" {
  description = "Max pages to fetch per run."
  type        = number
  default     = 2
}

variable "lambda_function_name" {
  description = "Name of the ingest Lambda function."
  type        = string
  default     = "tx-bid-watch-ingest"
}

variable "schedule_expression" {
  description = "EventBridge schedule expression."
  type        = string
  default     = "rate(24 hours)"
}

variable "notification_email" {
  description = "Email address for SNS subscription (leave empty to skip subscription)."
  type        = string
  default     = ""
}

