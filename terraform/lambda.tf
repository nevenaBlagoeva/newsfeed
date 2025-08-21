# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "newsfeed-lambda-role"

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

# Package the Lambda code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/lambda.zip"
}

# Lambda function
resource "aws_lambda_function" "main" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "newsfeed-lambda"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda.lambda_handler"
  runtime         = "python3.11"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  depends_on      = [aws_iam_role_policy_attachment.lambda_policy]
}

output "terraform_aws_role_output" {
 value = aws_iam_role.lambda_role.name
}

output "terraform_aws_role_arn_output" {
 value = aws_iam_role.lambda_role.arn
}

output "terraform_logging_arn_output" {
 value = aws_iam_policy.iam_policy_for_lambda.arn
}