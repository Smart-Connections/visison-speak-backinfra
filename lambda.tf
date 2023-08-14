
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
        "TABLE_NAME" = aws_dynamodb_table.users_table.name
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
