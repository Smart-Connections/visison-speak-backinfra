resource "aws_api_gateway_rest_api" "main" {
  name = "vision-speak-api-${var.environment}"
}

resource "aws_api_gateway_authorizer" "cognito" {
  name            = "cognito-authorizer"
  rest_api_id     = aws_api_gateway_rest_api.main.id
  type            = "COGNITO_USER_POOLS"
  identity_source = "method.request.header.Authorization"
  provider_arns   = [aws_cognito_user_pool.main.arn]
}

resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch_logs.arn
}

module "api_gateway_resources" {
  for_each = {
    "test" = {
      http_method          = "GET"
      lambda_invoke_arn    = module.lambda_functions["test"].invoke_arn
      response_status_code = "200"
    },
    "v1_setup_chat" = {
      http_method          = "POST"
      lambda_invoke_arn    = module.lambda_functions["setup_chat"].invoke_arn
      response_status_code = "201"
    },
    "v1_get_chat_threads" = {
      http_method          = "GET"
      lambda_invoke_arn    = module.lambda_functions["get_chat_threads"].invoke_arn
      response_status_code = "200"
    },
    "v1_get_chat_messages" = {
      http_method          = "GET"
      lambda_invoke_arn    = module.lambda_functions["get_chat_messages"].invoke_arn
      response_status_code = "200"
    },
    "v1_send_message" = {
      http_method          = "POST"
      lambda_invoke_arn    = module.lambda_functions["send_message"].invoke_arn
      response_status_code = "201"
    },
  }
  source                    = "./modules/api_gateway_resource"
  rest_api_id               = aws_api_gateway_rest_api.main.id
  rest_api_root_resource_id = aws_api_gateway_rest_api.main.root_resource_id
  path                      = each.key
  http_method               = each.value["http_method"]
  authorizer_id             = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn         = each.value["lambda_invoke_arn"]
  response_status_code      = each.value["response_status_code"]
}

resource "aws_api_gateway_stage" "main" {
  stage_name    = "main"
  rest_api_id   = aws_api_gateway_rest_api.main.id
  deployment_id = aws_api_gateway_deployment.main.id

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format          = "$context.identity.sourceIp $context.identity.caller $context.identity.user [$context.requestTime] \"$context.httpMethod $context.resourcePath $context.protocol\" $context.status $context.responseLength $context.requestId $context.integrationError $context.integrationLatency $context.integrationStatus"
  }
}

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = var.deploy_enable ? timestamp() : ""
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    module.api_gateway_resources,
  ]
}

resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name = "/aws/apigateway/${aws_api_gateway_rest_api.main.name}"
}

resource "aws_iam_role" "api_gateway_cloudwatch_logs" {
  name = "APIGatewayCloudWatchLogsRole-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Principal = {
          Service = "apigateway.amazonaws.com"
        },
        Effect = "Allow",
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch_logs_attach" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
  role       = aws_iam_role.api_gateway_cloudwatch_logs.name
}
