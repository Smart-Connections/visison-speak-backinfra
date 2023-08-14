variable "rest_api_id" {}
variable "rest_api_root_resource_id" {}
variable "path" {}
variable "http_method" {}
variable "authorizer_id" {}
variable "lambda_invoke_arn" {}
variable "response_status_code" {}
variable "authorization_scopes" {}

resource "aws_api_gateway_resource" "main" {
  rest_api_id = var.rest_api_id
  parent_id   = var.rest_api_root_resource_id
  path_part   = var.path
}

resource "aws_api_gateway_method" "main" {
  rest_api_id          = var.rest_api_id
  resource_id          = aws_api_gateway_resource.main.id
  http_method          = var.http_method
  authorization        = "COGNITO_USER_POOLS"
  authorizer_id        = var.authorizer_id
  authorization_scopes = var.authorization_scopes
}

resource "aws_api_gateway_integration" "main" {
  rest_api_id = var.rest_api_id
  resource_id = aws_api_gateway_resource.main.id
  http_method = aws_api_gateway_method.main.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arn
}

resource "aws_api_gateway_method_response" "main" {
  rest_api_id = var.rest_api_id
  resource_id = aws_api_gateway_resource.main.id
  http_method = aws_api_gateway_method.main.http_method
  status_code = var.response_status_code
}

resource "aws_api_gateway_integration_response" "main" {
  rest_api_id = var.rest_api_id
  resource_id = aws_api_gateway_resource.main.id
  http_method = aws_api_gateway_method.main.http_method
  status_code = aws_api_gateway_method_response.main.status_code

  response_templates = {
    "application/json" = ""
  }
}
