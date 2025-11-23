#!/bin/bash
set -e

# Configuration
REGION="us-east-1"
CLUSTER_NAME="nlp-sentiment-cluster"
ECR_REPO_NAME="nlp-sentiment-k8s"
IMAGE_TAG="latest"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting Kubernetes deployment...${NC}"

# Get Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO_NAME}"

# 1. Create ECR Repo (if not exists)
echo -e "${YELLOW}Ensuring ECR repository exists...${NC}"
aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${REGION} 2>/dev/null || \
aws ecr create-repository --repository-name ${ECR_REPO_NAME} --region ${REGION}

# 2. Login to ECR
echo -e "${YELLOW}Logging into ECR...${NC}"
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_URI}

# 3. Build & Push Image
echo -e "${YELLOW}Building and Pushing Docker image...${NC}"
PROJECT_ROOT="$(dirname "$0")/.."
cd "${PROJECT_ROOT}"

# Build using the K8s Dockerfile
docker buildx build --platform linux/amd64 --provenance=false -t ${ECR_URI}:${IMAGE_TAG} -f model/Dockerfile.k8s .
docker push ${ECR_URI}:${IMAGE_TAG}

# 4. Update kubeconfig
echo -e "${YELLOW}Updating kubeconfig for EKS...${NC}"
aws eks --region ${REGION} update-kubeconfig --name ${CLUSTER_NAME}

# 5. Update Image in Deployment YAML (Dynamic Substitution)
# We use sed to replace the image name in the yaml temporarily or just apply it if we use a fixed name
# Here we just ensure the deployment uses the ECR URI
echo -e "${YELLOW}Deploying to Kubernetes...${NC}"

# Replace the placeholder image in deployment.yaml with the actual ECR URI
# We create a temporary file to avoid modifying the source permanently
sed "s|image: nlp-sentiment-k8s:latest|image: ${ECR_URI}:${IMAGE_TAG}|g" infrastructure/kubernetes/deployment.yaml | kubectl apply -f -

# Apply Service
kubectl apply -f infrastructure/kubernetes/service.yaml

echo -e "${GREEN}Deployment applied!${NC}"
echo -e "${YELLOW}Waiting for LoadBalancer IP (this may take a minute)...${NC}"
sleep 10
kubectl get svc nlp-sentiment-service