output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_address
}

output "rds_database" {
  description = "RDS database name"
  value       = module.rds.db_instance_name
}

output "secrets_arn" {
  description = "Secrets Manager ARN"
  value       = aws_secretsmanager_secret.salesos.arn
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}
