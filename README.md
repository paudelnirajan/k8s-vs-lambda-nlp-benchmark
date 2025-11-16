# Serverless vs Kubernetes NLP Inference Benchmark

***STATUS - `AWS Lambda deplpy complete`***

A comprehensive benchmark comparing AWS Lambda and Kubernetes (EKS) deployments for NLP sentiment analysis using DistilBERT model.

## Project Overview

This project implements a sentiment analysis service using the DistilBERT model and deploys it using two cloud architectures:

1. **Serverless Architecture**: AWS Lambda + API Gateway
2. **Container Orchestration**: AWS EKS (Kubernetes)

The goal is to benchmark performance, scalability, cost, and latency under various load conditions to provide data-driven recommendations for production deployment.

## Technology Stack

### Core Components

- **Model**: DistilBERT-base-uncased (Hugging Face) for sentiment analysis
- **Language**: Python 3.9+
- **ML Framework**: Transformers (Hugging Face), PyTorch
- **Container**: Docker
- **Orchestration**: Kubernetes (EKS)
- **Serverless**: AWS Lambda
- **API Gateway**: AWS API Gateway (REST)
- **Backend**: FastAPI with retry logic

### Infrastructure

- **AWS Services**: Lambda, API Gateway, ECR, CloudWatch
- **Kubernetes**: AWS EKS
- **Monitoring**: CloudWatch Logs, CloudWatch Metrics
- **IaC**: Terraform (planned)

### Development Tools

- **Load Testing**: k6 (planned)
- **Testing**: pytest
- **Container Registry**: Amazon ECR

## Project Status: Week 1 Complete

### Completed Tasks

#### 1. Foundation & Model Setup (Days 1-2)
- Selected and configured DistilBERT model for sentiment analysis
- Created local inference function with proper model loading
- Set up project dependencies in requirements.txt
- Configured logging with logger_config.py

#### 2. AWS Lambda Deployment (Days 3-5)
- Created Lambda function for NLP inference
- Built Docker image compatible with Lambda runtime (Python 3.9)
- Set up ECR (Elastic Container Registry) for Docker image storage
- Configured API Gateway REST endpoint for Lambda invocation
- Fixed architecture compatibility issue: converted ARM to x86_64 architecture
- Resolved module import errors in Lambda container
- Optimized timeout configuration: increased to 300 seconds for model download

#### 3. Cold Start Handling (Day 6)
- Implemented automatic retry logic with exponential backoff
- Set up cache directory for Hugging Face model in Lambda /tmp
- Configured proper error handling for 504 Gateway Timeout errors
- Created test script with retry mechanism for cold start scenarios

#### 4. Backend Service Architecture (Day 7)
- Designed and implemented FastAPI backend service with separation of concerns
- Created modular architecture:
  - config.py: Configuration management and environment variables
  - models.py: Pydantic request/response validation models
  - services.py: Business logic and retry logic service layer
  - main.py: FastAPI application and endpoints
- Implemented Health check endpoint for monitoring
- Created sentiment analysis endpoint with automatic retry on timeout
- Added batch analysis endpoint for benchmarking multiple requests
- Fixed response model validation to match Lambda output format

## Project Structure

```
FinalProject/
├── README.md
├── .env.example
├── .env
├── requirements.txt
├── requirements-backend.txt
│
├── model/
│   ├── __init__.py
│   ├── lambda_handler.py
│   ├── model_loader.py
│   ├── logger_config.py
│   ├── app.py
│   └── Dockerfile
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── services.py
│   └── requirements.txt
│
├── tests/
│   ├── __init__.py
│   ├── test_backend.py
│   └── test_api.py
│
├── scripts/
│   ├── deploy-lambda.sh
│   ├── setup-api-gateway.sh
│   ├── run-backend.sh
│   └── fastapi_combined.sh
│
└── infrastructure/
    ├── terraform/
    └── kubernetes/
```

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Buildx
- AWS CLI configured with credentials
- AWS Account with appropriate permissions
- Conda or virtualenv for Python environment

### Installation

1. Clone the repository:
```bash
cd /Users/nirajanpaudel17/Downloads/DCSC/FinalProject
```

2. Create and activate Conda environment:
```bash
conda create -n dcsc python=3.9
conda activate dcsc
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your AWS account details and endpoints
```

## Usage

### Running the Backend Service Locally

Start the FastAPI backend service:

```bash
python backend/main.py
```

Or using the provided script:

```bash
bash scripts/run-backend.sh
```

The backend will start on http://localhost:8000

Access API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

#### Health Check
```bash
curl -X GET http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "lambda_endpoint": "https://zyzss2dbwd.execute-api.us-east-1.amazonaws.com/prod/predict",
  "kubernetes_endpoint": null,
  "timestamp": "2025-11-15T23:50:00"
}
```

#### Sentiment Analysis
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product!", "deployment": "lambda"}'
```

Response:
```json
{
  "text": "I love this product!",
  "sentiment": "POSITIVE",
  "confidence": 0.9998,
  "scores": {
    "negative": 0.0002,
    "positive": 0.9998
  },
  "deployment": "lambda",
  "retry_attempts": 0,
  "response_time_ms": 150.25,
  "timestamp": "2025-11-15T23:50:00"
}
```

#### Batch Analysis
```bash
curl -X POST http://localhost:8000/analyze-batch \
  -H "Content-Type: application/json" \
  -d '["I love this!", "This is terrible.", "It is okay."]'
```

### Testing

Run unit tests:
```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_backend.py -v
```

## AWS Lambda Deployment

### Deploy Lambda Function

```bash
bash scripts/deploy-lambda.sh
```

This script will:
1. Build Docker image for x86_64 architecture
2. Push image to Amazon ECR
3. Create or update Lambda function with ECR image
4. Configure timeout and memory settings
5. Set up CloudWatch logging

### Configure API Gateway

```bash
bash scripts/setup-api-gateway.sh
```

This script will:
1. Create or retrieve REST API Gateway
2. Create /predict resource
3. Set up POST method with Lambda integration
4. Grant API Gateway permission to invoke Lambda
5. Deploy to prod stage

### Lambda Configuration

Current configuration:
- **Runtime**: Python 3.9 (containerized)
- **Memory**: 3008 MB (maximum available)
- **Timeout**: 300 seconds (5 minutes)
- **Architecture**: x86_64 (AWS Lambda standard)
- **Environment Variables**: HF_HOME=/tmp for Hugging Face cache

## Performance Characteristics

### Cold Start Behavior

On first invocation after deployment:
- Model download: 20-40 seconds
- API Gateway timeout limit: 29 seconds
- Solution: Automatic retry with exponential backoff (5s, 7.5s, 11s)

### Warm Start Behavior

After initial load:
- Response time: 150-300ms
- Model inference: 50-100ms
- API Gateway overhead: 100-200ms

## Environment Configuration

Key configuration options in .env:

```
LAMBDA_ENDPOINT=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/predict
MAX_RETRIES=3
INITIAL_BACKOFF=5
REQUEST_TIMEOUT=35
LOG_LEVEL=INFO
DEBUG=False
```

## Known Issues and Solutions

### Issue 1: Lambda Cold Start Timeout
**Problem**: First invocation times out due to model download exceeding API Gateway 29s limit
**Solution**: Backend implements automatic retry with exponential backoff

### Issue 2: Read-only File System
**Problem**: Hugging Face tries to write to home directory
**Solution**: Set HF_HOME=/tmp environment variable in Lambda

### Issue 3: Module Import Errors
**Problem**: Lambda container couldn't find custom modules
**Solution**: Ensure all modules copied to LAMBDA_TASK_ROOT in Dockerfile

## Next Steps (Week 2-3)

- [ ] Kubernetes cluster setup on AWS EKS
- [ ] Deploy model service to Kubernetes
- [ ] Configure Kubernetes HPA (Horizontal Pod Autoscaling)
- [ ] Set up Prometheus + Grafana monitoring
- [ ] Implement k6 load testing scenarios
- [ ] Run performance benchmarks
- [ ] Compare costs and latency metrics
- [ ] Document findings and recommendations

## Monitoring

### CloudWatch Logs

View Lambda logs:
```bash
aws logs tail /aws/lambda/nlp-sentiment-analysis --follow
```

View backend logs:
```bash
tail -f logs/backend_main.log
tail -f logs/backend_services.log
```

### Metrics to Track

- Lambda invocation count
- Lambda duration
- Lambda errors
- API Gateway latency
- Cold start frequency
- Warm start latency

## Architecture Decisions

### Why Lambda for First Phase?

1. **Simplicity**: Minimal infrastructure management
2. **Cost**: Pay per invocation model
3. **Scalability**: Automatic scaling
4. **Fast Iteration**: Quick deployment and testing

### Why FastAPI Backend?

1. **Retry Logic**: Handles Lambda cold starts gracefully
2. **Benchmarking**: Consistent testing interface for both Lambda and Kubernetes
3. **Monitoring**: Captures metrics for comparison
4. **Production Ready**: Standards-based API design

## Contributing

To contribute to this project:

1. Create a new branch for features
2. Make changes and test thoroughly
3. Update documentation
4. Submit pull request with description

## References

- Hugging Face Transformers: https://huggingface.co/transformers/
- DistilBERT Model: https://huggingface.co/distilbert-base-uncased
- AWS Lambda: https://docs.aws.amazon.com/lambda/
- FastAPI: https://fastapi.tiangolo.com/
- AWS EKS: https://docs.aws.amazon.com/eks/

## Contact

For questions or issues, please open an GitHub issue or contact the project maintainer.

## License

This project is licensed under the MIT License.