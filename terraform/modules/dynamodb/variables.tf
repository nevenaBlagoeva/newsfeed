variable "table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "hash_key" {
  description = "Hash key for the DynamoDB table"
  type        = string
  default     = "id"
}

variable "ttl_attribute" {
  description = "TTL attribute name"
  type        = string
  default     = "ttl_epoch"
}

variable "ttl_enabled" {
  description = "Enable TTL for the table"
  type        = bool
  default     = true
}
