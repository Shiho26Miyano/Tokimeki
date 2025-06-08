from flask import Blueprint, send_from_directory

util_bp = Blueprint('util', __name__)

@util_bp.route('/')
def index():
    return send_from_directory('static', 'index.html') 