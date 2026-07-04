terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "s3" {
    bucket = "salesos-terraform-state"
    key    = "infra/terraform.tfstate"
    region = "me-south-1"
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  name_prefix = "salesos-${var.environment}"
  common_tags = {
    Project     = "SalesOS"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.name_prefix}-vpc"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "production"
  enable_dns_hostnames   = true

  tags = local.common_tags
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "${local.name_prefix}-cluster"
  cluster_version = "1.30"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    main = {
      desired_size = var.eks_desired_size
      min_size     = var.eks_min_size
      max_size     = var.eks_max_size

      instance_types = var.eks_instance_types
      capacity_type  = "ON_DEMAND"
    }
  }

  tags = local.common_tags
}

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${local.name_prefix}-postgres"

  engine               = "postgres"
  engine_version       = "16.3"
  family               = "postgres16"
  major_engine_version = "16"
  instance_class       = var.rds_instance_class

  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  storage_type          = "gp3"

  db_name  = "salesos"
  username = "salesos"
  password = random_password.rds_password.result
  port     = 5432

  multi_az               = var.environment == "production"
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.vpc.default_security_group_id]

  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:03:00-sun:04:00"

  storage_encrypted   = true
  deletion_protection = var.environment == "production"

  tags = local.common_tags
}

resource "random_password" "rds_password" {
  length  = 24
  special = false
}

resource "aws_secretsmanager_secret" "salesos" {
  name = "${local.name_prefix}-secrets"
}

resource "aws_secretsmanager_secret_version" "salesos" {
  secret_id = aws_secretsmanager_secret.salesos.id
  secret_string = jsonencode({
    database_url     = "postgresql+asyncpg://salesos:${random_password.rds_password.result}@${module.rds.db_instance_address}:5432/salesos"
    jwt_secret_key   = random_password.jwt_secret.result
  })
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}
