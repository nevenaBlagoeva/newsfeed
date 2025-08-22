output "lambda_role_name" {
  value = aws_iam_role.lambda_role.name
}

output "lambda_function_name" {
  value = aws_lambda_function.main.function_name
}
