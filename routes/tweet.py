from flask import Blueprint, request, jsonify
import os
import requests
import re
import yfinance as yf
import numpy as np
import pandas as pd

# Optional imports - app will work without these
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available")

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available")

# Define the blueprint
tweet_bp = Blueprint('tweet', __name__)

# Load sentiment model only if transformers is available
if TRANSFORMERS_AVAILABLE:
    try:
        sentiment_model = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
    except Exception as e:
        print(f"Warning: Could not load sentiment model: {e}")
        sentiment_model = None
else:
    sentiment_model = None

def fetch_tweets(query, max_results=100):
    bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    params = {
        "query": query,
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics"
    }
    response = requests.get(url, headers=headers, params=params)
    print("Twitter API status:", response.status_code)
    print("Twitter API response:", response.text)
    if response.status_code == 429:
        return 'RATE_LIMIT'
    tweets = []
    if response.status_code == 200:
        for tweet in response.json().get("data", []):
            tweets.append({
                "text": tweet["text"],
                "date": tweet["created_at"][:10],
                "retweets": tweet["public_metrics"]["retweet_count"]
            })
    return tweets

def clean_tweet(text):
    text = re.sub(r"http\\S+", "", text)
    text = re.sub(r"@\\w+", "", text)
    text = re.sub(r"#", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.lower().strip()

# Note: Tweet analysis routes are not currently used by the frontend
# Keeping the blueprint for potential future use

# @tweet_bp.route('/tweet_volatility_analysis', methods=['GET'])
# def tweet_volatility_analysis():
#     # This route is not used by the frontend
#     pass

# @tweet_bp.route('/tweet_sentiment', methods=['GET'])
# def tweet_sentiment():
#     # This route is not used by the frontend
#     pass 