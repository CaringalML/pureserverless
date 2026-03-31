terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }

  # Remote state backend — bucket and table are created by terraform-state/
  # Run `terraform -chdir=terraform-state apply` once before using this backend.
  backend "s3" {
    bucket         = "maangasserverless" # must match terraform-state/variables.tf
    key            = "hello-world/terraform.tfstate"
    region         = "ap-southeast-2"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
