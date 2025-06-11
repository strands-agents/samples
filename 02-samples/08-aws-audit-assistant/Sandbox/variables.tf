variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
  default     = "vpc-0b8f686866c5b1f82"
}

variable "subnet_id" {
  description = "Subnet ID"
  type        = string
  default     = "subnet-01e08c867437e6753"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "ami_id" {
  description = "Amazon Linux 2 AMI ID"
  type        = string
  default     = "ami-0f403e3180720dd7e"  # Amazon Linux 2 AMI in us-east-1
}

variable "key_name_prefix" {
  description = "Prefix for the key pair name"
  type        = string
  default     = "audit-assistant"
}
