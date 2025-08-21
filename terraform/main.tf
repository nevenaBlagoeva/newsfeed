# Fetcher Lambda (triggered by EventBridge, pushes to SQS)
module "fetcher_lambda" {
  source = "./modules/lambda"
  
  function_name = "newsfeed-fetcher"
  source_dir    = "${path.module}/../src/lambdas/fetcher"
  handler       = "fetcher_lambda.lambda_handler"
  
  environment_variables = {
    REDDIT_CLIENT_ID     = var.reddit_client_id
    REDDIT_CLIENT_SECRET = var.reddit_client_secret
  }
}