#!/usr/bin/env python3
"""
Test script for API Gateway endpoint with automatic retry on timeout.
Handles cold start gracefully by retrying.
"""

import requests
import time
import sys
from typing import Dict, Any

# Configuration
API_ENDPOINT = "https://zyzss2dbwd.execute-api.us-east-1.amazonaws.com/prod/predict"
MAX_RETRIES = 3
INITIAL_BACKOFF = 5  # seconds

def call_api_with_retry(text: str, max_retries: int = MAX_RETRIES) -> Dict[str, Any]:
    """
    Call API with automatic retry on timeout.
    
    Args:
        text: Text to analyze
        max_retries: Number of retry attempts
        
    Returns:
        API response or error
    """
    backoff = INITIAL_BACKOFF
    
    for attempt in range(max_retries):
        try:
            print(f"\n Attempt {attempt + 1}/{max_retries}: Calling API...")
            response = requests.post(
                API_ENDPOINT,
                json={"text": text},
                timeout=35  # 35 seconds (just over API Gateway's 29s limit)
            )
            
            if response.status_code == 200:
                print(" Success!")
                return response.json()
            elif response.status_code == 504:
                # 504 means Gateway Timeout - model still loading on cold start
                print(f" 504 Gateway Timeout (model loading on cold start)")
                if attempt < max_retries - 1:
                    print(f"⏳ Waiting {backoff}s before retry...")
                    time.sleep(backoff)
                    backoff *= 1.5  # exponential backoff
                else:
                    print(" Max retries exceeded after timeout")
                    return None
            else:
                print(f" Error: {response.status_code}")
                print(response.text)
                return None
                
        except requests.exceptions.Timeout:
            print(f" Timeout (this is normal on first cold start)")
            if attempt < max_retries - 1:
                print(f"⏳ Waiting {backoff}s before retry (model is loading)...")
                time.sleep(backoff)
                backoff *= 1.5  # exponential backoff
            else:
                print(" Max retries exceeded")
                return None
                
        except Exception as e:
            print(f" Error: {str(e)}")
            return None
    
    return None

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "I hate this!"
    
    print(" Testing NLP Sentiment Analysis API")
    print(f" Text: {text}")
    
    result = call_api_with_retry(text)
    
    if result:
        print("\n Result:")
        print(f"  Sentiment: {result.get('sentiment', 'N/A')}")
        print(f"  Score: {result.get('score', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 'N/A')}")
    else:
        print("\n Failed to get response")
        sys.exit(1)
