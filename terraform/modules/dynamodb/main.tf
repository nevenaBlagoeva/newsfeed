resource "aws_dynamodb_table" "main" {
  name           = var.table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = var.hash_key

  attribute {
    name = var.hash_key
    type = "S"
  }

  # TTL configuration
  ttl {
    attribute_name = var.ttl_attribute
    enabled        = var.ttl_enabled
  }

  # DynamoDB Streams configuration
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  tags = {
    Name        = var.table_name
    Environment = "dev"
  }
}
