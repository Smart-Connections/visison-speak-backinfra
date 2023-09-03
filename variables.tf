variable "environment" {
  description = "環境識別子"
}
variable "deploy_enable" {
  description = "APIGatewayのデプロイをするかどうか。基本的にずっとtrueでよい。"
  type        = bool
  default     = true
}
variable "azure_account_region" {
  description = "Azureのリージョン"
}
variable "azure_account_key" {
  description = "AzureのComputerVisionClientを利用するためのアカウントキー。"
}
variable "openai_api_key" {
  description = "OpenAIのAPIキー"
}
