data "archive_file" "lambda_layer" {
  type        = "zip"
  source_dir  = "lambda_layer"
  output_path = "lambda_layer/.build/lambda_layer.zip"
}

resource "aws_lambda_layer_version" "main" {
  layer_name          = "vision-speak-layer-${var.environment}"
  filename            = data.archive_file.lambda_layer.output_path
  compatible_runtimes = ["python3.11"]
  source_code_hash    = data.archive_file.lambda_layer.output_base64sha256
}

module "lambda_functions" {
  for_each = {
    "test" = {
      lambda_environments = {
        "TEST_VALUE_1" = "sample_1"
        "TEST_VALUE_2" = "sample_2"
        "TEST_VALUE_3" = "sample_3"
        "ENV"          = var.environment
      }
    },
    "setup_chat" = {
      lambda_environments = {
        "CHAT_THREADS_TABLE_NAME" = aws_dynamodb_table.chat_threads.name
        "BUCKET_NAME"             = aws_s3_bucket.vision_speak.id
        "AZURE_ACCOUNT_REGION"    = var.azure_account_region
        "AZURE_ACCOUNT_KEY"       = var.azure_account_key
        "ENV"                     = var.environment
      }
    },
    "get_chat_threads" = {
      lambda_environments = {
        "CHAT_THREADS_TABLE_NAME"  = aws_dynamodb_table.chat_threads.name
        "CHAT_MESSAGES_TABLE_NAME" = aws_dynamodb_table.chat_messages.name
        "BUCKET_NAME"              = aws_s3_bucket.vision_speak.id
        "ENV"                      = var.environment
      }
    },
    "get_chat_messages" = {
      lambda_environments = {
        "CHAT_THREADS_TABLE_NAME"  = aws_dynamodb_table.chat_threads.name
        "CHAT_MESSAGES_TABLE_NAME" = aws_dynamodb_table.chat_messages.name
        "ENV"                      = var.environment
      }
    },
    "send_message" = {
      lambda_environments = {
        "CHAT_THREADS_TABLE_NAME"  = aws_dynamodb_table.chat_threads.name
        "CHAT_MESSAGES_TABLE_NAME" = aws_dynamodb_table.chat_messages.name
        "OPENAI_API_KEY"           = var.openai_api_key
        "ENV"                      = var.environment
      }
    },
    "cognito_user_auto_confirm" = {
      lambda_environments = {
        "ENV" = var.environment
      }
    },
  }
  source              = "./modules/lambda"
  function_name       = each.key
  role_arn            = aws_iam_role.lambda_role.arn
  environment         = var.environment
  lambda_environments = each.value["lambda_environments"]
  layers              = [aws_lambda_layer_version.main.arn]
}

resource "aws_iam_role" "lambda_role" {
  name               = "vision-speak-lambda-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess" # とりあえず適当に管理者権限付与
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com",
        "apigateway.amazonaws.com",
      ]
    }
  }
}
