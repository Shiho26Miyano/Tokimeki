from flask import Blueprint, request, jsonify
import uuid

pay_bp = Blueprint('pay', __name__)

@pay_bp.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    amount = data.get('amount')
    method = data.get('method')
    if method == 'mock':
        return jsonify({
            'status': 'success',
            'txn_id': str(uuid.uuid4()),
            'amount': amount,
            'method': method
        })
    else:
        return jsonify({'status': 'error', 'error': 'Only mock payments are supported in demo.'}), 400 