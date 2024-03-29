resource "aws_dynamodb_table" "chat_threads" {
  name           = "chat_threads-${var.environment}"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5

  attribute {
    name = "cognito_user_id"
    type = "S"
  }

  attribute {
    name = "updated_timestamp"
    type = "N"
  }

  attribute {
    name = "chat_thread_id"
    type = "S"
  }

  global_secondary_index {
    name            = "cognito_user_id"
    hash_key        = "cognito_user_id"
    range_key       = "updated_timestamp"
    write_capacity  = 5
    read_capacity   = 5
    projection_type = "ALL"
  }

  hash_key = "chat_thread_id"
}

resource "aws_dynamodb_table" "chat_messages" {
  name           = "chat_messages-${var.environment}"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5

  attribute {
    name = "chat_message_id"
    type = "S"
  }

  attribute {
    name = "chat_thread_id"
    type = "S"
  }

  attribute {
    name = "created_timestamp"
    type = "N"
  }

  global_secondary_index {
    name            = "chat_thread_id"
    hash_key        = "chat_thread_id"
    range_key       = "created_timestamp"
    write_capacity  = 5
    read_capacity   = 5
    projection_type = "ALL"
  }

  hash_key = "chat_message_id"
}
