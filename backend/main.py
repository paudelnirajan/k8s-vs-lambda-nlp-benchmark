"""FastAPI application for NLP sentiment analysis backend"""
from model.logger_config import get_logger
from fastapi import FastAPI, HTTPException
from datetime import datetime
from .config import settings
from .models import AnalysisRequest, AnalysisResponse, HealthResponse
from .services import SentimentAnalysisService


logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Unified backend for Lambda and Kubernetes deployments",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

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
    try:
        result = SentimentAnalysisService.analyze(request.text, request.deployment)
        result["timestamp"] = datetime.now().isoformat()
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
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