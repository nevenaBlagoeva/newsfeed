# S3 bucket for Lambda artifacts
resource "aws_s3_bucket" "lambda_artifacts" {
  bucket = "newsfeed-lambda-artifacts"
}

resource "aws_s3_bucket_versioning" "lambda_artifacts" {
  bucket = aws_s3_bucket.lambda_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}