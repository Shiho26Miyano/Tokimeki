# AI Platform Comparison with detailed model information
from flask import Blueprint, render_template, jsonify
import os

ai_platform_comparison_bp = Blueprint('ai_platform_comparison', __name__)

# Detailed model comparison data
MODEL_COMPARISON_DATA = {
    "mistral-small": {
        "name": "Mistral Small 3.2 24B Instruct",
        "provider": "Mistral AI",
        "context_window": "32K tokens",
        "max_tokens": "4000",
        "performance": "High",
        "cost": "Free",
        "strengths": ["Strong reasoning", "Code generation", "Multilingual"],
        "weaknesses": ["Slower than smaller models"],
        "best_for": ["Complex reasoning", "Code tasks", "Multilingual content"],
        "model_size": "24B parameters",
        "release_date": "2024",
        "license": "Commercial",
        "api_compatibility": "OpenAI-compatible"
    },
    "deepseek-r1": {
        "name": "DeepSeek R1 0528",
        "provider": "DeepSeek",
        "context_window": "128K tokens",
        "max_tokens": "4000",
        "performance": "Very High",
        "cost": "Free",
        "strengths": ["Extremely long context", "Strong reasoning", "Code expertise"],
        "weaknesses": ["May be slower due to size"],
        "best_for": ["Long documents", "Complex analysis", "Code review"],
        "model_size": "Large (exact size not disclosed)",
        "release_date": "2024",
        "license": "Commercial",
        "api_compatibility": "OpenAI-compatible"
    },
    "deepseek-chat": {
        "name": "DeepSeek Chat V3 0324",
        "provider": "DeepSeek",
        "context_window": "128K tokens",
        "max_tokens": "4000",
        "performance": "Very High",
        "cost": "Free",
        "strengths": ["Chat-optimized", "Long context", "Strong conversation"],
        "weaknesses": ["May be slower than smaller models"],
        "best_for": ["Conversational AI", "Chat applications", "Long discussions"],
        "model_size": "Large (exact size not disclosed)",
        "release_date": "2024",
        "license": "Commercial",
        "api_compatibility": "OpenAI-compatible",
        "note": "Recommended as chat-tuned"
    },
    "qwen3-8b": {
        "name": "Qwen3 8B",
        "provider": "Alibaba",
        "context_window": "32K tokens",
        "max_tokens": "4000",
        "performance": "Good",
        "cost": "Free",
        "strengths": ["Fast inference", "Good performance", "Open source"],
        "weaknesses": ["Smaller model size"],
        "best_for": ["Quick responses", "General tasks", "Resource-constrained environments"],
        "model_size": "8B parameters",
        "release_date": "2024",
        "license": "Commercial",
        "api_compatibility": "OpenAI-compatible"
    },
    "gemma-3n": {
        "name": "Gemma 3N E2B IT",
        "provider": "Google",
        "context_window": "8K tokens",
        "max_tokens": "4000",
        "performance": "Good",
        "cost": "Free",
        "strengths": ["Fast", "Efficient", "Google's latest"],
        "weaknesses": ["Limited context window"],
        "best_for": ["Quick tasks", "Short conversations", "Efficiency-focused apps"],
        "model_size": "2B parameters",
        "release_date": "2024",
        "license": "Commercial",
        "api_compatibility": "OpenAI-compatible"
    },
    "kimi-k2": {
        "name": "Kimi K2",
        "provider": "Moonshot AI",
        "context_window": "200K tokens",
        "max_tokens": "4000",
        "performance": "High",
        "cost": "Free",
        "strengths": ["Extremely long context", "Strong reasoning", "Chinese language"],
        "weaknesses": ["May be slower", "Limited English optimization"],
        "best_for": ["Long documents", "Chinese content", "Document analysis"],
        "model_size": "Large (exact size not disclosed)",
        "release_date": "2024",
        "license": "Commercial",
        "api_compatibility": "OpenAI-compatible"
    },
    "llama-maverick": {
        "name": "Llama 4 Maverick",
        "provider": "Meta",
        "context_window": "32K tokens",
        "max_tokens": "4000",
        "performance": "Good",
        "cost": "Free",
        "strengths": ["Community Llama", "Good performance", "Open source heritage"],
        "weaknesses": ["May not be latest Llama version"],
        "best_for": ["General tasks", "Llama ecosystem", "Community projects"],
        "model_size": "Large (exact size not disclosed)",
        "release_date": "2024",
        "license": "Commercial",
        "api_compatibility": "OpenAI-compatible",
        "note": "Community Llama"
    },
    "hunyuan": {
        "name": "Hunyuan A13B Instruct",
        "provider": "Tencent",
        "context_window": "32K tokens",
        "max_tokens": "4000",
        "performance": "Good",
        "cost": "Free",
        "strengths": ["Chinese language", "Good reasoning", "Tencent's latest"],
        "weaknesses": ["May be slower", "Limited English optimization"],
        "best_for": ["Chinese content", "Multilingual tasks", "Tencent ecosystem"],
        "model_size": "13B parameters",
        "release_date": "2024",
        "license": "Commercial",
        "api_compatibility": "OpenAI-compatible"
    },
    "quasar-alpha": {
        "name": "Quasar Alpha",
        "provider": "OpenRouter",
        "context_window": "32K tokens",
        "max_tokens": "4000",
        "performance": "Experimental",
        "cost": "Free",
        "strengths": ["Experimental features", "OpenRouter's latest", "Innovation"],
        "weaknesses": ["Experimental", "May be unstable", "Limited documentation"],
        "best_for": ["Testing new features", "Experimental projects", "Early adopters"],
        "model_size": "Unknown",
        "release_date": "2024",
        "license": "Commercial",
        "api_compatibility": "OpenAI-compatible",
        "note": "Experimental"
    }
}

@ai_platform_comparison_bp.route('/ai-platform-comparison')
def ai_platform_comparison():
    return render_template('ai_platform_comparison.html')

@ai_platform_comparison_bp.route('/api/model-comparison')
def get_model_comparison():
    """API endpoint to get detailed model comparison data"""
    return jsonify({
        "models": MODEL_COMPARISON_DATA,
        "categories": {
            "high_context": ["deepseek-r1", "deepseek-chat", "kimi-k2"],
            "fast_inference": ["qwen3-8b", "gemma-3n"],
            "multilingual": ["mistral-small", "kimi-k2", "hunyuan"],
            "code_focused": ["mistral-small", "deepseek-r1"],
            "chat_optimized": ["deepseek-chat"],
            "experimental": ["quasar-alpha"]
        }
    }) 