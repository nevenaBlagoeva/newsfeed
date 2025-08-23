variable "rule_name" {
  description = "Name of the EventBridge rule"
  type        = string
}

variable "description" {
  description = "Description of the EventBridge rule"
  type        = string
}

variable "schedule_expression" {
  description = "Schedule expression (e.g., 'rate(1 hour)')"
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function to trigger"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to trigger"
  type        = string
}
