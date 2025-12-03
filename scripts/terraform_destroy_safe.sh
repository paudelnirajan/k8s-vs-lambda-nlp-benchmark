#!/bin/bash
set -e

cd "$(dirname "$0")/../infrastructure/terraform"

echo "============================================"
echo "  Safe Terraform Destroy"
echo "============================================"

# Step 1: Destroy K8s service first (releases Load Balancer)
echo ""
echo "Step 1: Destroying Kubernetes Service..."
if terraform state list 2>/dev/null | grep -q "kubernetes_service.nlp_service"; then
    terraform destroy -target=kubernetes_service.nlp_service -auto-approve
    echo "Waiting 90 seconds for Load Balancer cleanup..."
    sleep 90
else
    echo "  -> Kubernetes Service not in state. Skipping."
fi

# Step 2: Destroy K8s deployment
echo ""
echo "Step 2: Destroying Kubernetes Deployment..."
if terraform state list 2>/dev/null | grep -q "kubernetes_deployment.nlp_deployment"; then
    terraform destroy -target=kubernetes_deployment.nlp_deployment -auto-approve
else
    echo "  -> Kubernetes Deployment not in state. Skipping."
fi

# Step 3: Destroy everything
echo ""
echo "Step 3: Destroying all remaining infrastructure..."
terraform destroy -auto-approve

echo ""
echo "============================================"
echo "  Destroy Complete!"
echo "============================================"
echo ""
echo "Note: ECR repositories have been deleted."
echo "You will need to recreate them and push images before next deployment."
echo ""
echo "To redeploy, run: ./scripts/deploy_all.sh"
