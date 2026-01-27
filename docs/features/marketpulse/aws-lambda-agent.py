"""
Market Pulse AWS Lambda Agent (v3 - Minimal)

Layer 2: Processing Layer
职责: 读取原始数据，计算 pulse 指标
技术: AWS Lambda (Python 3.11), EventBridge, boto3, statistics

处理流程 (v3 - simplified):
1. 读取 raw-data/ (从 Storage Layer)
2. 计算指标 (velocity, volume surge, volatility, stress, breadth)
3. 存储结果 (到 Storage Layer)

Deleted (v3):
- ❌ 学习模式 (learn_patterns)
- ❌ 生成总结 (generate_daily_summary)
- ❌ Insights 存储

触发方式:
- EventBridge: 每 5 分钟自动触发 (近实时)
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

# 初始化 AWS 客户端
s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

# ============================================================================
# 第一部分：数据读取
# ============================================================================

def read_raw_data_from_s3(date: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    从 S3 读取指定日期的原始数据
    
    Args:
        date: 日期字符串，格式 "YYYY-MM-DD"
    
    Returns:
        Dict[ticker, List[bar_data]]: 按 ticker 分组的原始 bar 数据
    
    示例返回:
        {
            "SPY": [
                {"timestamp": "2024-01-15T10:00:00Z", "bar_data": {...}},
                {"timestamp": "2024-01-15T10:01:00Z", "bar_data": {...}},
            ],
            "QQQ": [...]
        }
    """
    raw_bars_by_ticker = {}
    prefix = f"raw-data/{date}/"
    
    logger.info(f"📥 Reading raw data from S3: {prefix}")
    
    try:
        # 列出所有对象
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix)
        
        total_files = 0
        for page in pages:
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                key = obj['Key']
                # 解析路径: raw-data/YYYY-MM-DD/ticker/timestamp.json
                parts = key.split('/')
                
                if len(parts) >= 4:
                    ticker = parts[2]  # ticker 是路径的第三部分
                    
                    # 读取 JSON 文件
                    try:
                        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
                        bar_data = json.loads(response['Body'].read().decode('utf-8'))
                        
                        if ticker not in raw_bars_by_ticker:
                            raw_bars_by_ticker[ticker] = []
                        raw_bars_by_ticker[ticker].append(bar_data)
                        total_files += 1
                    except Exception as e:
                        logger.warning(f"Failed to read {key}: {e}")
                        continue
        
        logger.info(f"✅ Read {total_files} raw bar files for {len(raw_bars_by_ticker)} tickers")
        
        # 按时间戳排序
        for ticker in raw_bars_by_ticker:
            raw_bars_by_ticker[ticker].sort(
                key=lambda x: x.get('timestamp', '')
            )
        
        return raw_bars_by_ticker
        
    except Exception as e:
        logger.error(f"❌ Error reading raw data: {e}")
        return {}


# ============================================================================
# 第二部分：Pulse 指标计算
# ============================================================================

def calculate_price_velocity(prices: List[float]) -> float:
    """
    计算价格速度（价格变化率）
    
    公式: (最新价格 - 5分钟前价格) / 5分钟前价格 * 100
    
    Args:
        prices: 价格列表（按时间顺序）
    
    Returns:
        float: 价格速度百分比
    """
    if len(prices) < 5:
        return 0.0
    
    # 使用最近5个价格点计算速度
    recent = prices[-5:]
    if recent[0] > 0:
        velocity = ((recent[-1] - recent[0]) / recent[0]) * 100
        return round(velocity, 4)
    return 0.0


def calculate_volume_surge(current_volume: float, avg_volume: float) -> Dict[str, Any]:
    """
    计算成交量激增
    
    Args:
        current_volume: 当前成交量
        avg_volume: 平均成交量（过去20个周期）
    
    Returns:
        Dict: {
            "surge_ratio": 1.5,  # 当前/平均
            "is_surge": True,     # 是否激增（>1.5倍）
            "magnitude": "high"   # normal/high/extreme
        }
    """
    if avg_volume == 0:
        surge_ratio = 1.0
    else:
        surge_ratio = current_volume / avg_volume
    
    is_surge = surge_ratio >= 1.5
    
    if surge_ratio >= 3.0:
        magnitude = "extreme"
    elif surge_ratio >= 1.5:
        magnitude = "high"
    else:
        magnitude = "normal"
    
    return {
        "surge_ratio": round(surge_ratio, 2),
        "is_surge": is_surge,
        "magnitude": magnitude
    }


def calculate_volatility(prices: List[float]) -> Dict[str, Any]:
    """
    计算波动率
    
    使用收益率的标准差来衡量波动
    
    Args:
        prices: 价格列表
    
    Returns:
        Dict: {
            "volatility": 0.8,    # 波动率百分比
            "is_burst": True,     # 是否爆发（>1.0%）
            "magnitude": "high"   # normal/high/extreme
        }
    """
    if len(prices) < 2:
        return {
            "volatility": 0.0,
            "is_burst": False,
            "magnitude": "normal"
        }
    
    # 计算收益率
    returns = []
    for i in range(1, len(prices)):
        if prices[i-1] > 0:
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
    
    if len(returns) < 2:
        return {
            "volatility": 0.0,
            "is_burst": False,
            "magnitude": "normal"
        }
    
    # 使用最近20个收益率计算波动率
    recent_returns = returns[-20:] if len(returns) >= 20 else returns
    volatility = stdev(recent_returns) * 100 if len(recent_returns) >= 2 else 0.0
    
    is_burst = volatility > 1.0
    
    if volatility > 2.0:
        magnitude = "extreme"
    elif volatility > 1.0:
        magnitude = "high"
    else:
        magnitude = "normal"
    
    return {
        "volatility": round(volatility, 4),
        "is_burst": is_burst,
        "magnitude": magnitude
    }


def calculate_stress_index(
    volatility: float,
    volume_surge_ratio: float,
    velocity: float
) -> Dict[str, Any]:
    """
    计算市场压力指数
    
    综合波动率、成交量激增和价格速度
    
    Args:
        volatility: 波动率
        volume_surge_ratio: 成交量激增比率
        velocity: 价格速度
    
    Returns:
        Dict: {
            "stress_score": 0.5,      # 0-1 之间的压力分数
            "regime": "moderate_stress" # calm/low_stress/moderate_stress/high_stress/extreme_stress
        }
    """
    # 归一化各项指标到 0-1 范围
    vol_score = min(volatility / 10.0, 1.0)  # 10% 波动 = 满分
    volume_score = min(volume_surge_ratio / 5.0, 1.0)  # 5倍成交量 = 满分
    velocity_score = min(abs(velocity) / 10.0, 1.0)  # 10% 价格变化 = 满分
    
    # 加权平均
    stress_score = (
        vol_score * 0.3 +      # 波动率权重 30%
        volume_score * 0.2 +   # 成交量权重 20%
        velocity_score * 0.2 + # 速度权重 20%
        0.3                     # 基础压力 30%
    )
    
    # 确定市场状态
    if stress_score >= 0.8:
        regime = "extreme_stress"
    elif stress_score >= 0.6:
        regime = "high_stress"
    elif stress_score >= 0.4:
        regime = "moderate_stress"
    elif stress_score >= 0.2:
        regime = "low_stress"
    else:
        regime = "calm"
    
    return {
        "stress_score": round(stress_score, 3),
        "regime": regime
    }


def compute_pulse_from_bars(bars: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    从原始 bar 数据计算完整的 pulse event
    
    Args:
        bars: 原始 bar 数据列表（至少5个）
    
    Returns:
        Dict: 完整的 pulse event，包含所有指标
    """
    if len(bars) < 5:
        logger.warning(f"Insufficient bars: {len(bars)} < 5")
        return None
    
    # 提取价格和成交量
    prices = [bar['bar_data']['close'] for bar in bars]
    volumes = [bar['bar_data']['volume'] for bar in bars]
    
    # 获取最新 bar 的信息
    latest_bar = bars[-1]
    current_price = prices[-1]
    current_volume = volumes[-1]
    timestamp = latest_bar.get('timestamp')
    
    # 计算各项指标
    velocity = calculate_price_velocity(prices)
    avg_volume = mean(volumes[-20:]) if len(volumes) >= 20 else current_volume
    volume_surge = calculate_volume_surge(current_volume, avg_volume)
    volatility_burst = calculate_volatility(prices)
    
    # 计算压力指数
    stress = calculate_stress_index(
        volatility=volatility_burst['volatility'],
        volume_surge_ratio=volume_surge['surge_ratio'],
        velocity=velocity
    )
    
    # 构建完整的 pulse event
    pulse_event = {
        "timestamp": timestamp,
        "ticker": latest_bar.get('ticker', 'MARKET'),
        "price": current_price,
        "volume": current_volume,
        "velocity": velocity,
        "volume_surge": volume_surge,
        "volatility_burst": volatility_burst,
        "stress": stress['stress_score'],
        "regime": stress['regime'],
        "breadth": {  # 简化版，实际可以从多个 ticker 计算
            "breadth": "neutral"
        }
    }
    
    return pulse_event




# ============================================================================
# 第五部分：主处理流程
# ============================================================================

def process_daily_data(date: str) -> Dict[str, Any]:
    """
    处理指定日期的数据 (v3 - Minimal)
    
    处理流程：
    1. 读取原始数据
    2. 计算 pulse events（每5分钟一个）
    3. 存储结果
    
    Args:
        date: 日期字符串 "YYYY-MM-DD"
    
    Returns:
        Dict: 处理结果统计
    """
    logger.info(f"🚀 Starting processing for {date}")
    
    # 步骤 1: 读取原始数据
    raw_bars_by_ticker = read_raw_data_from_s3(date)
    
    if not raw_bars_by_ticker:
        logger.warning(f"⚠️  No raw data found for {date}")
        return {
            "success": False,
            "message": f"No raw data found for {date}",
            "pulse_events_count": 0
        }
    
    # 步骤 2: 计算 pulse events
    # 使用主要 ticker (SPY) 作为市场代表
    primary_ticker = "SPY"
    if primary_ticker not in raw_bars_by_ticker:
        # 如果没有 SPY，使用第一个可用的 ticker
        primary_ticker = list(raw_bars_by_ticker.keys())[0]
        logger.info(f"Using {primary_ticker} as primary ticker")
    
    bars = raw_bars_by_ticker[primary_ticker]
    pulse_events = []
    
    # 每5分钟计算一个 pulse event
    window_size = 5  # 5个1分钟bar = 5分钟窗口
    for i in range(0, len(bars), window_size):
        window_bars = bars[i:i+window_size]
        
        if len(window_bars) >= 5:
            pulse = compute_pulse_from_bars(window_bars)
            if pulse:
                pulse_events.append(pulse)
    
    logger.info(f"✅ Computed {len(pulse_events)} pulse events")
    
    # 步骤 3: 存储结果到 S3 (v3 - only pulse events)
    processed_prefix = f"processed-data/{date}/"
    
    # 存储 pulse events
    pulse_events_data = {
        "date": date,
        "processed_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "events": pulse_events
    }
    
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=f"{processed_prefix}pulse-events.json",
        Body=json.dumps(pulse_events_data, default=str, ensure_ascii=False, indent=2),
        ContentType='application/json'
    )
    logger.info(f"✅ Stored pulse events to S3")
    
    return {
        "success": True,
        "date": date,
        "pulse_events_count": len(pulse_events)
    }


# ============================================================================
# Lambda Handler (入口点)
# ============================================================================

def lambda_handler(event, context):
    """
    Lambda 函数入口点
    
    触发方式：
    1. EventBridge (定时): event 包含 date 字段
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
        
        logger.info(f"📅 Processing Market Pulse data for {date}")
        logger.info(f"📦 Bucket: {BUCKET_NAME}")
        
        if not BUCKET_NAME:
            raise ValueError("S3_BUCKET_NAME environment variable not set")
        
        # 执行处理
        result = process_daily_data(date)
        
        logger.info(f"✅ Processing completed: {result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing Market Pulse data: {e}", exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
