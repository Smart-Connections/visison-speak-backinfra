data "archive_file" "lambda_layer" {
  type        = "zip"
  source_dir  = "lambda_layer"
  output_path = "lambda_layer/.build/lambda_layer.zip"
}

resource "aws_lambda_layer_version" "main" {
  layer_name          = "vision-speak-layer-${var.environment}"
  filename            = data.archive_file.lambda_layer.output_path
  compatible_runtimes = ["python3.9"]
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
    "insert" = {
      lambda_environments = {
        "TABLE_NAME" = aws_dynamodb_table.chat_threads.name
        "ENV"        = var.environment
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
