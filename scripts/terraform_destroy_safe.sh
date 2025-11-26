#!/bin/bash
set -e

# Navigate to the terraform directory
cd "$(dirname "$0")/../infrastructure/terraform"

echo "Checking for Kubernetes Service in Terraform state..."
if terraform state list | grep -q "kubernetes_service.nlp_service"; then
    echo "Found Kubernetes Service. Destroying it first to trigger Load Balancer cleanup..."
    
    # 1. Target only the service
    terraform destroy -target=kubernetes_service.nlp_service -auto-approve
    
    echo "Waiting 90 seconds for AWS to fully delete the Load Balancer and ENIs..."
    # We wait because AWS needs time to detach network interfaces from the VPC
    sleep 90
else
    echo "Kubernetes Service not found in state (already deleted?). Moving on."
fi

echo "Destroying remaining infrastructure..."
# 2. Destroy everything else
terraform destroy -auto-approve