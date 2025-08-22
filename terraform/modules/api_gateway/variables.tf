variable "ingest_lambda_function_name" {
  description = "Name of the Lambda function to integrate for ingestion"
  type        = string
}

variable "ingest_lambda_invoke_arn" {
  description = "Invoke ARN of the Lambda function for ingestion"
  type        = string
}
