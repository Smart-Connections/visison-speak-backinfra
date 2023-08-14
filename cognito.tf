
resource "aws_cognito_user_pool" "main" {
  deletion_protection = "ACTIVE"
  mfa_configuration   = "OFF"
  name                = "vision-speak-user-pool-${var.environment}"
  alias_attributes    = ["preferred_username"]
  admin_create_user_config {
    allow_admin_create_user_only = false
  }
}

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "vision-speak-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id
}

resource "aws_cognito_user_pool_client" "mobile_app" {
  allowed_oauth_flows          = ["code"]
  allowed_oauth_scopes         = aws_cognito_resource_server.api.scope_identifiers
  callback_urls                = ["https://example.com/callback"]
  explicit_auth_flows          = ["ALLOW_REFRESH_TOKEN_AUTH", "ALLOW_USER_SRP_AUTH"]
  name                         = "mobile_app"
  supported_identity_providers = ["COGNITO"]
  user_pool_id                 = aws_cognito_user_pool.main.id
}

resource "aws_cognito_resource_server" "api" {
  identifier = "api"
  name       = "api"

  user_pool_id = aws_cognito_user_pool.main.id

  scope {
    scope_name        = "full_access"
    scope_description = "Access to all APIs"
  }
}
