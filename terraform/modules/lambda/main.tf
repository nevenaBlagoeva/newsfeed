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

# Track source file changes
locals {
  source_files = fileset(var.source_dir, "**/*.py")
  source_hash = md5(join("", [for f in local.source_files : filemd5("${var.source_dir}/${f}")]))
}

# Create build directory and install dependencies
resource "null_resource" "lambda_build" {
  triggers = {
    source_hash = local.source_hash
    requirements = filemd5("${var.source_dir}/requirements.txt")
  }
  
  provisioner "local-exec" {
    command = <<EOF
      rm -rf ${path.module}/build/${var.function_name}
      mkdir -p ${path.module}/build/${var.function_name}
      cp -r ${var.source_dir}/* ${path.module}/build/${var.function_name}/
      cd ${path.module}/build/${var.function_name}
      if [ -f requirements.txt ]; then
        pip install -r requirements.txt -t .
      fi
    EOF
  }
}

# Package the Lambda code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/build/${var.function_name}"
  output_path = "${path.module}/${var.function_name}.zip"
  excludes    = ["__pycache__", "*.pyc"]
  
  depends_on = [null_resource.lambda_build]
}

# Lambda function
resource "aws_lambda_function" "main" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.function_name
  role            = aws_iam_role.lambda_role.arn
  handler         = var.handler
  runtime          = "python3.11"
  timeout          = 30  # Increase from default 3 seconds
  source_code_hash = "${data.archive_file.lambda_zip.output_base64sha256}-${local.source_hash}"

  environment {
    variables = var.environment_variables
  }

  depends_on = [data.archive_file.lambda_zip]
}