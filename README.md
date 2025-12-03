# Serverless vs Kubernetes NLP Inference Benchmark

A comprehensive benchmark comparing AWS Lambda and Kubernetes (EKS) deployments for NLP sentiment analysis using the DistilBERT model.

## Project Overview

This project implements a sentiment analysis service using the DistilBERT model and deploys it using two cloud architectures:

1. **Serverless Architecture:** AWS Lambda + API Gateway
2. **Container Orchestration:** AWS EKS (Kubernetes)

The goal is to benchmark performance, scalability, cost, and latency under various load conditions.

## System Architecture

![Architecture](Architecture.png)

### Infrastructure Components

```
+------------------------------------------------------------------+
|                     INFRASTRUCTURE OVERVIEW                       |
+------------------------------------------------------------------+
|                                                                   |
|  1. LAMBDA (Serverless)                                           |
|     Endpoint: https://xxx.execute-api.../prod/predict             |
|     Container: nlp-sentiment-analysis                             |
|     Use: Benchmarking serverless cold starts                      |
|                                                                   |
|  2. KUBERNETES (EKS)                                              |
|     Endpoint: http://xxx.elb.amazonaws.com/predict                |
|     Container: nlp-sentiment-k8s (2 replicas)                     |
|     Use: Benchmarking container orchestration                     |
|                                                                   |
|  3. EC2 INSTANCE                                                  |
|     Port 8501: Streamlit Frontend (nlp-frontend)                  |
|     Port 8000: FastAPI Backend (nlp-backend)                      |
|     Use: User-facing app that calls Lambda/K8s                    |
|                                                                   |
+------------------------------------------------------------------+
```

## Technology Stack

### Core Components

| Component | Technology |
|-----------|------------|
| Model | DistilBERT-base-uncased |
| Language | Python 3.9+ |
| Container | Docker |
| Orchestration | Kubernetes (EKS) |
| Serverless | AWS Lambda |
| CI/CD | GitHub Actions + AWS ECR |
| IaC | Terraform |

## Project Structure

```
FinalProject/
├── README.md
├── .env                      # Environment variables (not in git)
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD: Builds & pushes images to ECR
│
├── model/                    # Shared Model/Worker Code
│   ├── app.py                # FastAPI app for K8s & Lambda
│   ├── lambda_handler.py     # Entry point for Lambda
│   ├── model_loader.py       # DistilBERT loader
│   ├── Dockerfile.lambda     # Lambda container image
│   └── Dockerfile.k8s        # Kubernetes container image
│
├── backend/                  # Orchestrator Service
│   ├── main.py               # Router (Lambda vs K8s)
│   └── Dockerfile
│
├── frontend/                 # Streamlit Dashboard
│   ├── app.py
│   └── Dockerfile
│
├── infrastructure/
│   └── terraform/            # Infrastructure as Code
│       ├── main.tf           # VPC, EKS cluster
│       ├── ec2.tf            # App Server (pulls from ECR)
│       ├── lambda.tf         # Lambda + API Gateway
│       ├── kubernetes.tf     # K8s deployment & service
│       ├── ecr.tf            # Container registries
│       └── outputs.tf        # Deployment endpoints
│
├── load-testing/
│   ├── benchmark.py
│   └── locust/
│       └── locustfile.py     # Load testing configuration
│
├── scripts/
│   ├── deploy_all.sh         # One-click deployment
│   ├── terraform_destroy_safe.sh  # Safe teardown
│   ├── build_and_push.sh     # Build & push Lambda/K8s images
│   └── run-tests.sh          # Integration tests
│
└── tests/
    ├── test_backend.py
    └── test_model.py
```

---

## Deployment Guide

### Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform installed (v1.0+)
- Docker installed
- GitHub Repository Secrets configured:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION`

---

### Step 1: Initial Setup (One-Time)

Before first deployment, create the ECR repositories that GitHub Actions needs:

```bash
# Create ECR repositories
aws ecr create-repository --repository-name nlp-backend --region us-east-1
aws ecr create-repository --repository-name nlp-frontend --region us-east-1
aws ecr create-repository --repository-name nlp-sentiment-analysis --region us-east-1
aws ecr create-repository --repository-name nlp-sentiment-k8s --region us-east-1
```

---

### Step 2: Push Code to GitHub

Push your code to trigger GitHub Actions:

```bash
git add .
git commit -m "Deploy infrastructure"
git push origin main
```

GitHub Actions will automatically:
1. Build Docker images for Backend and Frontend
2. Authenticate with AWS
3. Push images to Amazon ECR

---

### Step 3: Build and Push Lambda/K8s Images

Build and push the model images locally:

```bash
./scripts/build_and_push.sh
```

This pushes:
- `nlp-sentiment-analysis:latest` (for Lambda)
- `nlp-sentiment-k8s:latest` (for Kubernetes)

---

### Step 4: Deploy Infrastructure

Run the deployment script:

```bash
./scripts/deploy_all.sh
```

This script will:
1. Initialize Terraform
2. Import existing ECR repositories
3. Create/update ECR repositories
4. Check if images exist (build if missing)
5. Deploy all infrastructure (VPC, EKS, EC2, Lambda, API Gateway)

**Expected Output:**

```
+------------------------------------------------------------------+
|                    DEPLOYMENT COMPLETE!                          |
+------------------------------------------------------------------+
|                                                                  |
|  LAMBDA (Serverless)                                             |
|  API Endpoint: https://xxx.execute-api.us-east-1.amazonaws.com/prod/predict
|                                                                  |
|  KUBERNETES (EKS)                                                |
|  API Endpoint: http://xxx.us-east-1.elb.amazonaws.com/predict
|                                                                  |
|  EC2 INSTANCE (x.x.x.x)                                          |
|  Frontend (Streamlit): http://x.x.x.x:8501
|  Backend (FastAPI):    http://x.x.x.x:8000
|                                                                  |
+------------------------------------------------------------------+
```

---

### Step 5: Configure Environment Variables (REQUIRED)

The EC2 instance needs your `.env` file with API keys and endpoints.

```bash
# Get the EC2 IP from Terraform output
cd infrastructure/terraform
EC2_IP=$(terraform output -raw ec2_public_ip)

# Copy your .env file to the server
scp -i nlp-project-key.pem ../../.env ubuntu@$EC2_IP:~/.env

# Move it to the app directory and restart containers
ssh -i nlp-project-key.pem ubuntu@$EC2_IP \
  "sudo mv ~/.env /home/ubuntu/app/.env && \
   cd /home/ubuntu/app && \
   sudo docker-compose up -d --force-recreate"
```

**Important:** The `.env` file must contain:
- `LAMBDA_ENDPOINT` - Your Lambda API Gateway URL
- `KUBERNETES_ENDPOINT` - Your K8s Load Balancer URL
- `GROQ_API_KEY` - For AI-powered analysis (optional)

---

### Step 6: Access the Application

| Service | URL |
|---------|-----|
| Streamlit Dashboard | `http://<EC2_IP>:8501` |
| Backend API | `http://<EC2_IP>:8000` |
| Lambda API | `https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/predict` |
| Kubernetes API | `http://<elb-hostname>/predict` |

---

## Teardown

To destroy all infrastructure:

```bash
./scripts/terraform_destroy_safe.sh
```

This script:
1. Destroys K8s service first (releases Load Balancer)
2. Waits for ENIs to detach
3. Destroys remaining infrastructure

---

## Daily Workflow

| Action | Command |
|--------|---------|
| Deploy everything | `./scripts/deploy_all.sh` |
| Destroy everything | `./scripts/terraform_destroy_safe.sh` |
| Rebuild Lambda/K8s images | `./scripts/build_and_push.sh` |
| Update backend/frontend | `git push origin main` (triggers GitHub Actions) |

---

## Testing and Benchmarking

### Dashboard Features

Access the Streamlit dashboard at `http://<EC2_IP>:8501`:

1. **Live Comparison:** Send parallel requests to Lambda and Kubernetes
2. **Load Testing:** Execute distributed Locust tests from the UI
3. **AI Analysis:** Generate SRE-style performance reports using LLMs

### Running Tests

```bash
# Run integration tests
./scripts/run-tests.sh

# Run load tests with Locust
./scripts/run-locust.sh
```

---

## Technical Notes

### Lambda Cold Starts vs. API Gateway Timeouts

- **Problem:** Loading DistilBERT takes ~60s, exceeding the 29s API Gateway timeout
- **Solution:** The Backend implements exponential backoff - first request warms Lambda, second succeeds

### Kubernetes Networking

- LoadBalancer services take time to provision
- Terraform outputs handle this asynchronous behavior
- In production, use Ingress Controllers (ALB) for robust routing

### EC2 IAM Permissions

The EC2 instance has an IAM Instance Profile with `AmazonEC2ContainerRegistryReadOnly` policy. This allows secure image pulls from ECR without storing credentials on disk.

---

## Troubleshooting

### ECR Repository Already Exists

If Terraform fails with "repository already exists":

```bash
cd infrastructure/terraform
terraform import aws_ecr_repository.backend_repo nlp-backend
terraform import aws_ecr_repository.frontend_repo nlp-frontend
terraform import aws_ecr_repository.lambda_repo nlp-sentiment-analysis
terraform import aws_ecr_repository.k8s_repo nlp-sentiment-k8s
```

### Kubernetes Deployment Already Exists

```bash
terraform state rm kubernetes_deployment.nlp_deployment
terraform state rm kubernetes_service.nlp_service
terraform apply -auto-approve
```

### Lambda Image Not Found

Ensure images are pushed before creating Lambda:

```bash
./scripts/build_and_push.sh
terraform apply -auto-approve
```

---

## License

This project is licensed under the MIT License.
