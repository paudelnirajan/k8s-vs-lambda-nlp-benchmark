# Serverless vs Kubernetes NLP Inference Benchmark

**Status:** AWS Lambda & Kubernetes Deployment Complete

A comprehensive benchmark comparing AWS Lambda and Kubernetes (EKS) deployments for NLP sentiment analysis using the DistilBERT model.

## Project Overview

This project implements a sentiment analysis service using the DistilBERT model and deploys it using two cloud architectures:

1.  **Serverless Architecture:** AWS Lambda + API Gateway
2.  **Container Orchestration:** AWS EKS (Kubernetes)

The goal is to benchmark performance, scalability, cost, and latency under various load conditions.

## System Architecture

![Architecture](Architecture.png)

## Technology Stack

### Core Components
-   **Model:** DistilBERT-base-uncased
-   **Language:** Python 3.9+
-   **Container:** Docker
-   **Orchestration:** Kubernetes (EKS)
-   **Serverless:** AWS Lambda
-   **IaC:** Terraform

## Project Structure

```
FinalProject/
├── README.md
├── .env
├── model/                  # Shared Model/Worker Code
│   ├── app.py              # FastAPI app for K8s & Lambda
│   ├── lambda_handler.py   # Entry point for Lambda
│   ├── model_loader.py     # DistilBERT loader
│   ├── Dockerfile.k8s
│   └── Dockerfile.lambda
│
├── backend/                # Orchestrator
│   ├── main.py             # Router (Lambda vs K8s)
│   └── services.py         # Retry logic
│
├── frontend/               # Streamlit Dashboard & Locust
│   ├── app.py
│   ├── Dockerfile
│   └── load-testing/       # Locust configurations
│
├── infrastructure/
│   ├── terraform/          # IaC definition
│   │   ├── main.tf
│   │   ├── lambda.tf
│   │   ├── kubernetes.tf
│   │   └── ecr.tf
│
└── scripts/
    ├── deploy_all.sh       # One-click deployment
    ├── build_and_push.sh   # Docker build helper
    ├── run-metrics.sh      # Metrics fetcher
    └── run-tests.sh        # Integration tests
```

## Deployment Workflow

This project uses Terraform for full infrastructure management.

### Prerequisites
-   AWS CLI configured
-   Terraform installed
-   Docker installed

### Deployment Steps

1.  **Deploy Infrastructure**
    Run the automated deployment script which initializes Terraform, provisions EC2/EKS/Lambda, and builds the application on the remote server.
    ```bash
    bash scripts/deploy_all.sh
    ```

2.  **Configure Environment Variables**
    The deployment script output will provide the API Gateway URL and K8s LoadBalancer hostname.
    -   Copy your local `.env` file to the server:
        ```bash
        scp -i infrastructure/terraform/nlp-project-key.pem .env ubuntu@<APP_IP>:~/.env
        ```
    -   SSH into the server and move the file:
        ```bash
        ssh -i infrastructure/terraform/nlp-project-key.pem ubuntu@<APP_IP>
        sudo mv ~/.env /home/ubuntu/app/.env
        ```

3.  **Restart Application**
    Reload the containers to apply the new configuration.
    ```bash
    cd /home/ubuntu/app
    sudo docker-compose up -d --force-recreate
    ```

## Testing

### Dashboard & Benchmarking
The project includes a Streamlit dashboard for real-time benchmarking.

1.  Access the dashboard at `http://<APP_IP>:8501`.
2.  **Live Comparison:** Send parallel requests to Lambda and Kubernetes to observe cold starts vs. warm latency.
3.  **Load Testing:** Execute distributed Locust tests directly from the UI to measure throughput (RPS) and failure rates.
4.  **AI Analysis:** Generate an SRE-style performance report using LLMs based on the benchmark data.

### Manual Integration Tests
```bash
bash scripts/run-realAPI-tests.sh
```

## Performance Notes

### Cold Starts
-   **Lambda:** Initial load takes ~60 seconds. The backend handles this via exponential backoff retries.
-   **Kubernetes:** Pods stay warm, offering consistent low latency (<200ms).

### Monitoring
-   **Lambda:** Uses CloudWatch Logs and Metrics.
-   **Kubernetes:** Exposes Prometheus metrics at `/metrics`.

## License
This project is licensed under the MIT License.

