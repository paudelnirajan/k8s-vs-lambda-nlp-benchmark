import pytest
from unittest.mock import Mock, patch
import os

# fixtures for mock api calls
@pytest.fixture
def mock_sentiment_service():
    """Mock the SentimentAnalysisService for unit tests"""
    with patch('backend.services.SentimentAnalysisService.analyze') as mock:
        # Mock response for Lambda
        mock.side_effect = lambda text, deployment: {
            "text": text,
            "sentiment": "POSITIVE",
            "confidence": 0.95,
            "scores": {"positive": 0.95, "negative": 0.05},
            "deployment": deployment,
            "retry_attempts": 0,
            "response_time_ms": 150.0
        }
        yield mock

# fixture to switch between mock and real based on env variable
@pytest.fixture
def use_real_endpoints():
    """
    Returns True if USE_REAL_ENDPOINTS=true in environment
    Otherwise returns False (use mocks)
    
    Usage in tests:
        def test_something(use_real_endpoints):
            if use_real_endpoints:
                # Test real endpoints
            else:
                # Test with mocks
    """
    return os.getenv("USE_REAL_ENDPOINTS", "false").lower() == "true"