#!/bin/bash
set -e

# Configuration
REGION="us-east-1"
LAMBDA_REPO="nlp-sentiment-analysis"
K8S_REPO="nlp-sentiment-k8s"
TAG="latest"

echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com

echo "Building Lambda Image..."
docker buildx build --platform linux/amd64 --provenance=false -t $LAMBDA_REPO:$TAG -f model/Dockerfile.lambda .
docker tag $LAMBDA_REPO:$TAG $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/$LAMBDA_REPO:$TAG
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/$LAMBDA_REPO:$TAG

echo "Building K8s Image..."
docker buildx build --platform linux/amd64 -t $K8S_REPO:$TAG -f model/Dockerfile.k8s .
docker tag $K8S_REPO:$TAG $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/$K8S_REPO:$TAG
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/$K8S_REPO:$TAG

echo "Images pushed successfully!"