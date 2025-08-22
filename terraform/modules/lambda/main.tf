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
      echo "=== Building Lambda function: ${var.function_name} ==="
      echo "Source directory: ${var.source_dir}"
      echo "Build directory: ${path.module}/build/${var.function_name}"
      
      # Check if source directory exists
      if [ ! -d "${var.source_dir}" ]; then
        echo "ERROR: Source directory does not exist: ${var.source_dir}"
        exit 1
      fi
      
      # Create build directory
      rm -rf "${path.module}/build/${var.function_name}"
      mkdir -p "${path.module}/build/${var.function_name}"
      
      # Copy lambda source files
      echo "Copying lambda source files..."
      cp -r "${var.source_dir}/"* "${path.module}/build/${var.function_name}/"
      
      # Copy shared directory if it exists
      SHARED_DIR="${var.source_dir}/../shared"
      if [ -d "$SHARED_DIR" ]; then
        echo "Copying shared directory from: $SHARED_DIR"
        cp -r "$SHARED_DIR" "${path.module}/build/${var.function_name}/"
      else
        echo "Shared directory not found: $SHARED_DIR"
      fi
      
      # Install requirements if they exist
      cd "${path.module}/build/${var.function_name}"
      if [ -f requirements.txt ]; then
        echo "Installing requirements..."
        pip install -r requirements.txt -t .
      else
        echo "No requirements.txt found"
      fi
      
      # Create ZIP file directly
      echo "Creating ZIP file..."
      cd "${path.module}/build/${var.function_name}"
      zip -r "../../${var.function_name}.zip" . -x "__pycache__/*" "*.pyc"
      
      echo "Build and ZIP creation completed successfully"
    EOF
    
    on_failure = fail
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