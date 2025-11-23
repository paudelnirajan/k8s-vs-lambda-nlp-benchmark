"""FastAPI application for NLP sentiment analysis backend"""
from model.logger_config import get_logger
from fastapi import FastAPI, HTTPException
from datetime import datetime
from .config import settings
from .models import AnalysisRequest, AnalysisResponse, HealthResponse
from .services import SentimentAnalysisService
import time

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, REGISTRY

logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Unified backend for Lambda and Kubernetes deployments",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Custom metrics for deployment comparison
# Create metrics with duplicate handling for module reloads
def create_metric(metric_type, name, documentation, labelnames, **kwargs):
    """Create a metric, handling duplicates from module reloads."""
    try:
        if metric_type == 'counter':
            return Counter(name, documentation, labelnames)
        elif metric_type == 'histogram':
            return Histogram(name, documentation, labelnames, **kwargs)
    except ValueError:
        # Metric already registered, retrieve it from registry
        return REGISTRY._names_to_collectors[name + '_total'] if metric_type == 'counter' else REGISTRY._names_to_collectors[name + '_bucket']

DEPLOYMENT_REQUEST_COUNT = create_metric(
    'counter',
    'backend_deployment_requests',
    'Total backend requests by deployment',
    ['deployment', 'status']
)

DEPLOYMENT_LATENCY = create_metric(
    'histogram',
    'backend_deployment_request_duration_seconds',
    'Backend request latency by deployment',
    ['deployment'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
)

RETRY_ATTEMPTS = create_metric(
    'counter',
    'backend_retry_attempts',
    'Total retry attempts by deployment',
    ['deployment', 'reason']
)

# This line ACTIVATES the metrics collection and exposes /metrics
Instrumentator().instrument(app).expose(app)

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "lambda_endpoint": settings.LAMBDA_ENDPOINT,
        "kubernetes_endpoint": settings.KUBERNETES_ENDPOINT,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze", response_model=AnalysisResponse)
def analyze_sentiment(request: AnalysisRequest):
    """
    Analyze sentiment with automatic retry on timeout.
    """
    start_time = time.time()
    try:
        result = SentimentAnalysisService.analyze(request.text, request.deployment)
        result["timestamp"] = datetime.now().isoformat()

        # Track successful request
        DEPLOYMENT_REQUEST_COUNT.labels(
            deployment=request.deployment, 
            status="success"
        ).inc()
        
        # Track latency
        DEPLOYMENT_LATENCY.labels(
            deployment=request.deployment
        ).observe(time.time() - start_time)

        return result
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")

        # Track failed request
        DEPLOYMENT_REQUEST_COUNT.labels(
            deployment=request.deployment, 
            status="error"
        ).inc()
        
        # Track latency even on failure
        DEPLOYMENT_LATENCY.labels(
            deployment=request.deployment
        ).observe(time.time() - start_time)
        
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/analyze-batch")
def analyze_batch(texts: list[str]):
    """Analyze multiple texts (for benchmarking)."""
    results = []
    for text in texts:
        try:
            result = analyze_sentiment(AnalysisRequest(text=text))
            results.append(result.dict())
        except HTTPException as e:
            results.append({"text": text, "error": e.detail})
    
    return {
        "total": len(texts),
        "successful": sum(1 for r in results if "error" not in r),
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )