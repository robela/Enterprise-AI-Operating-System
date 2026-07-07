terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }
}

variable "environment" {
  description = "Deployment environment (dev | staging | prod)"
  default     = "dev"
}

variable "region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "db_password" {
  description = "PostgreSQL master password"
  sensitive   = true
}

provider "aws" {
  region = var.region
}

# --- RDS PostgreSQL ---
resource "aws_db_instance" "postgres" {
  identifier              = "enterprise-ai-${var.environment}"
  engine                  = "postgres"
  engine_version          = "16.2"
  instance_class          = var.environment == "prod" ? "db.r8g.large" : "db.t3.medium"
  allocated_storage       = 100
  storage_encrypted       = true
  db_name                 = "enterprise_ai"
  username                = "postgres"
  password                = var.db_password
  skip_final_snapshot     = var.environment != "prod"
  deletion_protection     = var.environment == "prod"
  backup_retention_period = var.environment == "prod" ? 30 : 7
  multi_az                = var.environment == "prod"

  tags = {
    Environment = var.environment
    Project     = "enterprise-ai-os"
  }
}

# --- ElastiCache Redis ---
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "enterprise-ai-${var.environment}"
  engine               = "redis"
  node_type            = var.environment == "prod" ? "cache.r7g.large" : "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379

  tags = {
    Environment = var.environment
    Project     = "enterprise-ai-os"
  }
}

# --- EKS Cluster ---
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "enterprise-ai-${var.environment}"
  cluster_version = "1.30"

  eks_managed_node_groups = {
    default = {
      min_size     = var.environment == "prod" ? 3 : 1
      max_size     = var.environment == "prod" ? 20 : 5
      desired_size = var.environment == "prod" ? 3 : 2
      instance_types = [var.environment == "prod" ? "m7i.xlarge" : "t3.large"]
    }
  }
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}
