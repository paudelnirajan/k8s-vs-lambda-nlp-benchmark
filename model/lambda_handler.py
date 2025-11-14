"""
AWS Lambda handler for sentiment analysis.
"""

import json
import logging
import time
from typing import Dict, Any

# configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# import model loader
from model_loader import predict_sentiment, load_model

# load model once at cold start - this will be cached as long as the container is warm -- no need to load model again if the container's resources are not taken -- applies for the awsLambda

logger.info("Loading model at cold start...")
try:
    load_model()
    logger.info("Model loaded sucessfully")
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    raise

def lambda_handler(event: Dict[str, Any], content: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    start_time = time.time()

    try:
        # Parse request body
        if isinstance(event.get("body", str)):
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
        
        # run prediction
        result = predict_sentiment(text)

        # calculate latency
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
        logger.error(f"Validation error: {str(e)}")
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
        logger.error(f"Error processing request: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        }