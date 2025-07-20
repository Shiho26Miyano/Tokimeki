# NOTE: This module provides free AI chatbot functionality via OpenRouter API
from flask import Blueprint, request, jsonify
import requests
import os
import logging
from datetime import datetime, timedelta
import yfinance as yf
import time
import concurrent.futures

deepseek_chatbot_bp = Blueprint('deepseek_chatbot', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Free model configuration - Updated free models on OpenRouter
FREE_MODELS = {
    "mistral-small": "mistralai/mistral-small-3.2-24b-instruct:free",
    "deepseek-r1": "deepseek/deepseek-r1-0528:free",
    "deepseek-chat": "deepseek/deepseek-chat-v3-0324:free",
    "qwen3-8b": "qwen/qwen3-8b:free",
    "gemma-3n": "google/gemma-3n-e2b-it:free",
    "hunyuan": "tencent/hunyuan-a13b-instruct:free"
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

def calculate_performance_metrics(hist):
    """Calculate performance metrics from historical data"""
    if hist.empty or len(hist) < 2:
        return None
    
    # Calculate daily returns
    daily_returns = hist['Close'].pct_change().dropna()
    
    # Cumulative return
    cumulative_return = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
    
    # Sharpe Ratio (assuming risk-free rate of 0 for simplicity)
    if daily_returns.std() > 0:
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * (252 ** 0.5)  # Annualized
    else:
        sharpe_ratio = 0
    
    # Max Drawdown
    cumulative_returns = (1 + daily_returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min() * 100
    
    # Win rate and trade count (simplified - treating each day as a "trade")
    winning_days = (daily_returns > 0).sum()
    total_days = len(daily_returns)
    win_rate = (winning_days / total_days) * 100 if total_days > 0 else 0
    
    return {
        'cumulative_return': round(cumulative_return, 2),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'max_drawdown': round(max_drawdown, 2),
        'win_rate': round(win_rate, 1),
        'trade_count': total_days
    }

def get_stock_data(symbol, days=7):
    """Fetch comprehensive stock data using yfinance"""
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
        
        # Calculate additional metrics
        high_price = hist['High'].max()
        low_price = hist['Low'].min()
        avg_volume = hist['Volume'].mean()
        volatility = hist['Close'].pct_change().std() * 100
        
        # Calculate performance metrics
        performance_metrics = calculate_performance_metrics(hist)
        
        # Get daily data for the period
        daily_data = []
        for i, (date, row) in enumerate(hist.iterrows()):
            daily_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume']),
                'change': round(row['Close'] - hist['Close'].iloc[i-1] if i > 0 else 0, 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2)
            })
        
        # Get additional info
        info = ticker.info
        company_name = info.get('longName', symbol)
        sector = info.get('sector', 'Unknown')
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 0)
        
        return {
            'symbol': symbol,
            'company_name': company_name,
            'sector': sector,
            'current_price': round(current_price, 2),
            'start_price': round(start_price, 2),
            'price_change': round(price_change, 2),
            'price_change_pct': round(price_change_pct, 2),
            'high_price': round(high_price, 2),
            'low_price': round(low_price, 2),
            'avg_volume': int(avg_volume),
            'volatility': round(volatility, 2),
            'market_cap': market_cap,
            'pe_ratio': round(pe_ratio, 2) if pe_ratio else 0,
            'daily_data': daily_data,
            'period_days': days,
            'performance_metrics': performance_metrics
        }
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
        return None

def is_stock_query(message):
    """Enhanced stock query detection"""
    stock_keywords = ['stock', 'price', 'performance', 'trading', 'market', 'share', 'shares', 'ticker', 'quote']
    company_keywords = [
        'apple', 'aapl', 'microsoft', 'msft', 'google', 'googl', 'amazon', 'amzn', 
        'tesla', 'tsla', 'nvidia', 'nvda', 'meta', 'facebook', 'netflix', 'nflx',
        'amd', 'intel', 'oracle', 'salesforce', 'adobe', 'paypal', 'visa', 'mastercard',
        'coca-cola', 'pepsi', 'mcdonalds', 'starbucks', 'walmart', 'target', 'home depot',
        'disney', 'warner', 'sony', 'spotify', 'uber', 'lyft', 'airbnb', 'zoom'
    ]
    
    message_lower = message.lower()
    
    # Check for stock-related keywords
    has_stock_keyword = any(keyword in message_lower for keyword in stock_keywords)
    
    # Check for company names
    has_company = any(company in message_lower for company in company_keywords)
    
    # Check for time periods
    time_keywords = ['past', 'last', 'recent', 'week', 'month', 'year', 'days', 'performance', 'trend']
    has_time_period = any(keyword in message_lower for keyword in time_keywords)
    
    # Check for analysis keywords
    analysis_keywords = ['analyze', 'analysis', 'chart', 'graph', 'movement', 'volatility', 'trend']
    has_analysis = any(keyword in message_lower for keyword in analysis_keywords)
    
    return has_stock_keyword and (has_company or has_time_period or has_analysis)

def extract_stock_symbol(message):
    """Enhanced stock symbol extraction"""
    symbol_mapping = {
        'apple': 'AAPL', 'aapl': 'AAPL',
        'microsoft': 'MSFT', 'msft': 'MSFT',
        'google': 'GOOGL', 'googl': 'GOOGL',
        'amazon': 'AMZN', 'amzn': 'AMZN',
        'tesla': 'TSLA', 'tsla': 'TSLA',
        'nvidia': 'NVDA', 'nvda': 'NVDA',
        'meta': 'META', 'facebook': 'META',
        'netflix': 'NFLX', 'nflx': 'NFLX',
        'amd': 'AMD',
        'intel': 'INTC',
        'oracle': 'ORCL',
        'salesforce': 'CRM',
        'adobe': 'ADBE',
        'paypal': 'PYPL',
        'visa': 'V',
        'mastercard': 'MA',
        'coca-cola': 'KO',
        'pepsi': 'PEP',
        'mcdonalds': 'MCD',
        'starbucks': 'SBUX',
        'walmart': 'WMT',
        'target': 'TGT',
        'home depot': 'HD',
        'disney': 'DIS',
        'warner': 'WBD',
        'sony': 'SONY',
        'spotify': 'SPOT',
        'uber': 'UBER',
        'lyft': 'LYFT',
        'airbnb': 'ABNB',
        'zoom': 'ZM'
    }
    
    message_lower = message.lower()
    for company, symbol in symbol_mapping.items():
        if company in message_lower:
            return symbol
    return None

def create_stock_analysis_response(stock_data, message):
    """Create comprehensive stock analysis response"""
    if not stock_data:
        return "Sorry, I couldn't fetch stock data for that symbol. Please check the symbol and try again."
    
    # Get performance metrics
    metrics = stock_data.get('performance_metrics', {})
    
    # Create performance metrics explanation paragraph
    def get_performance_explanation(metrics):
        if not metrics:
            return ""
        
        cumulative_return = metrics.get('cumulative_return', 0)
        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        max_drawdown = metrics.get('max_drawdown', 0)
        win_rate = metrics.get('win_rate', 0)
        
        explanation = f"📊 **Performance Analysis:** "
        
        # Cumulative return assessment
        if cumulative_return > 5:
            explanation += f"The stock has shown strong performance with a {cumulative_return:.1f}% cumulative return. "
        elif cumulative_return > 0:
            explanation += f"The stock has generated a modest {cumulative_return:.1f}% return. "
        else:
            explanation += f"The stock has declined by {abs(cumulative_return):.1f}% during this period. "
        
        # Sharpe ratio assessment
        if sharpe_ratio > 1.0:
            explanation += f"The Sharpe ratio of {sharpe_ratio:.2f} indicates good risk-adjusted returns. "
        elif sharpe_ratio > 0:
            explanation += f"The Sharpe ratio of {sharpe_ratio:.2f} suggests moderate risk-adjusted performance. "
        else:
            explanation += f"The negative Sharpe ratio of {sharpe_ratio:.2f} indicates poor risk-adjusted returns. "
        
        # Max drawdown assessment
        if abs(max_drawdown) < 5:
            explanation += f"Risk management appears solid with a maximum drawdown of only {abs(max_drawdown):.1f}%. "
        elif abs(max_drawdown) < 10:
            explanation += f"The maximum drawdown of {abs(max_drawdown):.1f}% shows moderate volatility. "
        else:
            explanation += f"The significant maximum drawdown of {abs(max_drawdown):.1f}% indicates high volatility and risk. "
        
        # Win rate assessment
        if win_rate > 60:
            explanation += f"With a {win_rate:.0f}% win rate, the stock has been consistently positive. "
        elif win_rate > 50:
            explanation += f"The {win_rate:.0f}% win rate shows slightly more positive than negative days. "
        else:
            explanation += f"The {win_rate:.0f}% win rate indicates more negative than positive trading days. "
        
        return explanation
    
    # Determine analysis type based on message
    message_lower = message.lower()
    
    if 'price' in message_lower or 'current' in message_lower:
        return f"""📈 **{stock_data['company_name']} ({stock_data['symbol']}) - Current Stock Price**

💰 **Current Price:** ${stock_data['current_price']}
📊 **Price Change:** ${stock_data['price_change']} ({stock_data['price_change_pct']:+.2f}%)
📅 **Period:** Past {stock_data['period_days']} days

📈 **Price Range:**
• High: ${stock_data['high_price']}
• Low: ${stock_data['low_price']}
• Starting: ${stock_data['start_price']}

📊 **Market Data:**
• Sector: {stock_data['sector']}
• P/E Ratio: {stock_data['pe_ratio'] if stock_data['pe_ratio'] > 0 else 'N/A'}
• Volatility: {stock_data['volatility']:.2f}%
• Avg Volume: {stock_data['avg_volume']:,}

📊 **Performance Metrics:**
• Cumulative Return: {metrics.get('cumulative_return', 0):+.2f}%
• Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
• Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%
• Win Rate: {metrics.get('win_rate', 0):.1f}%
• Trade Count: {metrics.get('trade_count', 0)}

{get_performance_explanation(metrics)}

💡 **Analysis:** {stock_data['company_name']} has {'📈 increased' if stock_data['price_change'] >= 0 else '📉 decreased'} by {abs(stock_data['price_change_pct']):.1f}% over the past {stock_data['period_days']} days."""

    elif 'performance' in message_lower or 'trend' in message_lower:
        return_text = f"""📊 **{stock_data['company_name']} ({stock_data['symbol']}) - Performance Analysis**

📈 **Performance Summary:**
• Current Price: ${stock_data['current_price']}
• Change: ${stock_data['price_change']} ({stock_data['price_change_pct']:+.2f}%)
• Volatility: {stock_data['volatility']:.2f}%

📊 **Performance Metrics:**
• Cumulative Return: {metrics.get('cumulative_return', 0):+.2f}%
• Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
• Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%
• Win Rate: {metrics.get('win_rate', 0):.1f}%
• Trade Count: {metrics.get('trade_count', 0)}

{get_performance_explanation(metrics)}

📅 **Daily Performance:**
"""
        for day in stock_data['daily_data']:
            change_symbol = "📈" if day['change'] >= 0 else "📉"
            return_text += f"• {day['date']}: ${day['close']} ({change_symbol} {day['change']:+})\n"
        
        return_text += f"""
📊 **Market Metrics:**
• Sector: {stock_data['sector']}
• 52-Week High: ${stock_data['high_price']}
• 52-Week Low: ${stock_data['low_price']}
• Average Volume: {stock_data['avg_volume']:,}

💡 **Trend Analysis:** {stock_data['company_name']} shows {'an upward trend' if stock_data['price_change'] >= 0 else 'a downward trend'} with {stock_data['volatility']:.1f}% volatility over the past {stock_data['period_days']} days."""

    else:
        # Default comprehensive analysis
        return_text = f"""📈 **{stock_data['company_name']} ({stock_data['symbol']}) - Stock Analysis**

💰 **Current Status:**
• Price: ${stock_data['current_price']}
• Change: ${stock_data['price_change']} ({stock_data['price_change_pct']:+.2f}%)
• Period: Past {stock_data['period_days']} days

📊 **Key Metrics:**
• Sector: {stock_data['sector']}
• Market Cap: ${stock_data['market_cap']:,} (if available)
• P/E Ratio: {stock_data['pe_ratio'] if stock_data['pe_ratio'] > 0 else 'N/A'}
• Volatility: {stock_data['volatility']:.2f}%
• Average Volume: {stock_data['avg_volume']:,}

📊 **Performance Metrics:**
• Cumulative Return: {metrics.get('cumulative_return', 0):+.2f}%
• Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
• Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%
• Win Rate: {metrics.get('win_rate', 0):.1f}%
• Trade Count: {metrics.get('trade_count', 0)}

{get_performance_explanation(metrics)}

📅 **Price Range:**
• High: ${stock_data['high_price']}
• Low: ${stock_data['low_price']}
• Starting: ${stock_data['start_price']}

📈 **Daily Breakdown:**
"""
        for day in stock_data['daily_data']:
            change_symbol = "📈" if day['change'] >= 0 else "📉"
            return_text += f"• {day['date']}: ${day['close']} ({change_symbol} {day['change']:+})\n"
        
        return_text += f"""
💡 **Summary:** {stock_data['company_name']} has {'increased' if stock_data['price_change'] >= 0 else 'decreased'} by {abs(stock_data['price_change_pct']):.1f}% over the past {stock_data['period_days']} days with {stock_data['volatility']:.1f}% volatility.

🔍 **For detailed charts and longer time periods, use the "Market Overtime" tab in this application!**"""

    return return_text

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
            logger.info(f"API response for {model}: {data}")
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                logger.info(f"Extracted content for {model}: {content[:200]}...")
                
                return {
                    "success": True,
                    "response": content,
                    "model": model,
                    "usage": data.get("usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
            elif "response" in data:
                # Fallback for different API response formats
                content = data["response"]
                logger.info(f"Fallback extracted content for {model}: {content[:200]}...")
                
                return {
                    "success": True,
                    "response": content,
                    "model": model,
                    "usage": data.get("usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Invalid response format for {model}: {data}")
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

def test_single_model(model, prompt, temperature=0.7, max_tokens=1000):
    """Test a single model and return performance metrics"""
    start_time = time.time()
    
    messages = [{"role": "user", "content": prompt}]
    result = call_free_api(messages, model, temperature, max_tokens)
    
    end_time = time.time()
    response_time = end_time - start_time
    
    if "error" in result:
        return {
            "model": model,
            "success": False,
            "error": result["error"],
            "response_time": response_time,
            "response": None,
            "token_count": 0,
            "word_count": 0,
            "avg_word_length": 0
        }
    
    # Check if we have a successful response
    if not result.get("success", False) or "response" not in result:
        return {
            "model": model,
            "success": False,
            "error": "No valid response received",
            "response_time": response_time,
            "response": None,
            "token_count": 0,
            "word_count": 0,
            "avg_word_length": 0
        }
    
    # Calculate response quality metrics
    response_text = result["response"]
    
    # Debug logging
    logger.info(f"Model {model} response: {response_text[:200]}...")
    logger.info(f"Response type: {type(response_text)}, Length: {len(response_text) if response_text else 0}")
    
    # Handle empty or None response
    if not response_text or response_text.strip() == "":
        return {
            "model": model,
            "success": False,
            "error": "Empty response received",
            "response_time": response_time,
            "response": None,
            "token_count": 0,
            "word_count": 0,
            "avg_word_length": 0
        }
    
    token_count = result.get("usage", {}).get("completion_tokens", len(response_text.split()))
    
    # Simple quality metrics
    word_count = len(response_text.split())
    avg_word_length = sum(len(word) for word in response_text.split()) / max(word_count, 1)
    
    return {
        "model": model,
        "success": True,
        "response_time": response_time,
        "response": response_text,
        "token_count": token_count,
        "word_count": word_count,
        "avg_word_length": avg_word_length,
        "usage": result.get("usage", {})
    }

@deepseek_chatbot_bp.route('/compare_models', methods=['POST'])
def compare_models():
    """Compare performance of multiple models"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        # Get optional parameters
        models_to_test = data.get('models', list(FREE_MODELS.keys()))
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 1000))
        
        # Validate parameters
        if not all(model in FREE_MODELS for model in models_to_test):
            return jsonify({"error": "Invalid model specified"}), 400
        if not 0 <= temperature <= 2:
            return jsonify({"error": "Temperature must be between 0 and 2"}), 400
        if not 1 <= max_tokens <= 4000:
            return jsonify({"error": "Max tokens must be between 1 and 4000"}), 400
        
        # Test all models concurrently
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_model = {
                executor.submit(test_single_model, model, prompt, temperature, max_tokens): model 
                for model in models_to_test
            }
            
            for future in concurrent.futures.as_completed(future_to_model):
                result = future.result()
                results.append(result)
        
        # Sort results by response time
        results.sort(key=lambda x: x.get('response_time', float('inf')))
        
        # Calculate summary statistics
        successful_results = [r for r in results if r['success']]
        avg_response_time = sum(r['response_time'] for r in successful_results) / len(successful_results) if successful_results else 0
        avg_token_count = sum(r['token_count'] for r in successful_results) / len(successful_results) if successful_results else 0
        
        return jsonify({
            "success": True,
            "prompt": prompt,
            "results": results,
            "summary": {
                "total_models": len(results),
                "successful_models": len(successful_results),
                "avg_response_time": avg_response_time,
                "avg_token_count": avg_token_count,
                "fastest_model": results[0]['model'] if results else None,
                "slowest_model": results[-1]['model'] if results else None
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter value: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in compare_models endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@deepseek_chatbot_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API configuration"""
    return jsonify({
        "api_configured": validate_api_key(),
        "timestamp": datetime.now().isoformat()
    })

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
        system_message = """You are an advanced AI assistant with comprehensive stock market analysis capabilities. You can:

1. **Stock Analysis**: Provide detailed stock price analysis, performance metrics, and market insights
2. **Real-time Data**: Access current stock prices, price changes, volatility, and trading volume
3. **Company Information**: Provide sector analysis, P/E ratios, market cap, and other financial metrics
4. **Technical Analysis**: Analyze price trends, support/resistance levels, and market patterns
5. **Performance Metrics**: Calculate and explain key performance indicators including:
   - Cumulative Return: Total percentage gain/loss over the period
   - Sharpe Ratio: Risk-adjusted return measure (higher is better)
   - Max Drawdown: Largest peak-to-trough decline percentage
   - Win Rate: Percentage of positive trading days
   - Trade Count: Number of trading days analyzed
6. **General Assistance**: Help with coding, mathematics, analysis, and other questions

When users ask about stocks, you can provide:
- Current stock prices and price changes
- Performance analysis over different time periods
- Volatility and risk metrics
- Sector and market analysis
- Trading volume and market activity
- Technical indicators and trends
- Comprehensive performance metrics for risk assessment

When presenting performance metrics, always include a clear explanation paragraph that interprets what the metrics mean for the stock's performance and risk profile. Explain whether the metrics indicate good or poor performance relative to typical market standards.

Always be respectful, accurate, and provide detailed, actionable information. For complex stock analysis, you can fetch real-time data and provide comprehensive insights including performance metrics."""
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
                    stock_response = create_stock_analysis_response(stock_data, message)
                    
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

@deepseek_chatbot_bp.route('/stock_symbols', methods=['GET'])
def get_stock_symbols():
    """Get available stock symbols for analysis"""
    symbols = {
        "Technology": {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc. (Google)",
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc.",
            "NVDA": "NVIDIA Corporation",
            "META": "Meta Platforms Inc.",
            "NFLX": "Netflix Inc.",
            "AMD": "Advanced Micro Devices",
            "INTC": "Intel Corporation",
            "ORCL": "Oracle Corporation",
            "CRM": "Salesforce Inc.",
            "ADBE": "Adobe Inc.",
            "PYPL": "PayPal Holdings",
            "ZM": "Zoom Video Communications"
        },
        "Finance": {
            "V": "Visa Inc.",
            "MA": "Mastercard Inc.",
            "JPM": "JPMorgan Chase & Co.",
            "BAC": "Bank of America Corp.",
            "WFC": "Wells Fargo & Company"
        },
        "Consumer": {
            "KO": "The Coca-Cola Company",
            "PEP": "PepsiCo Inc.",
            "MCD": "McDonald's Corporation",
            "SBUX": "Starbucks Corporation",
            "WMT": "Walmart Inc.",
            "TGT": "Target Corporation",
            "HD": "The Home Depot Inc."
        },
        "Entertainment": {
            "DIS": "The Walt Disney Company",
            "WBD": "Warner Bros. Discovery",
            "SONY": "Sony Group Corporation",
            "SPOT": "Spotify Technology"
        },
        "Transportation": {
            "UBER": "Uber Technologies Inc.",
            "LYFT": "Lyft Inc.",
            "ABNB": "Airbnb Inc."
        }
    }
    
    return jsonify({
        "available_symbols": symbols,
        "total_symbols": sum(len(category) for category in symbols.values()),
        "categories": list(symbols.keys())
    })

@deepseek_chatbot_bp.route('/models', methods=['GET'])
def get_models():
    """Get available free models"""
    return jsonify({
        "models": FREE_MODELS,
        "default_model": "mistral-small",
        "api_configured": validate_api_key()
    })

@deepseek_chatbot_bp.route('/debug-qwen', methods=['POST'])
def debug_qwen():
    """Debug endpoint to test Qwen3 8B specifically"""
    try:
        messages = [{"role": "user", "content": "Hello, please respond with a simple test message."}]
        result = call_free_api(messages, "qwen3-8b", 0.7, 100)
        
        return jsonify({
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

 