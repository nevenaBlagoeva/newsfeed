# S3 bucket for hosting the dashboard
resource "aws_s3_bucket" "dashboard" {
  bucket = "newsfeed-dashboard-${random_string.bucket_suffix.result}"
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Make bucket public for direct object access
resource "aws_s3_bucket_public_access_block" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.dashboard.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.dashboard]
}

# Create local value for API base URL with debugging
locals {
  api_base_url = module.api_gateway.api_base_url
}

# Upload dashboard HTML with API URL replacement
resource "aws_s3_object" "dashboard_html" {
  bucket       = aws_s3_bucket.dashboard.id
  key          = "dashboard.html"
  content      = replace(file("${path.module}/../src/dashboard/dashboard.html"), "PLACEHOLDER_API_URL", local.api_base_url)
  content_type = "text/html"
  etag         = md5(replace(file("${path.module}/../src/dashboard/dashboard.html"), "PLACEHOLDER_API_URL", local.api_base_url))
}