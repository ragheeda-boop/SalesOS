variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "me-south-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["me-south-1a", "me-south-1b"]
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDRs"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "eks_desired_size" {
  description = "EKS desired node count"
  type        = number
  default     = 3
}

variable "eks_min_size" {
  description = "EKS minimum node count"
  type        = number
  default     = 2
}

variable "eks_max_size" {
  description = "EKS maximum node count"
  type        = number
  default     = 10
}

variable "eks_instance_types" {
  description = "EKS instance types"
  type        = list(string)
  default     = ["t3.medium", "t3.large"]
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100
}

variable "rds_max_allocated_storage" {
  description = "RDS maximum autoscaling storage in GB"
  type        = number
  default     = 500
}
