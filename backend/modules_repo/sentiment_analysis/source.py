# ai_platform/modules_repo/sentiment_analysis/source.py

from textblob import TextBlob

class SentimentAnalyzer:
    def __init__(self):
        pass

    def run(self, text: str) -> dict:
        """
        Analyzes the sentiment of the input text.
        """
        blob = TextBlob(text)
        return {
            "polarity": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity,
            "assessment": "Positive" if blob.sentiment.polarity > 0 else "Negative"
        }