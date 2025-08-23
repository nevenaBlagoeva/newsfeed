# EventBridge rule with configurable schedule
resource "aws_cloudwatch_event_rule" "scheduled_rule" {
  name                = var.rule_name
  description         = var.description
  schedule_expression = var.schedule_expression
}

# EventBridge target
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.scheduled_rule.name
  target_id = "${var.rule_name}Target"
  arn       = var.lambda_function_arn
}

# Lambda permission for EventBridge
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge-${var.rule_name}"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_rule.arn
}
