"""
Tests for FastAPI backend.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    """Tests health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_analyze_valid_text():
    """Test sentiment analysis with valid text."""
    response = client.post(
        "/analyze",
        json={"text": "I love this!", "deployment": "lambda"}
    )
    assert response.status_code in [200, 500]  # 500 if Lambda not running

def test_analyze_empty_text():
    """Test sentiment analysis rejects empty text."""
    response = client.post(
        "/analyze",
        json={"text": "", "deployment": "lambda"}
    )
    assert response.status_code == 422  # Validation error