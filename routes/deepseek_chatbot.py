# NOTE: This module provides free AI chatbot functionality via OpenRouter API
from flask import Blueprint, request, jsonify
import requests
import os
import logging
from datetime import datetime, timedelta
import yfinance as yf

deepseek_chatbot_bp = Blueprint('deepseek_chatbot', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Free model configuration - Top 5 free models on OpenRouter
FREE_MODELS = {
    "mistral-small": "mistralai/mistral-small-3.2-24b-instruct:free",
    "deepseek-r1": "deepseek/deepseek-r1-0528:free", 
    "qwen3-8b": "qwen/qwen3-8b:free",
    "gemma-3n": "google/gemma-3n-e2b-it:free",
    "kimi-k2": "moonshotai/kimi-k2:free"
}

def validate_api_key():
    """Validate that OpenRouter API key is available"""
    if not OPENROUTER_API_KEY:
        logger.error("OpenRouter API key not found in environment variables")
        return False
    return True

def format_chat_message(role, content):
    """Format a chat message for the API"""
    return {
        "role": role,
        "content": content
    }

def get_stock_data(symbol, days=7):
    """Fetch stock data using yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            return None
            
        # Get current price and basic info
        current_price = hist['Close'].iloc[-1]
        start_price = hist['Close'].iloc[0]
        price_change = current_price - start_price
        price_change_pct = (price_change / start_price) * 100
        
        # Get daily data for the period
        daily_data = []
        for i, (date, row) in enumerate(hist.iterrows()):
            daily_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume']),
                'change': round(row['Close'] - hist['Close'].iloc[i-1] if i > 0 else 0, 2)
            })
        
        # Get additional info
        info = ticker.info
        company_name = info.get('longName', symbol)
        
        return {
            'symbol': symbol,
            'company_name': company_name,
            'current_price': round(current_price, 2),
            'start_price': round(start_price, 2),
            'price_change': round(price_change, 2),
            'price_change_pct': round(price_change_pct, 2),
            'daily_data': daily_data,
            'period_days': days
        }
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
        return None

def is_stock_query(message):
    """Check if the message is asking about stock performance"""
    stock_keywords = ['stock', 'price', 'performance', 'trading', 'market', 'share', 'shares']
    company_keywords = ['apple', 'aapl', 'microsoft', 'msft', 'google', 'googl', 'amazon', 'amzn', 
                       'tesla', 'tsla', 'nvidia', 'nvda', 'meta', 'facebook', 'netflix', 'nflx']
    
    message_lower = message.lower()
    
    # Check for stock-related keywords
    has_stock_keyword = any(keyword in message_lower for keyword in stock_keywords)
    
    # Check for company names
    has_company = any(company in message_lower for company in company_keywords)
    
    # Check for time periods
    time_keywords = ['past', 'last', 'recent', 'week', 'month', 'year', 'days', 'performance']
    has_time_period = any(keyword in message_lower for keyword in time_keywords)
    
    return has_stock_keyword and (has_company or has_time_period)

def extract_stock_symbol(message):
    """Extract stock symbol from message"""
    symbol_mapping = {
        'apple': 'AAPL',
        'aapl': 'AAPL',
        'microsoft': 'MSFT',
        'msft': 'MSFT',
        'google': 'GOOGL',
        'googl': 'GOOGL',
        'amazon': 'AMZN',
        'amzn': 'AMZN',
        'tesla': 'TSLA',
        'tsla': 'TSLA',
        'nvidia': 'NVDA',
        'nvda': 'NVDA',
        'meta': 'META',
        'facebook': 'META',
        'netflix': 'NFLX',
        'nflx': 'NFLX'
    }
    
    message_lower = message.lower()
    for company, symbol in symbol_mapping.items():
        if company in message_lower:
            return symbol
    return None

def call_free_api(messages, model="mistral-small", temperature=0.7, max_tokens=1000):
    """Call the free AI API via OpenRouter"""
    if not validate_api_key():
        return {"error": "OpenRouter API key not configured"}
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://tokimeki-pro.up.railway.app",
            "X-Title": "Tokimeki Free AI Chatbot"
        }
        
        payload = {
            "model": FREE_MODELS.get(model, FREE_MODELS["mistral-small"]),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        logger.info(f"Calling free AI API with model: {model}")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return {
                    "success": True,
                    "response": data["choices"][0]["message"]["content"],
                    "model": model,
                    "usage": data.get("usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": "Invalid response format from API"}
        else:
            error_msg = f"API request failed with status {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg = error_data["error"].get("message", error_msg)
            except:
                pass
            return {"error": error_msg}
            
    except requests.exceptions.Timeout:
        return {"error": "Request timed out"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

@deepseek_chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get('message', '').strip()
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Get optional parameters
        model = data.get('model', 'mistral-small')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 1000))
        conversation_history = data.get('history', [])
        
        # Validate parameters
        if model not in FREE_MODELS:
            return jsonify({"error": "Invalid model specified"}), 400
        if not 0 <= temperature <= 2:
            return jsonify({"error": "Temperature must be between 0 and 2"}), 400
        if not 1 <= max_tokens <= 4000:
            return jsonify({"error": "Max tokens must be between 1 and 4000"}), 400
        
        # Build conversation messages
        messages = []
        
        # Add system message for context
        system_message = """You are an advanced AI assistant. You are helpful, accurate, and provide detailed responses. 
        You can help with coding, mathematics, analysis, and general questions. Always be respectful and provide accurate information."""
        messages.append(format_chat_message("system", system_message))
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Limit to last 10 messages
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                messages.append(format_chat_message(msg['role'], msg['content']))
        
        # Check if this is a stock query and handle it specially
        if is_stock_query(message):
            symbol = extract_stock_symbol(message)
            if symbol:
                # Fetch real stock data
                stock_data = get_stock_data(symbol, days=7)
                if stock_data:
                    # Create a detailed response with real data
                    stock_response = f"""📈 **{stock_data['company_name']} ({stock_data['symbol']}) Stock Performance - Past 7 Days**

**Current Price:** ${stock_data['current_price']}
**Price Change:** ${stock_data['price_change']} ({stock_data['price_change_pct']}%)
**Starting Price (7 days ago):** ${stock_data['start_price']}

**Daily Breakdown:**
"""
                    for day in stock_data['daily_data']:
                        change_symbol = "📈" if day['change'] >= 0 else "📉"
                        stock_response += f"• {day['date']}: ${day['close']} ({change_symbol} {day['change']:+})\n"
                    
                    stock_response += f"""

**Summary:** {stock_data['company_name']} has {'increased' if stock_data['price_change'] >= 0 else 'decreased'} by {abs(stock_data['price_change_pct']):.1f}% over the past 7 days.

💡 **Tip:** For more detailed analysis, charts, and longer time periods, use the "Market Overtime" tab in this application!"""
                    
                    return jsonify({
                        "success": True,
                        "response": stock_response,
                        "model": model,
                        "usage": {"stock_data": True},
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Add current user message
        messages.append(format_chat_message("user", message))
        
        # Call the API
        result = call_free_api(messages, model, temperature, max_tokens)
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter value: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@deepseek_chatbot_bp.route('/models', methods=['GET'])
def get_models():
    """Get available free models"""
    return jsonify({
        "models": FREE_MODELS,
        "default_model": "mistral-small",
        "api_configured": validate_api_key()
    })

@deepseek_chatbot_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "api_configured": validate_api_key(),
        "timestamp": datetime.now().isoformat()
    }) 