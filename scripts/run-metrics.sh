#!/bin/bash
# View metrics from deployed Lambda and Kubernetes endpoints

echo "================================"
echo "Fetching Deployed Endpoint Metrics"
echo "================================"

# Load environment variables from .env file
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Use provided args or fall back to .env values
# LAMBDA_ENDPOINT="${1:-$LAMBDA_ENDPOINT}"
KUBERNETES_ENDPOINT="${2:-$KUBERNETES_ENDPOINT}"

# Check if endpoints are provided
if [ -z "$LAMBDA_ENDPOINT" ] || [ -z "$KUBERNETES_ENDPOINT" ]; then
    echo "ERROR: Both Lambda and Kubernetes endpoints are required"
    echo ""
    echo "Usage:"
    echo "  $0 [LAMBDA_ENDPOINT] [KUBERNETES_ENDPOINT]"
    echo ""
    echo "Endpoints can be provided as arguments or in .env file:"
    echo "  LAMBDA_ENDPOINT=<url>"
    echo "  KUBERNETES_ENDPOINT=<url>"
    echo ""
    exit 1
fi

# Strip '/predict' suffix to get the base URL...this is done because the env variable already contains the predict and here we need to strip that one
LAMBDA_BASE="${LAMBDA_ENDPOINT%/predict}"
KUBERNETES_BASE="${KUBERNETES_ENDPOINT%/predict}"

echo "Lambda Base URL:     $LAMBDA_BASE"
echo "Kubernetes Base URL: $KUBERNETES_BASE"
echo ""

# echo "=== Lambda Metrics ==="
# Fetch metrics from the base URL + /metrics
# curl -s "$LAMBDA_BASE/metrics" | head -50 || echo "Failed to fetch Lambda metrics"
# echo ""
# echo "... (showing first 50 lines)"
# echo ""

echo "=== Kubernetes Metrics ==="
# Fetch metrics from the base URL + /metrics
curl -s "$KUBERNETES_BASE/metrics" | head -50 || echo "Failed to fetch Kubernetes metrics"
echo ""
echo "... (showing first 50 lines)"
echo ""

echo "To view all metrics:"
# echo "  curl $LAMBDA_BASE/metrics | less"
echo "  curl $KUBERNETES_BASE/metrics | less"