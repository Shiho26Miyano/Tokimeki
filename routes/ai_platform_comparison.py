from flask import Blueprint, render_template

ai_platform_comparison_bp = Blueprint('ai_platform_comparison', __name__)

@ai_platform_comparison_bp.route('/ai-platform-comparison')
def ai_platform_comparison():
    return render_template('ai_platform_comparison.html') 