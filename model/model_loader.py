"""
Shared model loading and inference logic for both Lambda and Kubernetes deployments.
"""
from typing import Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# Set Hugging Face cache directory to Lambda's writable /tmp
os.environ['TRANSFORMERS_CACHE'] = '/tmp/transformers_cache'
os.environ['HF_HOME'] = '/tmp/hf_cache'

try:
    # Try relative import first (for package imports)
    from .logger_config import get_logger
except ImportError:
    # Fall back to absolute import (for direct execution)
    from logger_config import get_logger

logger = get_logger("model_loader")

# Global variables to cache model and tokenizer
_model = None
_tokenizer = None
_device = None


def get_device():
    """Get the appropriate device (CPU or GPU if available)."""
    global _device
    if _device is None:
        # AWS Lambda doesn't support MPS, always use CPU there
        # For local development, use MPS on macOS if available
        try:
            if torch.cuda.is_available():
                _device = "cuda"
            elif torch.backends.mps.is_available() and not torch.backends.mps.is_built():
                # MPS available but not properly built - fall back to CPU
                _device = "cpu"
            elif torch.backends.mps.is_available():
                _device = "mps"
            else:
                _device = "cpu"
        except Exception:
            # If anything goes wrong, default to CPU (safest for Lambda)
            _device = "cpu"
        logger.info(f"Using device: {_device}")
    return _device


def load_model(model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
    """
    Load the DistilBERT model and tokenizer.
    
    Args:
        model_name: Hugging Face model identifier
        
    Returns:
        tuple: (model, tokenizer)
    """
    global _model, _tokenizer
    
    if _model is None or _tokenizer is None:
        logger.info(f"Loading model: {model_name}")
        try:
            _tokenizer = AutoTokenizer.from_pretrained(model_name)
            _model = AutoModelForSequenceClassification.from_pretrained(model_name)
            _model.eval()  # Set to evaluation mode
            
            device = get_device()
            _model = _model.to(device)
            
            logger.info(f"Model loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    return _model, _tokenizer


def predict_sentiment(text: str) -> Dict[str, Any]:
    """
    Predict sentiment for a given text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        dict: Prediction results with label and confidence score
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    # Load model if not already loaded
    model, tokenizer = load_model()
    
    try:
        # Tokenize input
        inputs = tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors="pt"
        )
        
        # Move inputs to device
        device = get_device()
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Run inference
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # Get results
        # scores = predictions[0].cpu().numpy()

        # FIXME: this below is the fix for MAC
        predictions_cpu = predictions.cpu()
        scores = predictions_cpu[0].detach().numpy() 
        
        label_id = scores.argmax()
        confidence = float(scores[label_id])
        
        # Map label ID to sentiment
        labels = ["NEGATIVE", "POSITIVE"]
        label = labels[label_id]
        
        result = {
            "text": text,
            "sentiment": label,
            "confidence": confidence,
            "scores": {
                "negative": float(scores[0]),
                "positive": float(scores[1])
            }
        }
        
        logger.info(f"Prediction: {label} (confidence: {confidence:.4f})")
        return result
        
    except Exception as e:
        logger.error(f"Error during inference: {str(e)}")
        raise