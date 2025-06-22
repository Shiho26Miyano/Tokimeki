from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os
import numpy as np
import logging

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

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

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
    