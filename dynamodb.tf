resource "aws_dynamodb_table" "chat_threads" {
  name           = "chat_threads-${var.environment}"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5

  attribute {
    name = "chat_thread_id"
    type = "S"
  }

  attribute {
    name = "cognito_user_id"
    type = "S"
  }

  attribute {
    name = "image_path"
    type = "S"
  }

  attribute {
    name = "topic"
    type = "S"
  }

  attribute {
    name = "created_timestamp"
    type = "N"
  }

  attribute {
    name = "updated_timestamp"
    type = "N"
  }

  hash_key  = "cognito_user_id"
  range_key = "updated_timestamp"
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
    name = "cognito_user_id"
    type = "S"
  }

  attribute {
    name = "sender_type"
    type = "S"
  }

  attribute {
    name = "english_message"
    type = "S"
  }

  attribute {
    name = "japanese_message"
    type = "S"
  }

  attribute {
    name = "read"
    type = "BOOL"
  }

  attribute {
    name = "created_timestamp"
    type = "N"
  }

  hash_key  = "chat_thread_id"
  range_key = "created_timestamp"

  global_secondary_index {
    name            = "cognito_user_index"
    hash_key        = "cognito_user_id"
    range_key       = "created_timestamp"
    write_capacity  = 5
    read_capacity   = 5
    projection_type = "ALL"
  }
}
