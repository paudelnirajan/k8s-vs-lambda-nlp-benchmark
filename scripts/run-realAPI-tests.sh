#!/bin/bash
# Run tests against REAL Lambda and Kubernetes endpoints

echo "================================"
echo "Running Real Endpoint Tests"
echo "================================"

# Must have environment variables set
if [ -z "$LAMBDA_ENDPOINT" ] || [ -z "$KUBERNETES_ENDPOINT" ]; then
    echo "ERROR: LAMBDA_ENDPOINT and KUBERNETES_ENDPOINT must be set"
    echo "Example:"
    echo "  export LAMBDA_ENDPOINT='https://xxx.lambda-url.us-east-1.on.aws/'"
    echo "  export KUBERNETES_ENDPOINT='http://your-k8s-service.com:8000'"
    exit 1
fi

echo "Testing Lambda endpoint: $LAMBDA_ENDPOINT"
echo "Testing Kubernetes endpoint: $KUBERNETES_ENDPOINT"
echo ""

# Run tests with real endpoints enabled
USE_REAL_ENDPOINTS=true pytest tests/test_backend.py::TestAnalyzeEndpoint::test_analyze_real_lambda -v
USE_REAL_ENDPOINTS=true pytest tests/test_backend.py::TestAnalyzeEndpoint::test_analyze_real_kubernetes -v

echo ""
echo "================================"
echo "Real Endpoint Tests Complete"
echo "================================"