# Serverless vs Kubernetes NLP Inference Benchmark

**STATUS: AWS Lambda & Kubernetes Deployment Complete**

A comprehensive benchmark comparing AWS Lambda and Kubernetes (EKS) deployments for NLP sentiment analysis using DistilBERT model.

## Project Overview

This project implements a sentiment analysis service using the DistilBERT model and deploys it using two cloud architectures:

1. **Serverless Architecture**: AWS Lambda + API Gateway
2. **Container Orchestration**: AWS EKS (Kubernetes)

The goal is to benchmark performance, scalability, cost, and latency under various load conditions.

## System Architecture

![Architecture](Architecture.png)

## Technology Stack

### Core Components

- **Model**: DistilBERT-base-uncased
- **Language**: Python 3.9+
- **Container**: Docker
- **Orchestration**: Kubernetes (EKS)
- **Serverless**: AWS Lambda
- **IaC**: Terraform

## Project Structure

```
FinalProject/
├── README.md
├── .env
├── model/                  \# The shared Model/Worker Code
│   ├── app.py              \# FastAPI app for K8s & Lambda
│   ├── lambda\_handler.py   \# Entry point for Lambda
│   ├── model\_loader.py     \# DistilBERT loader
│   ├── Dockerfile.k8s
│   └── Dockerfile.lambda
│
├── backend/                \# The Orchestrator
│   ├── main.py             \# Router (Lambda vs K8s)
│   └── services.py         \# Retry logic
│
├── infrastructure/
│   ├── terraform/          \# Full IaC definition
│   │   ├── main.tf
│   │   ├── lambda.tf
│   │   ├── kubernetes.tf
│   │   └── ecr.tf
│
└── scripts/
├── build\_and\_push.sh   \# Docker build helper
├── run-metrics.sh      \# Metrics fetcher
└── run-tests.sh        \# Integration tests
```

## Deployment Workflow (Terraform)

This project uses Terraform for full infrastructure management.

### Prerequisites
- AWS CLI configured
- Terraform installed
- Docker installed

### Deployment Steps

1. **Initialize Terraform**
   ```bash
   cd infrastructure/terraform
   terraform init
    ```

2.  **Create ECR Repositories**

    ```bash
    terraform apply -target=aws_ecr_repository.lambda_repo -target=aws_ecr_repository.k8s_repo
    ```

3.  **Build and Push Images**

    ```bash
    cd ../..
    bash scripts/build_and_push.sh
    ```

4.  **Deploy Application (Lambda & K8s)**

    ```bash
    cd infrastructure/terraform
    terraform apply
    ```

5.  **Verify**
    The output will provide the API Gateway URL and K8s LoadBalancer hostname. Add these to your `.env` file.

## Testing

### Run Integration Tests

```bash
bash scripts/run-realAPI-tests.sh
```

### View Metrics

```bash
bash scripts/run-metrics.sh
```

## Performance Notes

### Cold Starts

  - **Lambda**: Initial load takes \~60 seconds. The backend handles this via exponential backoff retries.
  - **Kubernetes**: Pods stay warm, offering consistent low latency (\<200ms).

### Monitoring

  - **Lambda**: Uses CloudWatch Logs and Metrics.
  - **Kubernetes**: Exposes Prometheus metrics at `/metrics`.

## License

This project is licensed under the MIT License.
