variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-1"
}

variable "reddit_client_id" {
  description = "Reddit API client ID"
  type        = string
  sensitive   = true
}

variable "reddit_client_secret" {
  description = "Reddit API client secret"
  type        = string
  sensitive   = true
}

variable "commit_sha" {
  description = "Git commit SHA for deployment tracking"
  type        = string
  default     = "unknown"
}
