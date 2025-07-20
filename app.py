from flask import Flask, send_from_directory, jsonify, request, render_template
from flask_cors import CORS
import os
import numpy as np
import logging
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
app.register_blueprint(deepseek_chatbot_bp)
from routes.ai_platform_comparison import ai_platform_comparison_bp
app.register_blueprint(ai_platform_comparison_bp)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

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

# Monitoring endpoints
@app.route('/api/usage-stats')
def get_usage_stats():
    """Get usage statistics"""
    try:
        stats = usage_tracker.get_usage_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cache-status')
def get_cache_status():
    """Get cache status"""
    try:
        redis_connected = cache_manager.redis_client is not None and cache_manager.cache_enabled
        test_passed = False
        
        if redis_connected:
            try:
                cache_manager.redis_client.ping()
                test_passed = True
            except:
                test_passed = False
        
        return jsonify({
            "redis_connected": redis_connected,
            "test_passed": test_passed,
            "cache_ttl": cache_manager.default_ttl,
            "cache_enabled": cache_manager.cache_enabled
        })
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-redis')
def test_redis():
    """Test Redis connection"""
    try:
        if not cache_manager.redis_client:
            return jsonify({"success": False, "error": "Redis client not initialized"})
        
        cache_manager.redis_client.ping()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Redis test failed: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/cache-clear', methods=['POST'])
def clear_cache():
    """Clear all cache"""
    try:
        success = cache_manager.clear_all()
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/reset-stats', methods=['POST'])
def reset_stats():
    """Reset usage statistics"""
    try:
        usage_tracker.reset_stats()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error resetting stats: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.errorhandler(500)
def handle_500(e):
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Resource not found"}), 404

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
    