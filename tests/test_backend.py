import pytest
from fastapi.testclient import TestClient
from backend.main import app

# create test client
client = TestClient(app)

class TestHealthEndpoint():
    """Test suite for /health endpoint"""

    def test_health_check_returns_200(self):
        """Test that /health endpoint returns 200 status code"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_has_required_fields(self):
        """Test that /health response has all required fields"""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    def test_health_check_has_endpoints(self):
        """Test that /health returns endpoint information"""
        response = client.get("/health")
        data = response.json()

        # These might be None if not configured, but keys should exist
        assert "lambda_endpoint" in data
        assert "kubernetes_endpoint" in data


class TestAnalyzeEndpoint:
    """Test suite for /analyze endpoint"""

    # mock tests
    def test_analyze_with_lambda_mock(self, mock_sentiment_service):
        """Test /analyze with Lambda deployment (MOCKED)"""
        response = client.post(
            "/analyze",
            json={
                "text": "I love this product!",
                "deployment": "lambda"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] in ["POSITIVE", "NEGATIVE"]
        assert data["deployment"] == "lambda"
        assert "response_time_ms" in data

    def test_analyze_with_kubernetes_mock(self, mock_sentiment_service):
        """Test /analyze with Kubernetes deployment (MOCKED)"""
        response = client.post(
            "/analyze",
            json={
                "text": "This is terrible!",
                "deployment": "kubernetes"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deployment"] == "kubernetes"

    # REAL ENDPOINT TESTS (requires services running)
    def test_analyze_real_lambda(self, use_real_endpoints):
        """Test /analyze with REAL Lambda endpoint"""
        if not use_real_endpoints:
            pytest.skip("Skipping real endpoint test - set USE_REAL_ENDPOINTS=true to run")
        
        response = client.post(
            "/analyze",
            json={
                "text": "I absolutely love this lambda deployment!",
                "deployment": "lambda"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "sentiment" in data
        assert "confidence" in data
        print(f"Real Lambda Response: {data}")

    def test_analyze_real_kubernetes(self, use_real_endpoints):
        """Test /analyze with REAL Kubernetes endpoint"""
        if not use_real_endpoints:
            pytest.skip("Skipping real endpoint test - set USE_REAL_ENDPOINTS=true to run")
        
        response = client.post(
            "/analyze",
            json={
                "text": "This is a terrible experience.",
                "deployment": "kubernetes"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "sentiment" in data
        print(f"Real Kubernetes Response: {data}")