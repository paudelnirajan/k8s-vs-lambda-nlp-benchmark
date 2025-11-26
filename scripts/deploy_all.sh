#!/bin/bash

# Stop on any error
set -e

echo "Starting Deployment..."

# Navigate to Terraform directory
cd infrastructure/terraform

echo "Initializing Terraform..."
terraform init

echo "Applying Infrastructure (This may take 10-15 minutes for EKS/EC2)..."
terraform apply -auto-approve

# Extract the IP address
APP_IP=$(terraform output -raw app_server_public_ip)

echo ""
echo "Deployment Infrastructure Complete!"
echo "---------------------------------------------------"
echo "App URL: http://$APP_IP:8501"
echo "API URL: http://$APP_IP:8000"
echo "---------------------------------------------------"
echo "NOTE: The EC2 instance is currently installing Docker and building your app."
echo "   It may take another 3-5 minutes before the URL is reachable."
echo ""
echo "   To monitor progress, run this SSH command:"
echo "   $(terraform output -raw ssh_command)"
echo "   Then run: tail -f /var/log/cloud-init-output.log"