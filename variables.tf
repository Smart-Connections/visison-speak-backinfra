variable "environment" {
}
variable "deploy_enable" {
  description = "APIGatewayのデプロイをするかどうかです。基本的にずっとtrueでよいです。"
  type        = bool
  default     = true
}
