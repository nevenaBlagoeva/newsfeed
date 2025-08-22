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
    requirements = try(filemd5("${var.source_dir}/requirements.txt"), "")
  }
  
  provisioner "local-exec" {
    command = <<EOF
      set -e
      echo "Building Lambda function: ${var.function_name}"
      rm -rf ${path.module}/build/${var.function_name}
      mkdir -p ${path.module}/build/${var.function_name}
      cp -r ${var.source_dir}/* ${path.module}/build/${var.function_name}/
      
      # Copy shared directory if it exists
      SHARED_DIR="${var.source_dir}/../shared"
      if [ -d "$SHARED_DIR" ]; then
        echo "Copying shared directory..."
        cp -r "$SHARED_DIR" ${path.module}/build/${var.function_name}/
      fi
      
      cd ${path.module}/build/${var.function_name}
      if [ -f requirements.txt ]; then
        echo "Installing requirements..."
        pip install -r requirements.txt -t .
      fi
      echo "Build completed successfully"
      ls -la
    EOF
  }
}

# Ensure build directory exists before archiving
resource "null_resource" "verify_build" {
  depends_on = [null_resource.lambda_build]
  
  provisioner "local-exec" {
    command = <<EOF
      if [ ! -d "${path.module}/build/${var.function_name}" ]; then
        echo "ERROR: Build directory does not exist!"
        exit 1
      fi
      echo "Build directory verified: ${path.module}/build/${var.function_name}"
    EOF
  }
}

# Package the Lambda code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/build/${var.function_name}"
  output_path = "${path.module}/${var.function_name}.zip"
  excludes    = ["__pycache__", "*.pyc"]
  
  depends_on = [null_resource.verify_build]
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