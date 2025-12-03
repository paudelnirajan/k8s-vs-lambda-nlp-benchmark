#!/bin/bash
set -e

echo "============================================"
echo "  NLP Project Deployment"
echo "============================================"

cd "$(dirname "$0")/../infrastructure/terraform"

echo ""
echo "Step 1: Initializing Terraform..."
terraform init

echo ""
echo "Step 2: Importing existing ECR repositories (if any)..."
terraform import aws_ecr_repository.lambda_repo nlp-sentiment-analysis 2>/dev/null || true
terraform import aws_ecr_repository.k8s_repo nlp-sentiment-k8s 2>/dev/null || true
terraform import aws_ecr_repository.backend_repo nlp-backend 2>/dev/null || true
terraform import aws_ecr_repository.frontend_repo nlp-frontend 2>/dev/null || true

echo ""
echo "Step 3: Creating/updating ECR repositories..."
terraform apply -target=aws_ecr_repository.lambda_repo \
                -target=aws_ecr_repository.k8s_repo \
                -target=aws_ecr_repository.backend_repo \
                -target=aws_ecr_repository.frontend_repo \
                -auto-approve

echo ""
echo "Step 4: Checking if images exist in ECR..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"

check_image() {
    aws ecr describe-images --repository-name "$1" --image-ids imageTag=latest --region $REGION 2>/dev/null
}

if ! check_image "nlp-sentiment-analysis" || ! check_image "nlp-sentiment-k8s"; then
    echo "  -> Images missing! Building and pushing..."
    cd ../..
    ./scripts/build_and_push.sh
    cd infrastructure/terraform
else
    echo "  -> Images found in ECR. Skipping build."
fi

echo ""
echo "Step 5: Applying full infrastructure..."
terraform apply -auto-approve

# Get all outputs
LAMBDA_ENDPOINT=$(terraform output -raw lambda_api_endpoint 2>/dev/null || echo "N/A")
K8S_ENDPOINT=$(terraform output -raw kubernetes_api_endpoint 2>/dev/null || echo "N/A")
EC2_FRONTEND=$(terraform output -raw ec2_frontend_url 2>/dev/null || echo "N/A")
EC2_BACKEND=$(terraform output -raw ec2_backend_url 2>/dev/null || echo "N/A")
EC2_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || echo "N/A")
SSH_CMD=$(terraform output -raw ssh_command 2>/dev/null || echo "N/A")
KUBECTL_CMD=$(terraform output -raw configure_kubectl_command 2>/dev/null || echo "N/A")

echo ""
echo "+------------------------------------------------------------------+"
echo "|                    DEPLOYMENT COMPLETE!                          |"
echo "+------------------------------------------------------------------+"
echo "|                                                                  |"
echo "|  LAMBDA (Serverless)                                             |"
echo "|  API Endpoint: $LAMBDA_ENDPOINT"
echo "|                                                                  |"
echo "|  KUBERNETES (EKS)                                                |"
echo "|  API Endpoint: $K8S_ENDPOINT"
echo "|                                                                  |"
echo "|  EC2 INSTANCE ($EC2_IP)                                          |"
echo "|  Frontend (Streamlit): $EC2_FRONTEND"
echo "|  Backend (FastAPI):    $EC2_BACKEND"
echo "|                                                                  |"
echo "+------------------------------------------------------------------+"
echo "|  USEFUL COMMANDS                                                 |"
echo "+------------------------------------------------------------------+"
echo "|                                                                  |"
echo "|  SSH into EC2:                                                   |"
echo "|  $SSH_CMD"
echo "|                                                                  |"
echo "|  Configure kubectl:                                              |"
echo "|  $KUBECTL_CMD"
echo "|                                                                  |"
echo "|  Monitor EC2 startup:                                            |"
echo "|  tail -f /var/log/cloud-init-output.log                          |"
echo "+------------------------------------------------------------------+"
echo ""
echo "Note: EC2 instance needs ~60-90 seconds to pull images and start."
echo ""
echo "IMPORTANT: Upload your .env file to EC2:"
echo "  scp -i infrastructure/terraform/nlp-project-key.pem .env ubuntu@$EC2_IP:~/.env"
echo "  ssh -i infrastructure/terraform/nlp-project-key.pem ubuntu@$EC2_IP \"sudo mv ~/.env /home/ubuntu/app/.env && cd /home/ubuntu/app && sudo docker-compose up -d --force-recreate\""
