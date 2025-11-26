
# Key Takeaways and Technical Learnings

## Infrastructure as Code (Terraform)

### Migration from Manual Scripts
Transitioning from manual AWS CLI scripts to Terraform provided consistency and state management. The modular approach (separating `ec2.tf`, `eks.tf`, `lambda.tf`) allowed for easier debugging and independent resource scaling.

### Resource Dependencies
Defining explicit dependencies (`depends_on`) is critical when resources rely on the completion of others (e.g., waiting for EKS cluster readiness before deploying Kubernetes manifests).

## Containerization & Docker

### Docker Context & Build Strategy
A common pitfall is the Docker build context. When building images that require files from multiple directories (e.g., `model/` and `frontend/`), the build context must be set to the project root.
-   **Issue:** `COPY . .` respects `.dockerignore`. If a folder (like `load-testing/`) is ignored, it will be missing in the container, causing runtime errors.
-   **Solution:** Verify `.dockerignore` rules carefully and use `docker-compose build --no-cache` to ensure clean builds when file structures change.

### Cross-Platform Compatibility
Building Docker images on Apple Silicon (ARM64) for AWS Lambda (x86_64) requires explicit platform flags:
```bash
docker build --platform linux/amd64 ...
```
Using `--provenance=false` is also recommended for compatibility with older AWS Lambda container loaders.

## Deployment Strategy & Security

### Environment Variable Management
Handling secrets (API Keys, URLs) in a production-like environment requires careful planning.
-   **Current Approach:** Manual `scp` of `.env` file (Secure but manual).
-   **Industry Standard:** Use **AWS Systems Manager (SSM) Parameter Store** or **AWS Secrets Manager**. Terraform should provision an IAM role allowing the EC2 instance to fetch secrets at runtime, eliminating manual file transfers.

### Continuous Deployment (CD)
Instead of building images on the production server (which consumes resources and delays startup), a CI/CD pipeline (e.g., GitHub Actions) should build the images, push them to ECR, and simply refresh the ECS/EKS service.

## Application Architecture

### Lambda Cold Starts vs. API Gateway Timeouts
-   **Problem:** Loading large NLP models (DistilBERT) takes ~60s, exceeding the 29s hard timeout of API Gateway.
-   **Solution:** Implemented exponential backoff in the orchestrator backend. The first request acts as a "health check" to warm the container, while subsequent requests succeed.
-   **Optimization:** Using Provisioned Concurrency for Lambda would eliminate this but increase costs.

### Kubernetes Networking
LoadBalancer services expose the application root. If the application is namespaced or served on a specific path (e.g., `/predict`), the client must append this path explicitly to avoid 404 errors.

## Observability & Benchmarking

### Streamlit as a Control Plane
Using Streamlit with `st.session_state` effectively turns a script into a stateful application. This allows for managing long-running background processes (like Locust load tests) without blocking the UI.

### AI-Driven Observability
Integrating LLMs (Llama 3 via Groq) to analyze raw CSV metrics offers immediate, high-level insights. Instead of manual graph interpretation, the system acts as an "Automated SRE," highlighting anomalies and bottlenecks in plain English.
```