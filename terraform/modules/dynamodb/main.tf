resource "aws_dynamodb_table" "main" {
  name           = var.table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = var.hash_key
  range_key      = var.range_key

  attribute {
    name = var.hash_key
    type = "S"
  }

  # Add range key attribute if specified
  dynamic "attribute" {
    for_each = var.range_key != null ? [1] : []
    content {
      name = var.range_key
      type = var.range_key_type
    }
  }

  # TTL configuration
  ttl {
    attribute_name = var.ttl_attribute
    enabled        = var.ttl_enabled
  }

  # DynamoDB Streams configuration
  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"

  tags = {
    Name        = var.table_name
    Environment = "dev"
  }
}
