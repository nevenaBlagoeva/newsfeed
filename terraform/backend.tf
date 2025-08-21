terraform {
  backend "s3" {
    bucket = "newsfeed-terraform-state"
    key    = "lambda/terraform.tfstate"
    region = "eu-west-1"
  }
}
