variable "ingest_lambda_function_name" {
  description = "Name of the ingest Lambda function"
  type        = string
}

variable "ingest_lambda_invoke_arn" {
  description = "Invoke ARN of the ingest Lambda function"  
  type        = string
}

variable "retrieve_api_lambda_function_name" {
  description = "Name of the retrieve API Lambda function"
  type        = string
}

variable "retrieve_api_lambda_invoke_arn" {
  description = "Invoke ARN of the retrieve API Lambda function"
  type        = string
}
