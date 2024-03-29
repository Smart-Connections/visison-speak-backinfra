
resource "aws_cognito_user_pool" "main" {
  deletion_protection = "ACTIVE"
  mfa_configuration   = "OFF"
  name                = "vision-speak-user-pool-${var.environment}"
  alias_attributes    = ["preferred_username"]
  admin_create_user_config {
    allow_admin_create_user_only = false
  }
  lambda_config {
    pre_sign_up = module.lambda_functions["cognito_user_auto_confirm"].arn
  }
}

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "vision-speak-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id
}

resource "aws_cognito_user_pool_client" "mobile_app" {
  allowed_oauth_flows                  = ["implicit", "code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["openid"]
  callback_urls                        = ["https://example.com/callback"]
  explicit_auth_flows                  = ["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH", "ALLOW_USER_SRP_AUTH"]
  name                                 = "mobile_app"
  supported_identity_providers         = ["COGNITO"]
  user_pool_id                         = aws_cognito_user_pool.main.id
}

resource "aws_cognito_resource_server" "api" {
  identifier = "api"
  name       = "api"

  user_pool_id = aws_cognito_user_pool.main.id
}

resource "aws_lambda_permission" "cognito_triggers" {
  for_each = {
    pre_sign_up = module.lambda_functions["cognito_user_auto_confirm"].function_name
  }
  statement_id  = "AllowExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = each.value
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.main.arn
}
