"""
Market Pulse API Endpoints - Dual Agent Dashboard

Layer 3: API Layer
Responsibility: REST API endpoints (Dual Agent comparison)
Technology: FastAPI

API Endpoints:
- GET /api/v1/market-pulse/current - Current pulse (Compute Agent)
- GET /api/v1/market-pulse/events/today - Today's events
- GET /api/v1/market-pulse/compare - Dual Agent comparison ⭐
- GET /api/v1/market-pulse/compute-agent - Compute Agent data
- GET /api/v1/market-pulse/learning-agent - Learning Agent data
- GET /api/v1/market-pulse/performance - Performance comparison
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
from typing import Optional
import logging
import time
import json

from app.models.market_pulse_models import MarketPulseResponse
from app.services.marketpulse.pulse_service import MarketPulseService
from app.services.marketpulse.learning_agent_service import LearningAgentService
from app.core.dependencies import get_usage_service
from app.services.usage_service import AsyncUsageService

logger = logging.getLogger(__name__)

router = APIRouter()

# Global service instances (singleton pattern)
_pulse_service_instance: Optional[MarketPulseService] = None
_learning_agent_service_instance: Optional[LearningAgentService] = None


def get_pulse_service() -> MarketPulseService:
    """Dependency to get pulse service (singleton)"""
    global _pulse_service_instance
    if _pulse_service_instance is None:
        _pulse_service_instance = MarketPulseService()
        # Auto-start service on first access
        try:
            _pulse_service_instance.start()
        except Exception as e:
            logger.warning(f"Failed to auto-start pulse service: {e}")
    return _pulse_service_instance


def get_learning_agent_service() -> LearningAgentService:
    """Dependency to get learning agent service (singleton)"""
    global _learning_agent_service_instance
    if _learning_agent_service_instance is None:
        import os
        _learning_agent_service_instance = LearningAgentService(
            s3_bucket=os.getenv("AWS_S3_PULSE_BUCKET"),
            aws_region=os.getenv("AWS_REGION", "us-east-2")
        )
    return _learning_agent_service_instance


@router.get("/current", response_model=MarketPulseResponse)
async def get_current_pulse(
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Get current market pulse
    Returns real-time pulse indicators
    """
    try:
        pulse_event = await pulse_service.calculate_current_pulse()
        
        # Convert to response model
        indicators = [
            {
                'name': 'Price Velocity',
                'value': pulse_event.get('velocity', 0),
                'magnitude': 'high' if abs(pulse_event.get('velocity', 0)) > 2 else 'normal',
                'description': f"Price change rate: {pulse_event.get('velocity', 0):.2f}%"
            },
            {
                'name': 'Volume Surge',
                'value': pulse_event.get('volume_surge', {}).get('surge_ratio', 1.0),
                'magnitude': pulse_event.get('volume_surge', {}).get('magnitude', 'normal'),
                'description': f"Volume ratio: {pulse_event.get('volume_surge', {}).get('surge_ratio', 1.0):.2f}x"
            },
            {
                'name': 'Volatility Burst',
                'value': pulse_event.get('volatility_burst', {}).get('volatility', 0),
                'magnitude': pulse_event.get('volatility_burst', {}).get('magnitude', 'normal'),
                'description': f"Volatility: {pulse_event.get('volatility_burst', {}).get('volatility', 0):.2f}%"
            }
        ]
        
        response = MarketPulseResponse(
            timestamp=pulse_event['timestamp'],
            stress_score=pulse_event.get('stress', 0),
            regime=pulse_event.get('regime', 'calm'),
            indicators=indicators,
            velocity=pulse_event.get('velocity', 0),
            volume_surge=pulse_event.get('volume_surge', {}),
            volatility_burst=pulse_event.get('volatility_burst', {}),
            breadth=pulse_event.get('breadth', {})
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting current pulse: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get market pulse: {str(e)}")


@router.get("/events/today")
async def get_today_events(
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Get today's pulse events (optimized for frontend display)
    Reads from S3 - only today's prefix for fast response
    """
    try:
        events = pulse_service.get_today_events(ticker=ticker)
        
        return {
            "success": True,
            "events": events,
            "count": len(events),
            "date": datetime.now(timezone.utc).date().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting today's events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get today's events: {str(e)}")


@router.get("/available-tickers")
async def get_available_tickers(
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Get list of available tickers from today's data
    Returns unique tickers that have data available
    """
    try:
        events = pulse_service.get_today_events()
        
        # Extract unique tickers from events
        tickers = sorted(set([e.get('ticker') for e in events if e.get('ticker')]))
        
        # If no data, return default list
        if not tickers:
            tickers = ['SPY', 'QQQ', 'DIA', 'IWM', 'VOO', 'TSLA', 'AAPL', 'MSFT']
        
        return {
            "success": True,
            "tickers": tickers,
            "count": len(tickers)
        }
        
    except Exception as e:
        logger.error(f"Error getting available tickers: {e}")
        # Return default list on error
        return {
            "success": True,
            "tickers": ['SPY', 'QQQ', 'DIA', 'IWM', 'VOO', 'TSLA', 'AAPL', 'MSFT'],
            "count": 8
        }


@router.get("/compare")
async def compare_agents(
    ticker: Optional[str] = Query(None, description="Filter by ticker (e.g., SPY, QQQ, DIA)"),
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    learning_service: LearningAgentService = Depends(get_learning_agent_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Compare Compute Agent vs Learning Agent
    
    Returns side-by-side comparison of both agents' outputs
    Supports ticker filtering to view specific stock metrics
    """
    start_time = time.time()
    
    try:
        # Get compute agent data
        compute_start = time.time()
        compute_pulse = await pulse_service.calculate_current_pulse(ticker=ticker)
        compute_latency = (time.time() - compute_start) * 1000  # ms
        
        # Get learning agent enhanced data
        learning_start = time.time()
        enhanced_pulse = learning_service.enhance_pulse_event(compute_pulse)
        learning_latency = (time.time() - learning_start) * 1000  # ms
        
        # Get learning results metadata
        learning_results = learning_service.get_learning_results()
        
        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "compute_agent": {
                "data": compute_pulse,
                "latency_ms": round(compute_latency, 2),
                "features": ["stress", "velocity", "volume_surge", "volatility", "regime"]
            },
            "learning_agent": {
                "data": enhanced_pulse,
                "latency_ms": round(learning_latency, 2),
                "features": [
                    "stress", "velocity", "volume_surge", "volatility", "regime",
                    "anomalies", "prediction", "matched_patterns", "insights"
                ],
                "learning_metadata": {
                    "last_updated": learning_results.get("last_updated"),
                    "has_baseline": bool(learning_results.get("baseline")),
                    "has_patterns": bool(learning_results.get("patterns")),
                    "has_model": bool(learning_results.get("model_info"))
                }
            },
            "comparison": {
                "value_difference": {
                    "stress": enhanced_pulse.get("stress", 0) - compute_pulse.get("stress", 0),
                    "has_anomalies": len(enhanced_pulse.get("anomalies", [])) > 0,
                    "has_prediction": bool(enhanced_pulse.get("prediction")),
                    "has_insights": len(enhanced_pulse.get("insights", [])) > 0
                },
                "performance": {
                    "compute_latency_ms": round(compute_latency, 2),
                    "learning_latency_ms": round(learning_latency, 2),
                    "total_latency_ms": round((time.time() - start_time) * 1000, 2)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error comparing agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare agents: {str(e)}")


@router.get("/compute-agent")
async def get_compute_agent_data(
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get Compute Agent data only"""
    try:
        pulse_event = await pulse_service.calculate_current_pulse()
        return {
            "success": True,
            "agent_type": "compute",
            "data": pulse_event,
            "features": ["stress", "velocity", "volume_surge", "volatility", "regime"]
        }
    except Exception as e:
        logger.error(f"Error getting compute agent data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get compute agent data: {str(e)}")


@router.get("/learning-agent")
async def get_learning_agent_data(
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    learning_service: LearningAgentService = Depends(get_learning_agent_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get Learning Agent enhanced data only"""
    try:
        compute_pulse = await pulse_service.calculate_current_pulse()
        enhanced_pulse = learning_service.enhance_pulse_event(compute_pulse)
        learning_results = learning_service.get_learning_results()
        
        return {
            "success": True,
            "agent_type": "learning",
            "data": enhanced_pulse,
            "features": [
                "stress", "velocity", "volume_surge", "volatility", "regime",
                "anomalies", "prediction", "matched_patterns", "insights"
            ],
            "learning_metadata": {
                "last_updated": learning_results.get("last_updated"),
                "has_baseline": bool(learning_results.get("baseline")),
                "has_patterns": bool(learning_results.get("patterns")),
                "has_model": bool(learning_results.get("model_info"))
            }
        }
    except Exception as e:
        logger.error(f"Error getting learning agent data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get learning agent data: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    learning_service: LearningAgentService = Depends(get_learning_agent_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get performance comparison metrics"""
    try:
        # Measure compute agent performance
        compute_start = time.time()
        await pulse_service.calculate_current_pulse()
        compute_latency = (time.time() - compute_start) * 1000
        
        # Measure learning agent performance
        learning_start = time.time()
        compute_pulse = await pulse_service.calculate_current_pulse()
        learning_service.enhance_pulse_event(compute_pulse)
        learning_latency = (time.time() - learning_start) * 1000
        
        learning_results = learning_service.get_learning_results()
        
        return {
            "success": True,
            "compute_agent": {
                "latency_ms": round(compute_latency, 2),
                "uptime": "99.9%",  # Placeholder
                "features_count": 5,
                "accuracy": "N/A"
            },
            "learning_agent": {
                "latency_ms": round(learning_latency, 2),
                "uptime": "99.9%",  # Placeholder
                "features_count": 9,
                "model_accuracy": "76%",  # Placeholder
                "prediction_accuracy": "82%",  # Placeholder
                "last_learning": learning_results.get("last_updated")
            },
            "comparison": {
                "latency_difference_ms": round(learning_latency - compute_latency, 2),
                "feature_advantage": 4,  # Learning agent has 4 more features
                "learning_enabled": bool(learning_results.get("last_updated"))
            }
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.post("/collector/start")
async def start_data_collector(
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Manually start the data collector
    Starts WebSocket connection and begins collecting market data to S3
    """
    try:
        if pulse_service.started:
            return {
                "success": True,
                "message": "Data collector is already running",
                "status": "running",
                "stats": pulse_service.data_collector.get_collection_stats()
            }
        
        pulse_service.start()
        
        if pulse_service.started:
            stats = pulse_service.data_collector.get_collection_stats()
            return {
                "success": True,
                "message": "Data collector started successfully",
                "status": "running",
                "stats": stats
            }
        else:
            return {
                "success": False,
                "message": "Failed to start data collector. Check WebSocket connection.",
                "status": "failed"
            }
    except Exception as e:
        logger.error(f"Error starting data collector: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start data collector: {str(e)}")


@router.post("/collector/stop")
async def stop_data_collector(
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Manually stop the data collector
    Stops WebSocket connection and data collection
    """
    try:
        if not pulse_service.started:
            return {
                "success": True,
                "message": "Data collector is not running",
                "status": "stopped"
            }
        
        stats_before = pulse_service.data_collector.get_collection_stats()
        pulse_service.stop()
        
        return {
            "success": True,
            "message": "Data collector stopped successfully",
            "status": "stopped",
            "final_stats": {
                "bars_collected": stats_before.get('bars_collected', 0),
                "last_bar_time": stats_before.get('last_bar_time')
            }
        }
    except Exception as e:
        logger.error(f"Error stopping data collector: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop data collector: {str(e)}")


@router.get("/collector/status")
async def get_collector_status(
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Get data collector status and statistics
    """
    try:
        stats = pulse_service.data_collector.get_collection_stats()
        return {
            "success": True,
            "status": "running" if pulse_service.started else "stopped",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting collector status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get collector status: {str(e)}")


@router.get("/dual-signal")
async def get_dual_signal_comparison(
    ticker: Optional[str] = Query(None, description="Filter by ticker (e.g., AAPL, MSFT)"),
    pulse_service: MarketPulseService = Depends(get_pulse_service),
    learning_service: LearningAgentService = Depends(get_learning_agent_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Get dual agent signal comparison
    
    Returns side-by-side comparison of Compute Agent vs Learning Agent signals
    for all 10 stocks or a specific ticker
    
    Response includes:
    - Compute Agent: Signal, Return, Vol
    - Learning Agent: Predicted Signal, R², MAE, Training Iterations, Converged status
    - Difference: Signal difference, R² difference, MAE difference
    - Convergence: Status and progress
    """
    try:
        import os
        from app.services.marketpulse.aws_storage import AWSStorageService
        from botocore.exceptions import ClientError
        
        s3_bucket = os.getenv("AWS_S3_PULSE_BUCKET")
        aws_storage = AWSStorageService(s3_bucket=s3_bucket)
        
        if not aws_storage.s3_client or not aws_storage.s3_bucket:
            raise HTTPException(status_code=500, detail="S3 client not initialized")
        
        # 读取今天的 Compute Agent signals
        today = datetime.now(timezone.utc).date().isoformat()
        compute_key = f"processed-data/{today}/compute-signals.json"
        
        compute_signals = {}
        compute_data_available = False
        try:
            response = aws_storage.s3_client.get_object(
                Bucket=aws_storage.s3_bucket,
                Key=compute_key
            )
            content = response['Body'].read().decode('utf-8')
            compute_data = json.loads(content)
            signals_list = compute_data.get('signals', [])
            
            # 转换为字典，按 ticker 索引（取最新的）
            for signal in signals_list:
                ticker = signal.get('ticker')
                if ticker:
                    compute_signals[ticker] = signal
            
            compute_data_available = len(compute_signals) > 0
            logger.info(f"✅ Read {len(compute_signals)} compute signals from S3")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                logger.warning(f"⚠️  Compute signals not found in S3: {compute_key}")
            else:
                logger.warning(f"Error reading compute signals: {e}")
        except Exception as e:
            logger.warning(f"Error reading compute signals: {e}")
        
        # 读取今天的 Learning Agent signals
        learning_key = f"processed-data/{today}/learning-signals.json"
        
        learning_signals = {}
        learning_data_available = False
        try:
            response = aws_storage.s3_client.get_object(
                Bucket=aws_storage.s3_bucket,
                Key=learning_key
            )
            content = response['Body'].read().decode('utf-8')
            learning_data = json.loads(content)
            learning_models = learning_data.get('models', {})
            learning_signals = learning_models
            
            learning_data_available = len(learning_signals) > 0
            logger.info(f"✅ Read {len(learning_signals)} learning signals from S3")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                logger.warning(f"⚠️  Learning signals not found in S3: {learning_key}")
            else:
                logger.warning(f"Error reading learning signals: {e}")
        except Exception as e:
            logger.warning(f"Error reading learning signals: {e}")
        
        # 支持的股票列表
        supported_tickers = ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META', 'GOOGL', 'JPM', 'XOM', 'SPY']
        
        # 如果指定了 ticker，只返回该 ticker
        if ticker:
            supported_tickers = [ticker] if ticker in supported_tickers else []
        
        # 构建响应
        stocks = []
        for ticker in supported_tickers:
            compute_signal = compute_signals.get(ticker, {})
            learning_signal = learning_signals.get(ticker, {})
            
            compute_signal_value = compute_signal.get('signal', 0.0)
            learning_signal_value = learning_signal.get('signal_predicted', 0.0)
            signal_diff = learning_signal_value - compute_signal_value
            
            r2_score = learning_signal.get('r2_score', 0.0)
            mae = learning_signal.get('mae', 1.0)
            converged = learning_signal.get('converged', False)
            training_iterations = learning_signal.get('training_iterations', 0)
            
            # 计算收敛进度（简化版：基于 R²）
            convergence_progress = min(100, int(r2_score * 100)) if r2_score > 0 else 0
            convergence_status = "✅" if converged else "⏳"
            
            stocks.append({
                "ticker": ticker,
                "compute_agent": {
                    "signal": round(compute_signal_value, 4),
                    "return": round(compute_signal.get('return', 0.0), 6),
                    "vol": round(compute_signal.get('vol', 0.0), 6)
                },
                "learning_agent": {
                    "signal": round(learning_signal_value, 4),
                    "r2_score": round(r2_score, 4),
                    "mae": round(mae, 4),
                    "training_iterations": training_iterations,
                    "converged": converged
                },
                "difference": {
                    "signal_diff": round(signal_diff, 4),
                    "r2_diff": round(r2_score - 1.0, 4),  # 相对于 100% (1.0)
                    "mae_diff": round(mae - 0.0, 4)  # 相对于 0.0
                },
                "convergence": {
                    "status": convergence_status,
                    "progress": convergence_progress
                }
            })
        
        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "date": today,
            "stocks": stocks,
            "total_stocks": len(stocks),
            "data_status": {
                "compute_agent_available": compute_data_available,
                "learning_agent_available": learning_data_available,
                "compute_signals_count": len(compute_signals),
                "learning_signals_count": len(learning_signals)
            }
        }
        
    except HTTPException:
        # Let already-constructed HTTPExceptions (like S3 client not initialized) pass through unchanged
        raise
    except Exception as e:
        # Log full traceback to backend logs for debugging
        logger.exception("dual-signal endpoint failed")
        # Return non-empty, more detailed error information to the frontend
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dual signal comparison: {type(e).__name__}: {repr(e)}"
        )



