"""
Service layer for calling deployments and handling retries.
"""
import requests
import time
from typing import Dict, Any
from model.logger_config import get_logger
from .config import settings
from prometheus_client import Counter

logger = get_logger(__name__)

RETRY_ATTEMPTS = Counter(
    'backend_retry_attempts_total',
    'Total retry attempts by deployment',
    ['deployment', 'reason']
)

class SentimentAnalysisService:
    """Service for sentiment analysis with retry logic."""

    @staticmethod
    def analyze(text: str, deployment: str = "lambda") -> Dict[str, Any]:
        """
        Analyze sentiment with automatic retry on timeout.
        
        Args:
            text: Text to analyze
            deployment: Target deployment ('lambda' or 'kubernetes')
            
        Returns:
            Analysis result with metadata
            
        Raises:
            Exception: If analysis fails after retries
        """
        endpoint = SentimentAnalysisService._get_endpoint(deployment)
        if not endpoint:
            raise ValueError(f"Unknown deployment: {deployment}")
        
        start_time = time.time()
        backoff = settings.INITIAL_BACKOFF
        last_error = None

        logger.info(f"Analyzing text: '{text[:50]}...' on {deployment}")

        for attempt in range(settings.MAX_RETRIES):
            try:
                logger.info(f"Attempt {attempt + 1}/{settings.MAX_RETRIES}")
                
                response = requests.post(
                    endpoint,
                    json={"text": text},
                    timeout=settings.REQUEST_TIMEOUT
                )
                
                # Success
                if response.status_code == 200:
                    logger.info(f"Success on attempt {attempt + 1}")
                    elapsed_ms = (time.time() - start_time) * 1000
                    
                    return {
                        **response.json(),
                        "retry_attempts": attempt,
                        "response_time_ms": elapsed_ms,
                        "deployment": deployment
                    }
                
                # Timeout (cold start)
                elif response.status_code == 504:
                    RETRY_ATTEMPTS.labels(deployment=deployment, reason="504_timeout").inc()
                    last_error = "504 Gateway Timeout"
                    logger.warning(f"{last_error}")
                    
                    if attempt < settings.MAX_RETRIES - 1:
                        logger.info(f"Waiting {backoff}s before retry...")
                        time.sleep(backoff)
                        backoff *= 1.5
                    else:
                        raise Exception(f"{last_error} after {settings.MAX_RETRIES} attempts")
                
                # Other errors
                else:
                    raise Exception(f"{response.status_code}: {response.json().get('message', response.text)}")
            
            except requests.exceptions.Timeout:
                RETRY_ATTEMPTS.labels(deployment=deployment, reason="request_timeout").inc()
                last_error = "Request Timeout"
                logger.warning(f"{last_error}")
                
                if attempt < settings.MAX_RETRIES - 1:
                    time.sleep(backoff)
                    backoff *= 1.5
                else:
                    raise Exception(f"{last_error} after {settings.MAX_RETRIES} attempts")
            
            except requests.exceptions.ConnectionError as e:
                raise Exception(f"Cannot reach {deployment} endpoint: {str(e)}")
        
        raise Exception(f"Failed: {last_error}")

    @staticmethod
    def _get_endpoint(deployment: str) -> str:
        """Get endpoint URL for deployment type."""
        if deployment == "lambda":
            return settings.LAMBDA_ENDPOINT
        elif deployment == "kubernetes":
            return settings.KUBERNETES_ENDPOINT
        return None