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
  source_dir    = "${path.module}/../src/lambdas/fetcher"
  handler       = "fetcher_lambda.lambda_handler"
  
  environment_variables = {
    REDDIT_CLIENT_ID     = var.reddit_client_id
    REDDIT_CLIENT_SECRET = var.reddit_client_secret
    SQS_QUEUE_URL        = module.ingestion_queue.queue_url
  }
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
  source_dir    = "${path.module}/../src/lambdas/ingest"
  handler       = "ingest_lambda.lambda_handler"
  
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