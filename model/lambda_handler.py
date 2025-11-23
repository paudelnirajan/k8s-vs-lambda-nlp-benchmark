"""
AWS Lambda handler for sentiment analysis.
"""

import json
import logging
import sys
import time
import traceback
import os
from typing import Dict, Any

# Ensure cache directories exist before importing transformers
os.makedirs('/tmp/transformers_cache', exist_ok=True)
os.makedirs('/tmp/hf_cache', exist_ok=True)
os.environ['TRANSFORMERS_CACHE'] = '/tmp/transformers_cache'
os.environ['HF_HOME'] = '/tmp/hf_cache'

try:
    # Attempt absolute import first (Works in Lambda where files are at root)
    from logger_config import setup_logger, get_logger
    from model_loader import predict_sentiment, load_model
except ImportError:
    # Fallback to relative import (Works locally when running as a module)
    from .logger_config import setup_logger, get_logger
    from .model_loader import predict_sentiment, load_model

logger = get_logger(__name__)

# Global flag to track if model is loaded
_model_loaded = False

def _ensure_model_loaded():
    """Ensure model is loaded, load if not already loaded."""
    global _model_loaded
    if not _model_loaded:
        logger.info("Loading model at cold start...")
        try:
            load_model()
            _model_loaded = True
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}", exc_info=True)
            raise

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    # Load model on first invocation (lazy loading)
    try:
        _ensure_model_loaded()
    except Exception as e:
        logger.error(f"Model initialization failed: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Model initialization failed",
                "message": str(e)
            })
        }
    
    start_time = time.time()

    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        text = body.get("text", "")
        if not text:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Missing 'text' field in request body"
                })
            }
        
        # Run prediction
        result = predict_sentiment(text)

        # Calculate latency
        latency = time.time() - start_time
        logger.info(f"Request processed in {latency:.4f}s")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(result)
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": str(e)
            })
        }
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "message": f"Error: {str(e)}",
                "type": type(e).__name__
            })
        }