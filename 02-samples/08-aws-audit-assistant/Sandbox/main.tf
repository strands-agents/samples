provider "aws" {
  region = var.region
}

# Generate a new private key
resource "tls_private_key" "audit_assistant_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Create a new key pair using the generated private key
resource "aws_key_pair" "audit_assistant_key" {
  key_name   = "${var.key_name_prefix}-key-tf"
  public_key = tls_private_key.audit_assistant_key.public_key_openssh
}

# Save the private key to a local file
resource "local_file" "private_key" {
  content  = tls_private_key.audit_assistant_key.private_key_pem
  filename = "${path.module}/${var.key_name_prefix}-key.pem"
  file_permission = "0600"
}

# Create IAM role for EC2 with read-only access
resource "aws_iam_role" "ec2_readonly_role" {
  name = "ec2-readonly-role-tf"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

# Attach ReadOnlyAccess policy to the role
resource "aws_iam_role_policy_attachment" "readonly_policy_attachment" {
  role       = aws_iam_role.ec2_readonly_role.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

# Create custom IAM policy for Bedrock access
resource "aws_iam_policy" "bedrock_invoke_policy" {
  name        = "BedrockInvokeModelPolicy-tf"
  description = "Policy to allow invoking Bedrock models"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach Bedrock policy to the role
resource "aws_iam_role_policy_attachment" "bedrock_policy_attachment" {
  role       = aws_iam_role.ec2_readonly_role.name
  policy_arn = aws_iam_policy.bedrock_invoke_policy.arn
}

# Create instance profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ec2-readonly-profile-tf"
  role = aws_iam_role.ec2_readonly_role.name
}

# Create security group for SSH access
resource "aws_security_group" "audit_assistant_sg" {
  name        = "audit-assistant-sg-tf"
  description = "Security group for audit assistant EC2 instance"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "audit-assistant-sg-tf"
  }
}

# Create EC2 instance
resource "aws_instance" "audit_assistant_instance" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.audit_assistant_key.key_name
  vpc_security_group_ids = [aws_security_group.audit_assistant_sg.id]
  subnet_id              = var.subnet_id
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = <<-EOF
    #!/bin/bash
    # Log all output to a file for debugging
    exec > >(tee /var/log/user-data.log)
    exec 2>&1

    # Update system packages
    yum update -y

    # Install development tools and dependencies
    yum groupinstall -y "Development Tools"
    yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget git

    # Install Python 3.11 from source
    cd /tmp
    wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
    tar xzf Python-3.11.9.tgz
    cd Python-3.11.9
    ./configure --enable-optimizations --with-ensurepip=install
    make altinstall

    # Create symbolic links
    ln -sf /usr/local/bin/python3.11 /usr/local/bin/python3
    ln -sf /usr/local/bin/python3.11 /usr/local/bin/python
    ln -sf /usr/local/bin/pip3.11 /usr/local/bin/pip3
    ln -sf /usr/local/bin/pip3.11 /usr/local/bin/pip

    # Update PATH in bashrc
    echo 'export PATH="/usr/local/bin:$PATH"' >> /home/ec2-user/.bashrc
    echo 'export PATH="/usr/local/bin:$PATH"' >> /root/.bashrc

    # Verify Python version
    /usr/local/bin/python3.11 --version

    # Create directory for application
    mkdir -p /home/ec2-user/audit-assistant
    chown ec2-user:ec2-user /home/ec2-user/audit-assistant

    # Install AWS CLI v2
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install

    # Clean up
    cd /
    rm -rf /tmp/Python-3.11.9*
    rm -f awscliv2.zip

    echo "User data script completed successfully" >> /var/log/user-data.log
  EOF

  tags = {
    Name = "audit-assistant-instance-tf"
  }
}
