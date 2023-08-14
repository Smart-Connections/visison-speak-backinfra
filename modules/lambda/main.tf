variable "function_name" {}
variable "role_arn" {}
variable "environment" {}
variable "lambda_environments" {}

data "archive_file" "main" {
  type        = "zip"
  source_dir  = "lambda_functions/${var.function_name}"
  output_path = "lambda_functions/.build/${var.function_name}.zip"
}

resource "aws_lambda_function" "main" {
  filename         = data.archive_file.main.output_path
  function_name    = "${var.function_name}-${var.environment}"
  role             = var.role_arn
  handler          = "index.lambda_handler"
  runtime          = "python3.9"
  publish          = true
  source_code_hash = data.archive_file.main.output_base64sha256
  environment {
    variables = var.lambda_environments
  }
}

resource "aws_lambda_permission" "allow_execution_from_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "apigateway.amazonaws.com"
}

output "arn" {
  value = aws_lambda_function.main.arn
}

output "function_name" {
  value = aws_lambda_function.main.function_name
}

output "invoke_arn" {
  value = aws_lambda_function.main.invoke_arn
}
