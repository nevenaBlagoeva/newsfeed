# Fetcher Lambda (triggered by EventBridge, pushes to SQS)
module "fetcher_lambda" {
  source = "./modules/lambda"
  
  function_name = "newsfeed-fetcher"
  source_dir    = "${path.module}/../src/lambdas/fetcher"
  handler       = "fetcher.lambda_handler"
}