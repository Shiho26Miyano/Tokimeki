# DISABLED: This script is not currently used/imported in the app.
from flask import Blueprint, jsonify, request
import logging
from datasets import load_dataset
from transformers import AutoTokenizer, pipeline
from transformers_interpret import SequenceClassificationExplainer
import numpy as np
from multiprocessing import Process, Queue
import time
import uuid

hf_tweeteval_bp = Blueprint('hf_tweeteval', __name__)

# Load model, tokenizer, and dataset ONCE at module level
classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
dataset = load_dataset("tweet_eval", "sentiment", split="train")

# Model cache for dynamic selection
MODEL_CACHE = {}

# Helper to get or load a model pipeline
def get_classifier(model_name):
    if model_name not in MODEL_CACHE:
        MODEL_CACHE[model_name] = pipeline("sentiment-analysis", model=model_name)
    return MODEL_CACHE[model_name]

ALLOWED_MODELS = [
    "distilbert-base-uncased-finetuned-sst-2-english",
    "nreimers/TinyBERT_L-4_H-312_A-12-SST2",
    "cardiffnlp/twitter-roberta-base-sentiment-latest"
]

def blocking_inference(text, model_name, q):
    try:
        start_time = time.time()
        classifier = get_classifier(model_name)
        result = classifier(text)[0]
        label = result["label"]
        confidence = result["score"]
        explainer = SequenceClassificationExplainer(classifier.model, classifier.tokenizer)
        word_attributions = explainer(text)
        top_words = sorted(word_attributions, key=lambda x: abs(x[1]), reverse=True)[:3]
        top_words_str = ', '.join([f"'{w[0]}'" for w in top_words])
        explanation = f"Top contributing words: {top_words_str}."
        user_words = set(text.lower().split())
        best_match = None
        best_score = -1
        for ex in dataset.select(range(1000)):
            ex_words = set(ex['text'].lower().split())
            score = len(user_words & ex_words)
            if score > best_score:
                best_score = score
                best_match = ex
        similar_example = None
        if best_match:
            label_map = {0: "NEGATIVE", 1: "NEUTRAL", 2: "POSITIVE"}
            similar_example = {
                "text": best_match["text"],
                "label": label_map.get(best_match["label"], str(best_match["label"]))
            }
        elapsed = time.time() - start_time
        q.put({
            "text": text,
            "label": label,
            "confidence": confidence,
            "explanation": explanation,
            "similar_example": similar_example,
            "inference_time": elapsed,
            "model": model_name
        })
    except Exception as e:
        logging.exception("Error in analyze_tweet blocking_inference")
        q.put({"error": f"Internal error: {str(e)}"})

@hf_tweeteval_bp.route('/hf_tweeteval_sample', methods=['GET'])
def hf_tweeteval_sample():
    # Step 1: Load dataset
    dataset = load_dataset("tweet_eval", "sentiment")
    # Step 2: Preprocess/tokenize
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    def tokenize(example):
        return tokenizer(example["text"], truncation=True, padding="max_length")
    tokenized = dataset.map(tokenize, batched=True)
    # Step 3: Log and return a sample
    sample = tokenized["train"][0]
    logging.info(f"[HF_TWEETEVAL] Tokenized Sample: {sample}")
    return jsonify(sample)

@hf_tweeteval_bp.route('/analyze_tweet', methods=['POST'])
def analyze_tweet():
    data = request.get_json()
    text = data.get("text", "")
    model_name = data.get("model", "distilbert-base-uncased-finetuned-sst-2-english")
    if model_name not in ALLOWED_MODELS:
        return jsonify({"error": "Invalid model name."}), 400
    if not text:
        return jsonify({"error": "No text provided."}), 400
    q = Queue()
    p = Process(target=blocking_inference, args=(text, model_name, q))
    p.start()
    p.join(2000)  # Timeout after 2000 seconds
    if p.is_alive():
        p.terminate()
        return jsonify({"error": "Processing timed out."}), 500
    if not q.empty():
        result = q.get()
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)
    else:
        return jsonify({"error": "No result returned from process."}), 500

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