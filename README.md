# Serverless vs Kubernetes NLP Inference Benchmark

**Status:** CI/CD & Infrastructure Automated

A comprehensive benchmark comparing AWS Lambda and Kubernetes (EKS) deployments for NLP sentiment analysis using the DistilBERT model.

## Project Overview

This project implements a sentiment analysis service using the DistilBERT model and deploys it using two cloud architectures:

1. **Serverless Architecture:** AWS Lambda + API Gateway
2. **Container Orchestration:** AWS EKS (Kubernetes)

The goal is to benchmark performance, scalability, cost, and latency under various load conditions.

## System Architecture

![Architecture](Architecture.png)

## Technology Stack

### Core Components

* **Model:** DistilBERT-base-uncased
* **Language:** Python 3.9+
* **Container:** Docker
* **Orchestration:** Kubernetes (EKS)
* **Serverless:** AWS Lambda
* **CI/CD:** GitHub Actions + AWS ECR
* **IaC:** Terraform

## Project Structure

```
FinalProject/
├── README.md
├── .env
├── .github/
│   └── workflows/        # CI/CD Pipeline
│       └── deploy.yml    # Builds & pushes images to ECR on push
├── model/                # Shared Model/Worker Code
│   ├── app.py            # FastAPI app for K8s & Lambda
│   ├── lambda_handler.py # Entry point for Lambda
│   └── model_loader.py   # DistilBERT loader
│
├── backend/              # Orchestrator
│   └── main.py           # Router (Lambda vs K8s)
│
├── frontend/             # Streamlit Dashboard & Locust
│   ├── app.py
│   └── load-testing/     # Locust configurations
│
├── infrastructure/
│   └── terraform/        # IaC definition
│       ├── main.tf
│       ├── ec2.tf        # App Server (pulls from ECR)
│       ├── lambda.tf
│       ├── kubernetes.tf
│       └── ecr.tf        # Container Registry
│
└── scripts/
    ├── deploy_all.sh     # One-click deployment
    ├── run-metrics.sh    # Metrics fetcher
    └── run-tests.sh      # Integration tests
```

---

## Deployment Workflow

This project uses a fully automated CI/CD pipeline.

### Prerequisites

* AWS CLI configured
* Terraform installed
* GitHub Repository Secrets Configured: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`

---

### 1. Build & Push (CI/CD)

Simply push your code to the `main` branch.

GitHub Actions will automatically:<br>
**NOTE:** You need to have ECR repos named "nlp-backend" and "nlp-frontend" for these github actions to be succesfull.
1. Build Docker images for Backend and Frontend.
2. Authenticate with AWS.
3. Push images to **Amazon ECR**.

---

### 2. Deploy Infrastructure

Run the automated deployment script locally. This provisions EC2/EKS/Lambda and configures the servers to pull the latest images.

```bash
scripts/deploy_all.sh
```

---

### 3. Configure Secrets

The EC2 instance needs environment variables (API Keys, etc.).

```bash
# Get the App IP from the script output
APP_IP=$(terraform output -raw app_server_public_ip)

# Copy your local .env file to the server
scp -i infrastructure/terraform/nlp-project-key.pem .env ubuntu@$APP_IP:~/.env

# Move it to the app directory
ssh -i infrastructure/terraform/nlp-project-key.pem ubuntu@$APP_IP "sudo mv ~/.env /home/ubuntu/app/.env"
```

**Credentials on the EC2 instance**
I attached an **IAM Instance Profile** (`AmazonEC2ContainerRegistryReadOnly`).
This allows the server to securely pull Docker images from ECR without storing sensitive keys on disk.

```bash
# Get the App IP from the script output
APP_IP=$(terraform output -raw app_server_public_ip)

# Copy your local .env file to the server
scp -i infrastructure/terraform/nlp-project-key.pem .env ubuntu@$APP_IP:~/.env
```

---

### CI/CD & DevOps

#### Automated Image Builds (GitHub Actions)

I shifted from building Docker images on the production server (slow, resource-intensive) to a CI/CD pipeline.

* **Old Way:** `docker-compose build` on EC2.
* **New Way:** GitHub Actions builds images and pushes to **Amazon ECR**. EC2 simply pulls the pre-built images.
* **Benefit:** Faster deployment times and guaranteed consistency between environments.

#### Docker Context & Volumes

I encountered issues where test scripts (`load-testing/`) were missing in the container due to `.dockerignore` rules or caching.

* **Solution:** Use **Volume Mounts** in `docker-compose.yml` to map test scripts from the host directly into the container.

This ensures the benchmark engine always has the latest scripts without requiring a full image rebuild.

---

## Application Architecture

### Lambda Cold Starts vs. API Gateway Timeouts

* **Problem:** Loading DistilBERT takes ~60s, exceeding the 29s API Gateway timeout.
* **Solution:** The Orchestrator Backend implements exponential backoff — first request warms Lambda, second succeeds.

### Kubernetes Networking

LoadBalancer services take time to provision.
Terraform outputs and scripts handle this asynchronous behavior.

In production, I would use **Ingress Controllers (ALB)** for robust routing and health checks.

---

## Observability & AI Analysis

### Streamlit as an Ops Tool

Using Streamlit with `st.session_state` turns a Python script into a **stateful operations dashboard**, enabling:

* triggering background load tests
* real-time visualization of results

### AI-Driven Insights

Integrating LLMs (Llama 3 via Groq) to analyze raw CSV metrics creates an **Automated SRE**, identifying patterns such as:

* “Lambda latency spikes due to cold starts”

---

### 4. Restart Application

Reload the containers to apply the new configuration.

```bash
ssh -i infrastructure/terraform/nlp-project-key.pem ubuntu@$APP_IP "cd app && sudo docker-compose up -d --force-recreate"
```

---

## Testing

### Dashboard & Benchmarking

The project includes a Streamlit dashboard for real-time benchmarking.

1. Access the dashboard at `http://<APP_IP>:8501`.
2. **Live Comparison:** Send parallel requests to Lambda and Kubernetes.
3. **Load Testing:** Execute distributed Locust tests from the UI.
4. **AI Analysis:** Generate an SRE-style performance report using LLMs.

---

## License

This project is licensed under the MIT License.
