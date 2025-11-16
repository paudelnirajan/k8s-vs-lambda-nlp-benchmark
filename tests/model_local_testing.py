"""
Test script to verify model works locally.
"""
from model.model_loader import predict_sentiment, load_model

def test_model():
    """Test model with sample texts."""
    print("Loading model...")
    load_model()
    print("Model loaded sucessfully!\n")

    # Test cases
    test_texts = [
        "I love this product! It's amazing!",
        "This is terrible. I hate it.",
        "The weather is okay today.",
        "This movie was absolutely fantastic and I would watch it again!",
        "I'm not sure how I feel about this."
    ]

    print("Running predictions...\n")
    for text in test_texts:
        print(f"Text: {text}")
        result = predict_sentiment(text)
        print(f"Sentiment: {result['sentiment']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Scores - Negative: {result['scores']['negative']:.4f}, Positive: {result['scores']['positive']:.4f}")
        print("-" * 60)

if __name__ == "__main__":
    test_model()