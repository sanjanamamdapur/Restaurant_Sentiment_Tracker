"""Shared VADER compound-score classification."""


def classify_sentiment(score):
    """Use VADER's documented inclusive positive/negative thresholds."""
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"
