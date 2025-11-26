# 1. Generate a secure Key Pair for SSH access
resource "tls_private_key" "pk" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "kp" {
  key_name   = "nlp-project-key"
  public_key = tls_private_key.pk.public_key_openssh
}

# Save the private key locally so we can SSH in if needed
resource "local_file" "ssh_key" {
  filename        = "${path.module}/nlp-project-key.pem"
  content         = tls_private_key.pk.private_key_pem
  file_permission = "0400"
}

# 2. Security Group for the App Server
resource "aws_security_group" "app_sg" {
  name        = "nlp-app-sg"
  description = "Allow Web and SSH traffic"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Streamlit Frontend"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "FastAPI Backend"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "nlp-app-sg"
  }
}

# 3. Get the latest Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# 4. The App Server Instance
resource "aws_instance" "app_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.small" # Slightly larger for building containers
  key_name      = aws_key_pair.kp.key_name

  # Place in Public Subnet
  subnet_id                   = module.vpc.public_subnets[0]
  vpc_security_group_ids      = [aws_security_group.app_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size = 20 # GB
  }

  tags = {
    Name = "NLP-App-Server"
  }

  # The "Magic" User Data Script
  user_data = <<-EOF
              #!/bin/bash
              set -e

              # 1. Install Docker & Git
              sudo apt-get update
              sudo apt-get install -y docker.io git curl
              sudo systemctl start docker
              sudo systemctl enable docker
              sudo usermod -aG docker ubuntu

              # 2. Install Docker Compose
              sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              sudo chmod +x /usr/local/bin/docker-compose

              # 3. Clone Repository
              # Using the variable passed from Terraform
              cd /home/ubuntu
              git clone ${var.github_repo} app
              cd app

              # Build and run in detached mode
              sudo docker-compose up -d --build
              EOF
}