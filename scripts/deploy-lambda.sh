#!/bin/bash
set -e

# Configuration
REGION="us-east-1"
FUNCTION_NAME="nlp-sentiment-analysis"
ECR_REPO_NAME="nlp-sentiment-analysis"
IMAGE_TAG="latest"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Lambda deployment...${NC}"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO_NAME}"

# Step 1: Create ECR repository if it doesn't exist
echo -e "${YELLOW}Creating ECR repository...${NC}"
aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${REGION} 2>/dev/null || \
aws ecr create-repository --repository-name ${ECR_REPO_NAME} --region ${REGION}

# Step 2: Login to ECR
echo -e "${YELLOW}Logging into ECR...${NC}"
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_URI}

# Step 3: Build Docker image (for x86_64 architecture)
echo -e "${YELLOW}Building Docker image for x86_64...${NC}"
PROJECT_ROOT="$(dirname "$0")/.."
cd "${PROJECT_ROOT}"
docker buildx build --platform linux/amd64 -t ${ECR_REPO_NAME}:${IMAGE_TAG} -f model/Dockerfile .

# Step 4: Tag image
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}

# Step 5: Push image to ECR
echo -e "${YELLOW}Pushing image to ECR...${NC}"
docker push ${ECR_URI}:${IMAGE_TAG}

# Step 6: Create or update Lambda function
echo -e "${YELLOW}Creating/updating Lambda function...${NC}"
if aws lambda get-function --function-name ${FUNCTION_NAME} --region ${REGION} &>/dev/null; then
    # Function exists, update code
    aws lambda update-function-code \
      --function-name ${FUNCTION_NAME} \
      --image-uri ${ECR_URI}:${IMAGE_TAG} \
      --region ${REGION}
    
    # Wait for update to complete
    echo -e "${YELLOW}Waiting for function update to complete...${NC}"
    aws lambda wait function-updated \
      --function-name ${FUNCTION_NAME} \
      --region ${REGION}
    
    # Update configuration (increased timeout for model download on first invocation)
    aws lambda update-function-configuration \
      --function-name ${FUNCTION_NAME} \
      --timeout 300 \
      --memory-size 3008 \
      --region ${REGION}
else
    # Function doesn't exist, create it
    aws lambda create-function \
      --function-name ${FUNCTION_NAME} \
      --package-type Image \
      --code ImageUri=${ECR_URI}:${IMAGE_TAG} \
      --role arn:aws:iam::${ACCOUNT_ID}:role/lambda-execution-role \
      --timeout 300 \
      --memory-size 3008 \
      --region ${REGION}
    
    # Wait for creation to complete
    echo -e "${YELLOW}Waiting for function creation to complete...${NC}"
    aws lambda wait function-active \
      --function-name ${FUNCTION_NAME} \
      --region ${REGION}
fi

echo -e "${GREEN}Lambda deployment complete!${NC}"
echo -e "${GREEN}Function ARN: $(aws lambda get-function --function-name ${FUNCTION_NAME} --region ${REGION} --query 'Configuration.FunctionArn' --output text)${NC}"