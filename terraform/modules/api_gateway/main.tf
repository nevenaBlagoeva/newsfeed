# API Gateway REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = "newsfeed-api"
  description = "Newsfeed API Gateway"
}

# API Gateway resource for /ingest
resource "aws_api_gateway_resource" "ingest" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "ingest"
}

# API Gateway method POST /ingest
resource "aws_api_gateway_method" "ingest_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.ingest.id
  http_method   = "POST"
  authorization = "NONE"
}

# API Gateway integration with Lambda
resource "aws_api_gateway_integration" "ingest_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.ingest.id
  http_method = aws_api_gateway_method.ingest_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.ingest_lambda_invoke_arn
}

# API Gateway resource for /retrieve
resource "aws_api_gateway_resource" "retrieve" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "retrieve"
}

# API Gateway method GET /retrieve
resource "aws_api_gateway_method" "retrieve_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.retrieve.id
  http_method   = "GET"
  authorization = "NONE"
}

# API Gateway integration for retrieve
resource "aws_api_gateway_integration" "retrieve_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.retrieve.id
  http_method = aws_api_gateway_method.retrieve_get.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.retrieve_api_lambda_invoke_arn
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "main" {
  depends_on = [
    aws_api_gateway_integration.ingest_integration,
    aws_api_gateway_integration.retrieve_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.main.id

  # Force new deployment when anything changes
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.ingest.id,
      aws_api_gateway_resource.retrieve.id,
      aws_api_gateway_method.ingest_post.id,
      aws_api_gateway_method.retrieve_get.id,
      aws_api_gateway_integration.ingest_integration.id,
      aws_api_gateway_integration.retrieve_integration.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway stage
resource "aws_api_gateway_stage" "dev" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "dev"
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.ingest_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# Lambda permission for retrieve endpoint
resource "aws_lambda_permission" "retrieve_api_gateway" {
  statement_id  = "AllowRetrieveAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.retrieve_api_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}
