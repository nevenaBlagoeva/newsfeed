# SQS Queue for news ingestion
module "ingestion_queue" {
  source = "./modules/sqs"
  
  queue_name = "newsfeed-ingestion-queue"
}

# DynamoDB table for raw events
module "raw_events_table" {
  source = "./modules/dynamodb"
  
  table_name = "RawEvents"
}

# Fetcher Lambda (triggered by EventBridge, pushes to SQS)
module "fetcher_lambda" {
  source = "./modules/lambda"
  
  function_name = "newsfeed-fetcher"
  handler       = "fetcher_lambda.lambda_handler"
  commit_sha    = var.commit_sha

  environment_variables = {
    REDDIT_CLIENT_ID     = var.reddit_client_id
    REDDIT_CLIENT_SECRET = var.reddit_client_secret
    SQS_QUEUE_URL        = module.ingestion_queue.queue_url
  }

}

# EventBridge rule to trigger fetcher lambda
module "fetcher_schedule" {
  source = "./modules/eventbridge"
  rule_name           = "newsfeed-hourly-fetch"
  description         = "Trigger news fetcher every hour"
  schedule_expression = "rate(1 hour)"
  lambda_function_arn = module.fetcher_lambda.lambda_function_arn
  lambda_function_name = module.fetcher_lambda.lambda_function_name
}

# Add SQS permissions to fetcher lambda
resource "aws_iam_role_policy" "fetcher_sqs_policy" {
  name = "fetcher-sqs-policy"
  role = module.fetcher_lambda.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = module.ingestion_queue.queue_arn
      }
    ]
  })
}

# Ingest Lambda (processes SQS messages, writes to DynamoDB)
module "ingest_lambda" {
  source = "./modules/lambda"
  
  function_name = "newsfeed-ingest"
  handler       = "ingest_lambda.lambda_handler"
  commit_sha    = var.commit_sha

  environment_variables = {
    DYNAMODB_TABLE_NAME = module.raw_events_table.table_name
  }
}

# SQS trigger for ingest lambda
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = module.ingestion_queue.queue_arn
  function_name    = module.ingest_lambda.lambda_function_name
  batch_size       = 10
}

# DynamoDB permissions for ingest lambda
resource "aws_iam_role_policy" "ingest_dynamodb_policy" {
  name = "ingest-dynamodb-policy"
  role = module.ingest_lambda.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ]
        Resource = module.raw_events_table.table_arn
      }
    ]
  })
}

# SQS permissions for ingest lambda (to receive messages)
resource "aws_iam_role_policy" "ingest_sqs_policy" {
  name = "ingest-sqs-policy"
  role = module.ingest_lambda.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = module.ingestion_queue.queue_arn
      }
    ]
  })
}

# DynamoDB table for filtered events
module "filtered_events_table" {
  source = "./modules/dynamodb"
  
  table_name     = "FilteredEvents"
  hash_key       = "PK"
  range_key      = "SK"
  range_key_type = "S"  # SK is a string with format "relevance#timestamp"
}

# Filter Lambda (processes DynamoDB stream, writes to FilteredEvents)
module "filter_lambda" {
  source = "./modules/lambda"
  
  function_name = "newsfeed-filter"
  handler       = "filter_lambda.lambda_handler"
  commit_sha    = var.commit_sha
  
  environment_variables = {
    FILTERED_TABLE_NAME = module.filtered_events_table.table_name
  }
}

# DynamoDB stream trigger for filter lambda
resource "aws_lambda_event_source_mapping" "dynamodb_stream_trigger" {
  event_source_arn  = module.raw_events_table.stream_arn
  function_name     = module.filter_lambda.lambda_function_name
  starting_position = "LATEST"
  batch_size        = 10
}

# DynamoDB permissions for filter lambda
resource "aws_iam_role_policy" "filter_dynamodb_policy" {
  name = "filter-dynamodb-policy"
  role = module.filter_lambda.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem"
        ]
        Resource = module.filtered_events_table.table_arn
      }
    ]
  })
}

# DynamoDB stream permissions for filter lambda
resource "aws_iam_role_policy" "filter_stream_policy" {
  name = "filter-stream-policy"
  role = module.filter_lambda.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeStream",
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator"
        ]
        Resource = module.raw_events_table.stream_arn
      }
    ]
  })
}

# Ingest API Lambda (accepts JSON arrays via API Gateway)
module "ingest_api_lambda" {
  source = "./modules/lambda"
  
  function_name = "newsfeed-ingest-api"
  handler       = "ingest_api_lambda.lambda_handler"
  commit_sha    = var.commit_sha

  environment_variables = {
    DYNAMODB_TABLE_NAME = module.raw_events_table.table_name
  }
}

# DynamoDB permissions for ingest API lambda
resource "aws_iam_role_policy" "ingest_api_dynamodb_policy" {
  name = "ingest-api-dynamodb-policy"
  role = module.ingest_api_lambda.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ]
        Resource = module.raw_events_table.table_arn
      }
    ]
  })
}

# Retrieve Lambda (GET /retrieve endpoint)
module "retrieve_lambda" {
  source = "./modules/lambda"
  
  function_name = "newsfeed-retrieve"
  handler       = "retrieve_lambda.lambda_handler"  # This should match the actual file name
  commit_sha    = var.commit_sha
  
  environment_variables = {
    FILTERED_TABLE_NAME = module.filtered_events_table.table_name
  }
}

# DynamoDB permissions for retrieve lambda
resource "aws_iam_role_policy" "retrieve_dynamodb_policy" {
  name = "retrieve-dynamodb-policy"
  role = module.retrieve_lambda.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query"
        ]
        Resource = module.filtered_events_table.table_arn
      }
    ]
  })
}

# API Gateway for ingest and retrieve endpoints
module "api_gateway" {
  source = "./modules/api_gateway"
  
  ingest_lambda_function_name = module.ingest_api_lambda.lambda_function_name
  ingest_lambda_invoke_arn    = module.ingest_api_lambda.lambda_function_arn
  retrieve_api_lambda_function_name = module.retrieve_lambda.lambda_function_name
  retrieve_api_lambda_invoke_arn    = module.retrieve_lambda.lambda_function_arn
}

# Output the actual API URLs for debugging
output "debug_api_urls" {
  value = {
    base_url = module.api_gateway.api_base_url
    ingest_url = "${module.api_gateway.api_base_url}/ingest"
    retrieve_url = "${module.api_gateway.api_base_url}/retrieve"
  }
}

# Output the dashboard URL (direct S3 object access)
output "dashboard_url" {
  value = "https://${aws_s3_bucket.dashboard.id}.s3.eu-west-1.amazonaws.com/dashboard.html"
}