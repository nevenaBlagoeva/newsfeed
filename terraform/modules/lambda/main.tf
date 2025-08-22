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
  shared_dir = "${var.source_dir}/../shared"
  shared_files = can(fileset(local.shared_dir, "**/*.py")) ? fileset(local.shared_dir, "**/*.py") : []
  source_hash = md5(join("", concat(
    [for f in local.source_files : filemd5("${var.source_dir}/${f}")],
    [for f in local.shared_files : filemd5("${local.shared_dir}/${f}")]
  )))
}

# Create build directory and install dependencies
resource "null_resource" "lambda_build" {
  triggers = {
    source_hash = local.source_hash
    requirements = try(filemd5("${var.source_dir}/requirements.txt"), "")
  }
  
  provisioner "local-exec" {
    working_dir = path.module
    command = <<EOF
      set -e
      
      # Create build directory
      rm -rf "build/${var.function_name}"
      mkdir -p "build/${var.function_name}"
      
      # Copy lambda source files - use absolute path
      cp -r "${abspath(var.source_dir)}"/* "build/${var.function_name}/"
      
      # Copy shared directory if it exists - use absolute path
      SHARED_DIR="${abspath(var.source_dir)}/../shared"
      if [ -d "$SHARED_DIR" ]; then
        cp -r "$SHARED_DIR" "build/${var.function_name}/"
      fi
      
      # Install requirements if they exist
      cd "build/${var.function_name}"
      if [ -f requirements.txt ]; then
        pip install -r requirements.txt -t .
      fi
      
      # Create ZIP file
      rm -f "../../${var.function_name}.zip"
      zip -r "../../${var.function_name}.zip" . -x "__pycache__/*" "*.pyc"
    EOF
  }
}

# Lambda function
resource "aws_lambda_function" "main" {
  filename         = "${path.module}/${var.function_name}.zip"
  function_name    = var.function_name
  role            = aws_iam_role.lambda_role.arn
  handler         = var.handler
  runtime          = "python3.11"
  timeout          = 30
  source_code_hash = local.source_hash

  environment {
    variables = var.environment_variables
  }

  depends_on = [null_resource.lambda_build]
}