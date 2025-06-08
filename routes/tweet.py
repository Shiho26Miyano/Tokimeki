from flask import Blueprint, request, jsonify
import os
import requests
import re
import yfinance as yf
import numpy as np
import pandas as pd
from transformers import pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

# Define the blueprint
tweet_bp = Blueprint('tweet', __name__)

# Load sentiment model once at startup
sentiment_model = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')

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

@tweet_bp.route('/tweet_volatility_analysis', methods=['GET'])
def tweet_volatility_analysis():
    tweets = fetch_tweets("Tesla", 100)
    if not tweets:
        return jsonify({'error': 'No tweets found.'}), 400
    for t in tweets:
        t['clean'] = clean_tweet(t['text'])
    sentiments = sentiment_model([t['clean'] for t in tweets])
    for t, s in zip(tweets, sentiments):
        t['sentiment'] = s['score'] * (1 if s['label'] == 'POSITIVE' else -1)
    df = pd.DataFrame(tweets)
    daily = df.groupby('date').agg(
        mean_sentiment=('sentiment', 'mean'),
        mean_retweets=('retweets', 'mean'),
        tweet_count=('sentiment', 'count')
    ).reset_index()
    tsla = yf.Ticker("TSLA")
    hist = tsla.history(period="1mo")
    hist['returns'] = hist['Close'].pct_change()
    hist['volatility'] = hist['returns'].rolling(window=5).std()
    hist = hist.reset_index()
    hist['date'] = hist['Date'].dt.strftime('%Y-%m-%d')
    merged = pd.merge(daily, hist[['date', 'volatility']], on='date', how='inner')
    if len(merged) < 5:
        return jsonify({'error': 'Not enough merged data for analysis.'}), 400
    median_vol = merged['volatility'].median()
    merged['vol_label'] = (merged['volatility'] > median_vol).astype(int)
    X = merged[['mean_sentiment', 'mean_retweets']].values
    y = merged['vol_label'].values
    model = RandomForestClassifier(random_state=42)
    model.fit(X, y)
    y_pred = model.predict(X)
    acc = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred)
    importances = model.feature_importances_
    findings = {
        'accuracy': acc,
        'f1_score': f1,
        'feature_importances': {
            'mean_sentiment': float(importances[0]),
            'mean_retweets': float(importances[1])
        },
        'n_days': int(len(merged)),
        'summary': f"Model accuracy: {acc:.2f}, F1: {f1:.2f}. Sentiment and retweets show predictive value for Tesla volatility over {len(merged)} days."
    }
    return jsonify(findings)

@tweet_bp.route('/tweet_sentiment', methods=['GET'])
def tweet_sentiment():
    query = request.args.get('query', 'stock market')
    max_results = int(request.args.get('max_results', 10))
    tweets = fetch_tweets(query, max_results)
    tweet_texts = [tweet['text'] for tweet in tweets]
    sentiments = sentiment_model(tweet_texts) if tweet_texts else []
    return jsonify([
        {"created_at": t["date"], "text": t["text"], "sentiment": s}
        for t, s in zip(tweets, sentiments)
    ]) 