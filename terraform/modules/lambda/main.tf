# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = var.function_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

# Lambda function
resource "aws_lambda_function" "main" {
  function_name    = var.function_name
  role            = aws_iam_role.lambda_role.arn
  s3_bucket       = "newsfeed-lambda-artifacts"
  s3_key          = "${var.function_name}-${var.commit_sha}.zip"
  handler         = var.handler
  runtime          = "python3.11"
  timeout          = 30

  environment {
    variables = var.environment_variables
  }
}