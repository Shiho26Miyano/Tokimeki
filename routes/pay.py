from flask import Blueprint, request, jsonify
import uuid
import random
import numpy as np
from sklearn.cluster import KMeans

pay_bp = Blueprint('pay', __name__)

# Demo offers
OFFERS = [
    {"title": "10% off your next purchase!", "desc": "Use code NEXT10 at checkout."},
    {"title": "Upgrade to Premium", "desc": "Get exclusive features for just $5 more."},
    {"title": "Refer a Friend", "desc": "Earn $5 credit for every friend who joins."},
    {"title": "Bundle Deal", "desc": "Add another item for only $2 extra!"}
]

# In-memory payment history for stats and ML
global PAYMENT_HISTORY
PAYMENT_HISTORY = []

@pay_bp.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    amount = float(data.get('amount', 0))
    method = data.get('method')
    # Add to history
    PAYMENT_HISTORY.append({'amount': amount, 'method': method})
    # --- Anomaly detection: flag if amount > mean + 2*std ---
    amounts = [p['amount'] for p in PAYMENT_HISTORY]
    mean = np.mean(amounts)
    std = np.std(amounts) if len(amounts) > 1 else 0
    is_anomaly = amount > mean + 2*std if len(amounts) > 1 else False
    # --- ML-based offer recommendation using clustering ---
    offer = None
    if len(amounts) >= 3:
        # Use KMeans to cluster payment amounts into 3 groups
        X = np.array(amounts).reshape(-1, 1)
        kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
        clusters = kmeans.fit_predict(X)
        user_cluster = clusters[-1]
        # Map clusters to offers (e.g., high spenders get premium, low get refer/bundle)
        cluster_centers = kmeans.cluster_centers_.flatten()
        sorted_clusters = np.argsort(cluster_centers)
        if user_cluster == sorted_clusters[2]:
            offer = OFFERS[1]  # Highest cluster: Upsell to Premium
        elif user_cluster == sorted_clusters[1]:
            offer = OFFERS[0]  # Middle: 10% off
        else:
            offer = random.choice([OFFERS[2], OFFERS[3]])  # Lowest: refer/bundle
    else:
        # Fallback: rule-based or random
        if amount >= 50:
            offer = OFFERS[1]
        elif amount >= 20:
            offer = OFFERS[0]
        else:
            offer = random.choice(OFFERS)
    # --- Stats ---
    total_payments = len(PAYMENT_HISTORY)
    avg_amount = float(np.mean(amounts))
    most_common_method = max(set(p['method'] for p in PAYMENT_HISTORY), key=lambda m: [p['method'] for p in PAYMENT_HISTORY].count(m))
    stats = {
        'total_payments': total_payments,
        'avg_amount': avg_amount,
        'most_common_method': most_common_method
    }
    if method == 'mock':
        return jsonify({
            'status': 'success',
            'txn_id': str(uuid.uuid4()),
            'amount': amount,
            'method': method,
            'offer': offer,
            'is_anomaly': is_anomaly,
            'stats': stats
        })
    else:
        return jsonify({'status': 'error', 'error': 'Only mock payments are supported in demo.'}), 400 