"""
Market Pulse Learning Agent - Signal Prediction

Layer 2: Learning Layer (AWS Lambda)
职责: 学习历史数据，预测 Compute Agent 的 Signal
技术: AWS Lambda (Python 3.11), EventBridge, boto3, scikit-learn

模型: 线性回归 / Ridge（先用简单模型）
特征: 8 个特征（ret_1, ret_2, range, vol_norm, rolling stats）
训练频率: 每 1 小时
目标: 预测 Compute Agent 的 Signal

评估指标:
- R² Score（决定系数）
- MAE（平均绝对误差）
- 收敛标准: MAE < 0.1 持续 50 个 bars 或 R² > 0.9 持续 1 天

触发方式:
- EventBridge: 每 1 小时自动触发
- 手动触发: 通过 AWS Console 或 CLI
"""

import json
import boto3
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from statistics import mean, stdev
import logging

# 配置日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 尝试导入 scikit-learn
try:
    from sklearn.linear_model import Ridge
    from sklearn.metrics import r2_score, mean_absolute_error
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, using simple linear regression")

# 初始化 AWS 客户端
s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

# 支持的股票列表
SUPPORTED_TICKERS = ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META', 'GOOGL', 'JPM', 'XOM', 'SPY']

# 最少需要多少条 compute 信号才训练（降低后同一天内多次 Compute 即可开始学习）
MIN_SIGNALS_TO_TRAIN = 14
MIN_TRAINING_SAMPLES = 3


# ============================================================================
# 第一部分：数据读取
# ============================================================================

def read_compute_signals(date: str, hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
    """
    读取过去 N 小时的 Compute Agent signals
    
    Args:
        date: 日期字符串 "YYYY-MM-DD"
        hours: 读取多少小时的数据（默认 24 小时）
    
    Returns:
        Dict[ticker, List[signal_data]]: 按 ticker 分组的信号数据
    """
    signals_by_ticker = {ticker: [] for ticker in SUPPORTED_TICKERS}
    
    # 读取今天和昨天的数据（如果需要）
    end_date = datetime.fromisoformat(date).date()
    
    for i in range(hours // 24 + 1):  # 至少读取今天和昨天
        check_date = (end_date - timedelta(days=i)).isoformat()
        key = f"processed-data/{check_date}/compute-signals.json"
        
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            content = response['Body'].read().decode('utf-8')
            data = json.loads(content)
            
            signals = data.get('signals', [])
            
            # 按 ticker 分组
            for signal in signals:
                ticker = signal.get('ticker')
                if ticker in signals_by_ticker:
                    # 检查时间戳是否在范围内
                    signal_time = signal.get('timestamp')
                    if signal_time:
                        try:
                            signal_dt = datetime.fromisoformat(signal_time.replace('Z', '+00:00'))
                            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                            if signal_dt >= cutoff_time:
                                signals_by_ticker[ticker].append(signal)
                        except:
                            # 如果时间解析失败，仍然添加（可能是今天的数据）
                            signals_by_ticker[ticker].append(signal)
            
        except s3_client.exceptions.NoSuchKey:
            logger.debug(f"No compute signals found for {check_date}")
            continue
        except Exception as e:
            logger.warning(f"Error reading signals for {check_date}: {e}")
            continue
    
    # 按时间戳排序
    for ticker in signals_by_ticker:
        signals_by_ticker[ticker].sort(key=lambda x: x.get('timestamp', ''))
    
    logger.info(f"✅ Read signals for {sum(len(v) for v in signals_by_ticker.values())} total entries")
    return signals_by_ticker


# ============================================================================
# 第二部分：特征提取
# ============================================================================

def extract_features(signals: List[Dict[str, Any]], index: int) -> Optional[List[float]]:
    """
    提取 8 个特征用于模型训练
    
    特征列表:
    1. ret_1: 前 1 个 bar 的 Return
    2. ret_2: 前 2 个 bar 的 Return
    3. range: 当前 bar 的 (High - Low) / Open（需要从原始数据获取，这里用 Return 的绝对值近似）
    4. vol_norm: 当前 Vol 相对于历史平均的标准化值
    5. rolling_mean_5: 过去 5 个 bars 的 Return 均值
    6. rolling_mean_10: 过去 10 个 bars 的 Return 均值
    7. rolling_std_5: 过去 5 个 bars 的 Return 标准差
    8. rolling_std_10: 过去 10 个 bars 的 Return 标准差
    
    Args:
        signals: 信号数据列表（已排序）
        index: 当前索引（要预测的信号索引）
    
    Returns:
        List[float]: 8 个特征值，或 None（如果数据不足）
    """
    if index < 10:  # 需要至少 10 个历史数据点
        return None
    
    # 提取 Returns 和 Vols
    returns = [s.get('return', 0) for s in signals[:index+1]]
    vols = [s.get('vol', 1e-6) for s in signals[:index+1]]
    
    if len(returns) < 10:
        return None
    
    # 1. ret_1: 前 1 个 bar 的 Return
    ret_1 = returns[index - 1] if index > 0 else 0.0
    
    # 2. ret_2: 前 2 个 bar 的 Return
    ret_2 = returns[index - 2] if index > 1 else 0.0
    
    # 3. range: 用 Return 的绝对值近似（实际应该从原始 bar 数据获取）
    current_return = returns[index]
    range_feature = abs(current_return)
    
    # 4. vol_norm: 当前 Vol 相对于历史平均的标准化值
    current_vol = vols[index]
    avg_vol = mean(vols[:index]) if index > 0 else current_vol
    vol_norm = (current_vol - avg_vol) / (avg_vol + 1e-6) if avg_vol > 0 else 0.0
    
    # 5. rolling_mean_5: 过去 5 个 bars 的 Return 均值
    rolling_mean_5 = mean(returns[max(0, index-5):index]) if index >= 5 else mean(returns[:index]) if index > 0 else 0.0
    
    # 6. rolling_mean_10: 过去 10 个 bars 的 Return 均值
    rolling_mean_10 = mean(returns[max(0, index-10):index]) if index >= 10 else mean(returns[:index]) if index > 0 else 0.0
    
    # 7. rolling_std_5: 过去 5 个 bars 的 Return 标准差
    rolling_std_5 = stdev(returns[max(0, index-5):index]) if index >= 5 and len(returns[max(0, index-5):index]) > 1 else 0.0
    
    # 8. rolling_std_10: 过去 10 个 bars 的 Return 标准差
    rolling_std_10 = stdev(returns[max(0, index-10):index]) if index >= 10 and len(returns[max(0, index-10):index]) > 1 else 0.0
    
    return [
        ret_1,
        ret_2,
        range_feature,
        vol_norm,
        rolling_mean_5,
        rolling_mean_10,
        rolling_std_5,
        rolling_std_10
    ]


# ============================================================================
# 第三部分：模型训练和预测
# ============================================================================

def train_and_predict(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    训练模型并预测当前 Signal
    
    Args:
        signals: 信号数据列表（至少需要 20 个）
    
    Returns:
        Dict: {
            "signal_predicted": 0.48,
            "signal_actual": 0.52,
            "r2_score": 0.85,
            "mae": 0.08,
            "training_iterations": 24,
            "converged": False,
            "features": {...}
        }
    """
    if len(signals) < MIN_SIGNALS_TO_TRAIN:
        logger.warning(f"Insufficient signals for training: {len(signals)} < {MIN_SIGNALS_TO_TRAIN}")
        return {
            "signal_predicted": 0.0,
            "signal_actual": signals[-1].get('signal', 0.0) if signals else 0.0,
            "r2_score": 0.0,
            "mae": 1.0,
            "training_iterations": 0,
            "converged": False,
            "error": "Insufficient data"
        }
    
    # 准备训练数据
    X_train = []  # 特征
    y_train = []  # 目标（Signal）
    
    # 使用前 N-1 个信号作为训练数据，最后一个作为测试
    for i in range(10, len(signals) - 1):
        features = extract_features(signals, i)
        if features:
            X_train.append(features)
            y_train.append(signals[i].get('signal', 0.0))
    
    if len(X_train) < MIN_TRAINING_SAMPLES:
        logger.warning(f"Insufficient training samples: {len(X_train)} < {MIN_TRAINING_SAMPLES}")
        return {
            "signal_predicted": 0.0,
            "signal_actual": signals[-1].get('signal', 0.0),
            "r2_score": 0.0,
            "mae": 1.0,
            "training_iterations": 0,
            "converged": False,
            "error": "Insufficient training samples"
        }
    
    # 获取当前信号（最后一个）
    current_signal = signals[-1]
    current_features = extract_features(signals, len(signals) - 1)
    signal_actual = current_signal.get('signal', 0.0)
    
    if not current_features:
        return {
            "signal_predicted": 0.0,
            "signal_actual": signal_actual,
            "r2_score": 0.0,
            "mae": 1.0,
            "training_iterations": 0,
            "converged": False,
            "error": "Cannot extract features for current signal"
        }
    
    # 训练模型
    if SKLEARN_AVAILABLE:
        # 使用 Ridge 回归
        model = Ridge(alpha=1.0)
        scaler = StandardScaler()
        
        # 标准化特征
        X_train_scaled = scaler.fit_transform(X_train)
        X_current_scaled = scaler.transform([current_features])
        
        # 训练
        model.fit(X_train_scaled, y_train)
        
        # 预测
        signal_predicted = model.predict(X_current_scaled)[0]
        
        # 计算评估指标（在训练集上）
        y_pred_train = model.predict(X_train_scaled)
        r2 = r2_score(y_train, y_pred_train)
        mae = mean_absolute_error(y_train, y_pred_train)
        
    else:
        # 简单线性回归（不使用 scikit-learn）
        # 使用最小二乘法
        import numpy as np
        
        X_train_array = np.array(X_train)
        y_train_array = np.array(y_train)
        
        # 添加偏置项
        X_train_bias = np.column_stack([np.ones(len(X_train)), X_train_array])
        
        # 最小二乘解
        try:
            coeffs = np.linalg.lstsq(X_train_bias, y_train_array, rcond=None)[0]
            
            # 预测
            X_current_bias = np.array([1.0] + current_features)
            signal_predicted = np.dot(X_current_bias, coeffs)
            
            # 计算评估指标
            y_pred_train = np.dot(X_train_bias, coeffs)
            r2 = 1 - np.sum((y_train_array - y_pred_train) ** 2) / np.sum((y_train_array - np.mean(y_train_array)) ** 2)
            mae = np.mean(np.abs(y_train_array - y_pred_train))
            
        except Exception as e:
            logger.error(f"Error in simple linear regression: {e}")
            signal_predicted = signal_actual
            r2 = 0.0
            mae = 1.0
    
    # 检查收敛状态（简化版：基于当前指标）
    converged = (mae < 0.1) and (r2 > 0.9)
    
    return {
        "signal_predicted": round(signal_predicted, 4),
        "signal_actual": round(signal_actual, 4),
        "r2_score": round(r2, 4),
        "mae": round(mae, 4),
        "training_iterations": len(X_train),
        "converged": converged,
        "features": {
            "ret_1": round(current_features[0], 6),
            "ret_2": round(current_features[1], 6),
            "range": round(current_features[2], 6),
            "vol_norm": round(current_features[3], 6),
            "rolling_mean_5": round(current_features[4], 6),
            "rolling_mean_10": round(current_features[5], 6),
            "rolling_std_5": round(current_features[6], 6),
            "rolling_std_10": round(current_features[7], 6)
        }
    }


# ============================================================================
# 第四部分：主处理流程
# ============================================================================

def process_learning_task(date: str) -> Dict[str, Any]:
    """
    处理学习任务
    
    Args:
        date: 日期字符串 "YYYY-MM-DD"
    
    Returns:
        Dict: 处理结果统计
    """
    logger.info(f"🧠 Starting learning task for {date}")
    
    # 读取 Compute Agent signals（过去 7 天 ≈ 168 小时）
    # 增加时间窗口，让学习序列更长，模型可以使用更多历史样本
    signals_by_ticker = read_compute_signals(date, hours=168)
    
    all_models = {}
    
    # 对每个 ticker 训练模型（至少 MIN_SIGNALS_TO_TRAIN 条才训练，便于同一天内出学习结果）
    for ticker in SUPPORTED_TICKERS:
        signals = signals_by_ticker.get(ticker, [])
        
        if len(signals) < MIN_SIGNALS_TO_TRAIN:
            logger.warning(f"⚠️  Insufficient signals for {ticker}: {len(signals)} < {MIN_SIGNALS_TO_TRAIN}")
            continue
        
        try:
            # 训练模型并预测
            model_result = train_and_predict(signals)
            all_models[ticker] = model_result
            
            logger.info(f"✅ Trained model for {ticker}: R²={model_result['r2_score']:.4f}, MAE={model_result['mae']:.4f}")
            
        except Exception as e:
            logger.error(f"❌ Error training model for {ticker}: {e}")
            continue
    
    logger.info(f"✅ Trained {len(all_models)} models")
    
    # 存储结果到 S3
    processed_prefix = f"processed-data/{date}/"
    
    learning_data = {
        "date": date,
        "processed_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "models": all_models,
        "tickers_processed": len(all_models),
        "total_tickers": len(SUPPORTED_TICKERS)
    }
    
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f"{processed_prefix}learning-signals.json",
            Body=json.dumps(learning_data, default=str, ensure_ascii=False, indent=2),
            ContentType='application/json'
        )
        logger.info(f"✅ Stored learning signals to S3")
    except Exception as e:
        logger.error(f"❌ Error storing learning signals: {e}")
        raise
    
    return {
        "success": True,
        "date": date,
        "models_count": len(all_models),
        "tickers_processed": len(all_models),
        "total_tickers": len(SUPPORTED_TICKERS)
    }


# ============================================================================
# Lambda Handler (入口点)
# ============================================================================

def lambda_handler(event, context):
    """
    Lambda 函数入口点
    
    触发方式：
    1. EventBridge (定时): 每 1 小时
    2. 手动触发: 可以传递 date 参数
    
    Args:
        event: Lambda 事件对象
        context: Lambda 上下文
    
    Returns:
        Dict: 处理结果
    """
    try:
        # 获取日期（从 event 或使用今天）
        date = event.get('date') or datetime.now(timezone.utc).date().isoformat()
        
        logger.info(f"🧠 Learning Agent started for {date}")
        logger.info(f"📦 Bucket: {BUCKET_NAME}")
        
        if not BUCKET_NAME:
            raise ValueError("S3_BUCKET_NAME environment variable not set")
        
        # 执行学习任务
        result = process_learning_task(date)
        
        logger.info(f"✅ Learning completed: {result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in learning agent: {e}", exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
