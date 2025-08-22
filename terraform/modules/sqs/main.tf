# Dead Letter Queue for failed messages
resource "aws_sqs_queue" "dlq" {
  name = "${var.queue_name}-dlq"
}

# Main SQS Queue
resource "aws_sqs_queue" "main" {
  name                      = var.queue_name
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600  # 14 days
  visibility_timeout_seconds = 60
  
  # Configure dead letter queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}
