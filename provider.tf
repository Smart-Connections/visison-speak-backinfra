
terraform {
}

provider "aws" {
  region = "ap-northeast-1"

  default_tags {
    tags = {
      "env"       = var.environment
      "terraform" = "true"
    }
  }
}
