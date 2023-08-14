resource "aws_dynamodb_table" "users_table" {
  name           = "Users-${var.environment}"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "UserId"
  range_key      = "Name"

  attribute {
    name = "UserId"
    type = "S"
  }

  attribute {
    name = "Name"
    type = "S"
  }

  attribute {
    name = "Timestamp"
    type = "N"
  }

  global_secondary_index {
    name               = "NameIndex"
    hash_key           = "Name"
    range_key          = "Timestamp"
    write_capacity     = 10
    read_capacity      = 10
    projection_type    = "INCLUDE"
    non_key_attributes = ["UserId"]
  }
}
