# API Gateway outputs

output "api_base_url" {
  description = "API Gateway base URL without endpoint path"
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.eu-west-1.amazonaws.com/dev"
}
