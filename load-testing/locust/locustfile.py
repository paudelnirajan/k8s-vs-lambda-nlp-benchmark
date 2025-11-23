from locust import HttpUser, task, between
import random

class SentimentAnalysisUser(HttpUser):
    """Simulates a user making requests to sentiment analysis API"""

    wait_time = between(1, 3) # wait 1-3 seconds between requests

    # test texts
    test_texts = [
        "I specially love this product!",
        "This is terrible and I hate it",
        "It's okay, nothing special",
        "Amazing experience, highly recommend",
        "Worst purchase ever made"
    ]

    @task(3)
    def analyze_lambda(self):
        """Test Lambda Endpoint (3x frequency)"""
        text = random.choice(self.test_texts)
        self.client.post(
            "/analyze",
            json={"text": text, "deployment": "lambda"},
            name="/analyze_lambda"
        )

    @task(3)
    def analyze_kubernetes(self):
        """Tests Kubernetes endpoint (3x frequency)"""
        text = random.choice(self.test_texts)
        self.client.post(
            "/analyze",
            json={"text": text, "deployment": "kubernetes"},
            name="/analyze_kubernetes"
        )

    @task(1)
    def health_check(self):
        """Health check endpoint (1x frequency)"""
        self.client.get("/health", name="/health")