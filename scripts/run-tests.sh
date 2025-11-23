#!/bin/bash
# run all tests with pytest

echo "================================"
echo "Running Unit Tests"
echo "================================"

# install pytest dependencies if not installed
# pip install pytest pytest-asyncio

echo ""
echo "Running backend tests..."
pytest tests/test_backend.py -v

echo ""
echo "Running model tests (locally)..."
pytest tests/test_model.py -v 2>/dev/null || echo "Model tests file not yet created."

echo ""
echo "================================"
echo "Test Summary"
echo "================================"
pytest tests/ -v --tb=short