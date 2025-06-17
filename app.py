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
from routes.stock import stock_bp
app.register_blueprint(stock_bp)
from routes.util import util_bp
app.register_blueprint(util_bp)
from routes.tweet import tweet_bp
app.register_blueprint(tweet_bp)
from routes.hf_tweeteval import hf_tweeteval_bp
app.register_blueprint(hf_tweeteval_bp)
from routes.hf_signal_tool import hf_signal_bp
app.register_blueprint(hf_signal_bp)
from routes.pay import pay_bp
app.register_blueprint(pay_bp)

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
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port) 