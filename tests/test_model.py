import pytest
from fastapi.testclient import TestClient
from model.app import app

client = TestClient(app)

class TestModelHealth:
    """Test model service health"""
    
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

class TestModelPredict:
    """Test model prediction endpoint"""
    
    def test_predict_valid_text(self):
        response = client.post(
            "/predict",
            json={"text": "I love this product!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "sentiment" in data
        assert "confidence" in data
        assert data["sentiment"] in ["POSITIVE", "NEGATIVE"]
        assert 0 <= data["confidence"] <= 1
    
    def test_predict_rejects_empty_text(self):
        response = client.post(
            "/predict",
            json={"text": ""}
        )
        assert response.status_code == 422  # Validation error