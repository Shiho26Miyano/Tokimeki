from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import numpy as np

app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})

# Import and register blueprints
from routes.stock import stock_bp
app.register_blueprint(stock_bp)
from routes.util import util_bp
app.register_blueprint(util_bp)
from routes.tweet import tweet_bp
app.register_blueprint(tweet_bp)
from routes.hf_tweeteval import hf_tweeteval_bp
app.register_blueprint(hf_tweeteval_bp)
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port) 