from flask import Flask, send_from_directory, jsonify, request, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import numpy as np
import logging
import time

# Import our utilities
from utils.cache_manager import cache_manager
from utils.usage_tracker import usage_tracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "supports_credentials": True
}})

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Import and register blueprints
from routes.stock_data_provider import stock_bp as stock_data_provider_bp
app.register_blueprint(stock_data_provider_bp)
from routes.speech_analysis import speech_analysis_bp
app.register_blueprint(speech_analysis_bp)
from routes.tweet_sentiment_analyzer import hf_tweeteval_bp as tweet_sentiment_analyzer_bp
app.register_blueprint(tweet_sentiment_analyzer_bp)
from routes.trading_strategy_analyzer import hf_signal_bp as trading_strategy_analyzer_bp
app.register_blueprint(trading_strategy_analyzer_bp)
from routes.investment_playbooks import investment_playbooks_bp
app.register_blueprint(investment_playbooks_bp)
from routes.deepseek_chatbot import deepseek_chatbot_bp
# Set the limiter in the deepseek_chatbot module
import routes.deepseek_chatbot
routes.deepseek_chatbot.limiter = limiter
app.register_blueprint(deepseek_chatbot_bp)
from routes.ai_platform_comparison import ai_platform_comparison_bp
app.register_blueprint(ai_platform_comparison_bp)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    
    # Track request usage
    if request.endpoint and not request.endpoint.startswith('static'):
        start_time = getattr(request, '_start_time', time.time())
        response_time = time.time() - start_time
        
        # Extract model from request if available
        model = None
        if request.is_json:
            data = request.get_json()
            model = data.get('model') if data else None
        
        usage_tracker.track_request(
            endpoint=request.endpoint,
            model=model,
            response_time=response_time,
            success=response.status_code < 400
        )
    
    return response

@app.before_request
def before_request():
    request._start_time = time.time()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/monitoring')
def monitoring():
    """Monitoring dashboard page"""
    return render_template('monitoring.html')

@app.route('/test')
def test():
    return 'Hello, world!'



@app.errorhandler(500)
def handle_500(e):
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Resource not found"}), 404

# Monitoring and management endpoints
@app.route('/api/usage-stats')
@limiter.limit("10 per minute")
def get_usage_stats():
    """Get current usage statistics"""
    period = request.args.get('period', 'today')
    stats = usage_tracker.get_usage_stats(period)
    return jsonify(stats)

@app.route('/api/usage-limits')
@limiter.limit("10 per minute")
def get_usage_limits():
    """Check if usage limits are exceeded"""
    limits = usage_tracker.check_limits()
    return jsonify(limits)

@app.route('/api/cache-status')
@limiter.limit("10 per minute")
def get_cache_status():
    """Get cache status and statistics"""
    # Test Redis connection
    redis_test = False
    if cache_manager.redis_client:
        try:
            cache_manager.redis_client.ping()
            redis_test = True
        except Exception as e:
            redis_test = False
    
    return jsonify({
        "cache_enabled": cache_manager.cache_enabled,
        "redis_connected": cache_manager.redis_client is not None,
        "redis_test": redis_test,
        "default_ttl": cache_manager.default_ttl,
        "redis_url": os.environ.get('REDIS_URL', 'Not set')
    })

@app.route('/api/cache-clear', methods=['POST'])
@limiter.limit("5 per hour")
def clear_cache():
    """Clear all cached data"""
    success = cache_manager.clear_all()
    return jsonify({
        "success": success,
        "message": "Cache cleared successfully" if success else "Failed to clear cache"
    })

@app.route('/api/reset-stats', methods=['POST'])
@limiter.limit("5 per hour")
def reset_usage_stats():
    """Reset usage statistics"""
    usage_tracker.reset_stats()
    return jsonify({
        "success": True,
        "message": "Usage statistics reset successfully"
    })

@app.route('/api/test-redis')
@limiter.limit("5 per minute")
def test_redis():
    """Test Redis connection and basic operations"""
    try:
        if not cache_manager.redis_client:
            return jsonify({
                "success": False,
                "error": "Redis client not initialized",
                "cache_enabled": cache_manager.cache_enabled
            }), 500
        
        # Test basic Redis operations
        test_key = "test_connection"
        test_value = {"timestamp": time.time(), "message": "Redis test"}
        
        # Set a test value
        cache_manager.redis_client.setex(test_key, 60, str(test_value))
        
        # Get the test value
        retrieved = cache_manager.redis_client.get(test_key)
        
        # Delete the test value
        cache_manager.redis_client.delete(test_key)
        
        return jsonify({
            "success": True,
            "message": "Redis connection and operations working",
            "test_key": test_key,
            "test_value": test_value,
            "retrieved": retrieved,
            "timestamp": time.time()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "cache_enabled": cache_manager.cache_enabled
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    # For local development with HTTPS (needed for microphone access)
    if debug and os.environ.get('USE_HTTPS') == 'true':
        import ssl
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain('cert.pem', 'key.pem')
        app.run(debug=debug, host='0.0.0.0', port=port, ssl_context=context)
    else:
        app.run(debug=debug, host='0.0.0.0', port=port) 
    