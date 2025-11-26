#!/bin/bash

# Stop on any error
set -e

echo "Starting Deployment..."

# Navigate to Terraform directory
cd infrastructure/terraform

echo "Initializing Terraform..."
terraform init

echo "Applying Infrastructure..."
# We use auto-approve to skip the "yes" prompt
terraform apply -auto-approve

# Extract the IP address
APP_IP=$(terraform output -raw app_server_public_ip)

echo ""
echo "Deployment Infrastructure Complete!"
echo "---------------------------------------------------"
echo "App URL: http://$APP_IP:8501"
echo "API URL: http://$APP_IP:8000"
echo "---------------------------------------------------"
echo "NOTE: The EC2 instance is pulling pre-built images from ECR."
echo "   It should be ready in ~60-90 seconds."
echo ""
echo "   To monitor progress, run this SSH command:"
echo "   $(terraform output -raw ssh_command)"
echo "   Then run: tail -f /var/log/cloud-init-output.log"