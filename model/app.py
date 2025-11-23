"""
FastAPI application for Kubernetes deployment.
"""
import time
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator

try:
    from .logger_config import setup_logger, get_logger
    from .model_loader import predict_sentiment, load_model
except ImportError:
    from logger_config import setup_logger, get_logger
    from model_loader import predict_sentiment, load_model

logger = get_logger("app")

# Initialize FastAPI app
app = FastAPI(
    title="NLP Sentiment Analysis API",
    description="DistilBERT sentiment analysis service",
    version="1.0.0"
)

Instrumentator().instrument(app).expose(app)

class SentimentRequest(BaseModel):
    """Request model for sentiment analysis."""
    text: str = Field(..., min_length=1, max_length=5000, description="text to analyze")

class SentimentResponse(BaseModel):
    """Response Model for sentiment analysis."""
    text: str
    sentiment: str
    confidence: float
    scores: Dict[str, float]

# load model at start up
@app.on_event("startup")
async def startup_event():
    """Load model when application starts."""
    logger.info("Starting up application...")
    try:
        load_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "nlp-sentiment-analysis"
    }

@app.post("/predict", response_model=SentimentResponse)
async def predict(request: SentimentRequest):
    """
    Predict sentiment for the given test.

    Args:
        request: SentimentRequest containing text to analyze

    Returns: 
        SentimentResponse with prediction results
    """
    start_time = time.time()

    try:
        result = predict_sentiment(request.text)
        
        # calculate latency
        latency = time.time() - start_time
        logger.info(f"Request processed in {latency:.4f}s")

        return SentimentResponse(**result)

    except ValueError as e:
        logger.error(f"validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error: {str(e)}")

if __name__=="__main__":
    # Locally run for testing
    uvicorn.run(app, host="0.0.0.0", port=8000)
