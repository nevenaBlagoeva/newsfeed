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

# Lambda function - use local file deployment
resource "aws_lambda_function" "main" {
  filename         = "${path.module}/${var.function_name}.zip"
  function_name    = var.function_name
  role            = aws_iam_role.lambda_role.arn
  handler         = var.handler
  runtime          = "python3.11"
  timeout          = 30
  source_code_hash = local.source_hash

  environment {
    variables = merge(var.environment_variables, {
      COMMIT_SHA = var.commit_sha
    })
  }

  depends_on = [null_resource.lambda_build]
}