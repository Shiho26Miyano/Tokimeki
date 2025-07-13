# DISABLED: This script is not currently used/imported in the app.
from flask import Blueprint, request, jsonify
import yfinance as yf

investment_playbooks_bp = Blueprint('investment_playbooks', __name__)

PLAYBOOKS = [
    {
        "name": "Warren Buffett Playbook",
        "role": "Value Investor",
        "philosophy": "Seeks wonderful companies at a fair price. Focus on moat, ROE, consistent earnings, and long-term holding.",
        "logic": {
            "filters": ["High ROE", "Low Debt/Equity", "Consistent Earnings Growth", "Reasonable PE ratio"],
            "example": "Buy if ROE > 15% and PE < 20 and EPS growth positive for 5 years"
        }
    },
    {
        "name": "Charlie Munger Playbook",
        "role": "Quality + Patience",
        "philosophy": "Buys high-quality businesses with strong moats and intelligent management. Emphasizes simplicity and mental models.",
        "logic": {
            "filters": ["Wide Moat", "Competent Management", "Strong Unit Economics"],
            "example": "Buy only if business is understandable and moat is defensible over decades"
        }
    },
    {
        "name": "Valuation Playbook",
        "role": "Intrinsic Value Estimator",
        "philosophy": "Calculates intrinsic value based on discounted cash flow or relative multiples. Looks for undervalued stocks.",
        "logic": {
            "method": "DCF or Relative Valuation",
            "example": "Buy if intrinsic value > current price * 1.2 (20% margin of safety)"
        }
    },
    {
        "name": "Fundamentals Playbook",
        "role": "Financial Health Checker",
        "philosophy": "Analyzes earnings, margins, revenue growth, cash flows, and balance sheet strength.",
        "logic": {
            "metrics": ["EPS Growth", "Profit Margin", "Operating Cash Flow", "Debt/Equity"],
            "example": "Buy if EPS growth > 10%, Debt/Equity < 1, and OCF is positive"
        }
    },
    {
        "name": "Risk Manager Playbook",
        "role": "Drawdown & Volatility Control",
        "philosophy": "Ensures portfolio stays within acceptable risk levels. Limits position size and exposure to volatile assets.",
        "logic": {
            "rules": ["Max position size = 5%", "Volatility cap = 30-day std dev < 3%"],
            "example": "Reduce weight if volatility > 0.03 or stock has 10%+ drawdown"
        }
    }
]

def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    return {
        'pe_ratio': info.get('trailingPE', 0),
        'roe': info.get('returnOnEquity', 0),
        'debt_to_equity': info.get('debtToEquity', 0),
        'eps_growth': info.get('earningsQuarterlyGrowth', 0),
        'profit_margin': info.get('profitMargins', 0),
        'operating_cash_flow': info.get('operatingCashflow', 0),
    }

@investment_playbooks_bp.route('/analyze_playbook', methods=['POST'])
def analyze_playbook():
    data = request.get_json()
    symbol = data.get('symbol')
    playbook_name = data.get('playbook_name')

    if not symbol or not playbook_name:
        return jsonify({'error': 'Symbol and playbook name are required'}), 400

    playbook = next((p for p in PLAYBOOKS if p['name'] == playbook_name), None)
    if not playbook:
        return jsonify({'error': 'Playbook not found'}), 404

    try:
        stock_data = get_stock_data(symbol)
        
        decision = "Hold"
        reasons = ["General market conditions are neutral."]

        if playbook_name == "Warren Buffett Playbook":
            roe = stock_data['roe'] or 0
            pe_ratio = stock_data['pe_ratio'] or 0
            
            if roe > 0.15 and pe_ratio < 20:
                decision = "Buy"
                reasons = [f"ROE is attractive ({roe:.2f} > 15%)", f"P/E ratio is reasonable ({pe_ratio:.2f} < 20)"]
            else:
                decision = "Avoid"
                reasons = [f"Does not meet ROE criteria ({roe:.2f}) or P/E criteria ({pe_ratio:.2f})"]

        return jsonify({
            'playbook': playbook,
            'stock_data': stock_data,
            'decision': decision,
            'reasons': reasons
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@investment_playbooks_bp.route('/playbooks', methods=['GET'])
def get_playbooks():
    return jsonify(PLAYBOOKS) 