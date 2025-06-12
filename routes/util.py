from flask import Blueprint, send_from_directory, request, jsonify
import re
import yfinance as yf
from transformers import pipeline
from datetime import datetime, timedelta
import requests
import os

util_bp = Blueprint('util', __name__)

# Load sentiment model once
sentiment_model = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')

# Simple mapping for company names to tickers
COMPANY_TICKERS = {
    'google': 'GOOGL',
    'apple': 'AAPL',
    'microsoft': 'MSFT',
    'amazon': 'AMZN',
    'meta': 'META',
    'tesla': 'TSLA',
    'nvidia': 'NVDA',
    'netflix': 'NFLX',
    'amd': 'AMD',
    'intel': 'INTC',
}

@util_bp.route('/')
def index():
    return send_from_directory('static', 'index.html')

@util_bp.route('/analyze_speech_request', methods=['POST'])
def analyze_speech_request():
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided.'}), 400
    text_lower = text.lower()
    company = None
    for name in COMPANY_TICKERS:
        if name in text_lower:
            company = name
            break
    # --- ML/NLP: Detect time range and statistic intent ---
    days_match = re.search(r'(?:past|last)\s*(\d+)\s*days', text_lower)
    week_match = re.search(r'(?:past|last)\s*week', text_lower)
    month_match = re.search(r'(?:past|last)\s*month', text_lower)
    avg_match = re.search(r'(average|mean)', text_lower)
    min_match = re.search(r'(minimum|min|lowest)', text_lower)
    max_match = re.search(r'(maximum|max|highest)', text_lower)
    # NEW: fallback for just 'X days'
    any_days_match = re.search(r'(\d+)\s*days', text_lower)
    # Detect if user wants a description (performance, trend, summary)
    describe_match = re.search(r'(performance|trend|summary|describe)', text_lower)
    # Default to 1 day (today)
    days = 1
    if days_match:
        days = int(days_match.group(1))
    elif week_match:
        days = 7
    elif month_match:
        days = 30
    elif any_days_match:
        days = int(any_days_match.group(1))
    # Only answer if company and 'price' or stat intent is present, or if describe intent
    if company and (describe_match or 'price' in text_lower or avg_match or min_match or max_match):
        ticker = COMPANY_TICKERS[company]
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            if not hist.empty:
                closes = hist['Close'].tolist()
                dates = [d.strftime('%Y-%m-%d') for d in hist.index]
                start_price = closes[0]
                end_price = closes[-1]
                min_price = min(closes)
                min_date = dates[closes.index(min_price)]
                max_price = max(closes)
                max_date = dates[closes.index(max_price)]
                avg_price = sum(closes) / len(closes)
                trend = 'up' if end_price > start_price else 'down' if end_price < start_price else 'flat'
                # If describe intent, use Hugging Face LLM
                model = data.get('model', 'meta-llama/Llama-2-7b-chat-hf')
                if describe_match:
                    prompt = f"User question: {text}\nStock data summary for {company.title()} ({ticker}), last {days} days:\n- Start price: ${start_price:.2f}\n- End price: ${end_price:.2f}\n- Min: ${min_price:.2f} on {min_date}\n- Max: ${max_price:.2f} on {max_date}\n- Average: ${avg_price:.2f}\n- Trend: {trend}\n\nPlease describe the stock's performance in natural language."
                    # Hugging Face API call
                    HF_API_URL = f"https://api-inference.huggingface.co/models/{model}"
                    HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
                    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
                    try:
                        resp = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
                        resp.raise_for_status()
                        data = resp.json()
                        if isinstance(data, list) and 'generated_text' in data[0]:
                            answer = data[0]['generated_text']
                        elif isinstance(data, dict) and 'generated_text' in data:
                            answer = data['generated_text']
                        else:
                            answer = "[LLM] Could not generate a description."
                    except Exception as e:
                        answer = f"[LLM] Error generating description: {str(e)}"
                elif avg_match:
                    answer = f"The average closing price of {company.title()} ({ticker}) over the past {days} days is ${avg_price:.2f}."
                elif min_match:
                    answer = f"The lowest closing price of {company.title()} ({ticker}) in the past {days} days was ${min_price:.2f} on {min_date}."
                elif max_match:
                    answer = f"The highest closing price of {company.title()} ({ticker}) in the past {days} days was ${max_price:.2f} on {max_date}."
                elif days > 1:
                    price_list = ', '.join([f"${c:.2f}" for c in closes])
                    answer = f"The closing prices of {company.title()} ({ticker}) for the past {days} days are: {price_list}."
                else:
                    answer = f"The price of {company.title()} ({ticker}) today is ${end_price:.2f}."
            else:
                answer = f"Sorry, I couldn't find the prices for {company.title()} in the past {days} days."
        except Exception as e:
            answer = f"Error fetching price for {company.title()}: {str(e)}"
    else:
        answer = "Sorry, I can only answer questions about the price, average, min, max, or performance of supported stocks right now."
    return jsonify({'answer': answer}) 