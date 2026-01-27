"""
Market Pulse Compute Agent - Signal Formula

Layer 2: Processing Layer
职责: 读取原始数据，计算 Signal 指标
技术: AWS Lambda (Python 3.11), EventBridge, boto3, statistics

公式:
Return = (Close - Open) / Open
Vol = Std(Return over last 20 bars) + 1e-6
Signal = Return / Vol

处理流程:
1. 读取 raw-data/ (从 Storage Layer)
2. 计算 Signal (使用新公式)
3. 存储结果 (到 Storage Layer)

触发方式:
- EventBridge: 每 5 分钟自动触发 (近实时)
- 手动触发: 通过 AWS Console 或 CLI

股票列表: AAPL, MSFT, AMZN, NVDA, TSLA, META, GOOGL, JPM, XOM, SPY
"""

import json
import boto3
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from statistics import stdev
import logging

# 配置日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 初始化 AWS 客户端
s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

# 支持的股票列表
SUPPORTED_TICKERS = ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META', 'GOOGL', 'JPM', 'XOM', 'SPY']


# ============================================================================
# 第一部分：数据读取
# ============================================================================

def read_raw_data_from_s3(date: str, ticker: str) -> List[Dict[str, Any]]:
    """
    从 S3 读取指定日期和 ticker 的原始数据
    
    Args:
        date: 日期字符串，格式 "YYYY-MM-DD"
        ticker: 股票代码
    
    Returns:
        List[Dict]: 原始 bar 数据列表（按时间排序）
    """
    prefix = f"raw-data/{date}/{ticker}/"
    
    logger.info(f"📥 Reading raw data from S3: {prefix}")
    
    bars = []
    
    try:
        # 列出所有对象
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix)
        
        for page in pages:
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                key = obj['Key']
                
                # 读取 JSON 文件
                try:
                    response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
                    bar_data = json.loads(response['Body'].read().decode('utf-8'))
                    bars.append(bar_data)
                except Exception as e:
                    logger.warning(f"Failed to read {key}: {e}")
                    continue
        
        # 按时间戳排序
        bars.sort(key=lambda x: x.get('timestamp', ''))
        
        logger.info(f"✅ Read {len(bars)} raw bars for {ticker}")
        return bars
        
    except Exception as e:
        logger.error(f"❌ Error reading raw data for {ticker}: {e}")
        return []


# ============================================================================
# 第二部分：Signal 计算
# ============================================================================

def calculate_signal(bars: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    计算 Signal 指标
    
    公式:
    Return = (Close - Open) / Open
    Vol = Std(Return over last 20 bars) + 1e-6
    Signal = Return / Vol
    
    Args:
        bars: 原始 bar 数据列表（至少需要 20 个 bars）
    
    Returns:
        Dict: {
            "timestamp": "...",
            "ticker": "...",
            "return": 0.0012,
            "vol": 0.0023,
            "signal": 0.52
        } 或 None（如果数据不足）
    """
    if len(bars) < 20:
        logger.warning(f"Insufficient bars: {len(bars)} < 20")
        return None
    
    # 获取最新 bar
    latest_bar = bars[-1]
    bar_data = latest_bar.get('bar_data', {})
    
    open_price = bar_data.get('open')
    close_price = bar_data.get('close')
    ticker = latest_bar.get('ticker', 'UNKNOWN')
    timestamp = latest_bar.get('timestamp')
    
    if not open_price or not close_price or open_price == 0:
        logger.warning(f"Invalid price data for {ticker}")
        return None
    
    # 计算当前 Return
    current_return = (close_price - open_price) / open_price
    
    # 计算过去 20 个 bars 的 Return 列表
    returns = []
    for i in range(max(0, len(bars) - 20), len(bars)):
        bar = bars[i]
        bar_data_item = bar.get('bar_data', {})
        bar_open = bar_data_item.get('open')
        bar_close = bar_data_item.get('close')
        
        if bar_open and bar_close and bar_open > 0:
            bar_return = (bar_close - bar_open) / bar_open
            returns.append(bar_return)
    
    if len(returns) < 2:
        logger.warning(f"Insufficient returns for volatility calculation: {len(returns)}")
        return None
    
    # 计算 Vol (标准差 + 小常数)
    vol = stdev(returns) + 1e-6
    
    # 计算 Signal
    signal = current_return / vol
    
    return {
        "timestamp": timestamp,
        "ticker": ticker,
        "return": round(current_return, 6),
        "vol": round(vol, 6),
        "signal": round(signal, 4),
        "bars_used": len(returns)
    }


# ============================================================================
# 第三部分：主处理流程
# ============================================================================

def process_daily_signals(date: str) -> Dict[str, Any]:
    """
    处理指定日期的数据，计算所有 ticker 的 Signal
    
    Args:
        date: 日期字符串 "YYYY-MM-DD"
    
    Returns:
        Dict: 处理结果统计
    """
    logger.info(f"🚀 Starting signal processing for {date}")
    
    all_signals = []
    
    # 对每个 ticker 计算 Signal
    for ticker in SUPPORTED_TICKERS:
        try:
            # 读取原始数据
            bars = read_raw_data_from_s3(date, ticker)
            
            if len(bars) < 20:
                logger.warning(f"⚠️  Insufficient data for {ticker}: {len(bars)} bars")
                continue
            
            # 计算 Signal
            signal_data = calculate_signal(bars)
            
            if signal_data:
                all_signals.append(signal_data)
                logger.info(f"✅ Computed signal for {ticker}: {signal_data['signal']:.4f}")
            else:
                logger.warning(f"⚠️  Failed to compute signal for {ticker}")
                
        except Exception as e:
            logger.error(f"❌ Error processing {ticker}: {e}")
            continue
    
    logger.info(f"✅ Computed {len(all_signals)} signals for {len(SUPPORTED_TICKERS)} tickers")
    
    # 存储结果到 S3
    processed_prefix = f"processed-data/{date}/"
    
    signals_data = {
        "date": date,
        "processed_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "signals": all_signals,
        "tickers_processed": len(all_signals),
        "total_tickers": len(SUPPORTED_TICKERS)
    }
    
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f"{processed_prefix}compute-signals.json",
            Body=json.dumps(signals_data, default=str, ensure_ascii=False, indent=2),
            ContentType='application/json'
        )
        logger.info(f"✅ Stored compute signals to S3")
    except Exception as e:
        logger.error(f"❌ Error storing signals: {e}")
        raise
    
    return {
        "success": True,
        "date": date,
        "signals_count": len(all_signals),
        "tickers_processed": len(all_signals),
        "total_tickers": len(SUPPORTED_TICKERS)
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
        
        logger.info(f"📅 Processing Compute Agent signals for {date}")
        logger.info(f"📦 Bucket: {BUCKET_NAME}")
        
        if not BUCKET_NAME:
            raise ValueError("S3_BUCKET_NAME environment variable not set")
        
        # 执行处理
        result = process_daily_signals(date)
        
        logger.info(f"✅ Processing completed: {result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing Compute Agent signals: {e}", exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
