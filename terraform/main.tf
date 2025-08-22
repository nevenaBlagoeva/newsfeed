# SQS Queue for news ingestion
module "ingestion_queue" {
  source = "./modules/sqs"
  
  queue_name = "newsfeed-ingestion-queue"
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