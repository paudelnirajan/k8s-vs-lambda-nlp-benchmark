# Key Takeaways and Technical Learnings

## Infrastructure as Code (Terraform)

### Automation & State Management
Terraform manages the entire lifecycle, from ECR repositories to EKS clusters. We moved from manual resource creation to a fully declared state, preventing configuration drift.

### IAM Roles & Instance Profiles
Instead of hardcoding AWS credentials on the EC2 instance, we attached an **IAM Instance Profile** (`AmazonEC2ContainerRegistryReadOnly`). This allows the server to securely pull Docker images from ECR without storing sensitive keys on disk.

## CI/CD & DevOps

### Automated Image Builds (GitHub Actions)
We shifted from building Docker images on the production server (slow, resource-intensive) to a CI/CD pipeline.
-   **Old Way:** `docker-compose build` on EC2.
-   **New Way:** GitHub Actions builds images and pushes to **Amazon ECR**. EC2 simply pulls the pre-built images.
-   **Benefit:** Faster deployment times and guaranteed consistency between environments.

### Docker Context & Volumes
We encountered issues where test scripts (`load-testing/`) were missing in the container due to `.dockerignore` rules or caching.
-   **Solution:** We used **Volume Mounts** in `docker-compose.yml` to map the test scripts from the host directly into the container. This ensures the benchmark engine always has the latest scripts without requiring a full image rebuild.

## Application Architecture

### Lambda Cold Starts vs. API Gateway Timeouts
-   **Problem:** Loading DistilBERT takes ~60s, exceeding the 29s API Gateway timeout.
-   **Solution:** The Orchestrator Backend implements exponential backoff. The first request fails (warming the Lambda), and the retry succeeds.

### Kubernetes Networking
LoadBalancer services take time to provision. Our Terraform outputs and scripts handle this asynchronous nature, but in production, we would use **Ingress Controllers** (ALB) for more robust routing and health checks.

## Observability & AI Analysis

### Streamlit as an Ops Tool
Using Streamlit with `st.session_state` effectively turns a Python script into a stateful Operations Dashboard, allowing us to trigger background load tests and visualize results in real-time.

### AI-Driven Insights
Integrating LLMs (Llama 3 via Groq) to analyze raw CSV metrics offers immediate, high-level insights. The system acts as an "Automated SRE," identifying performance bottlenecks (e.g., "Lambda Latency Spikes due to Cold Starts") that might be missed in raw logs.
