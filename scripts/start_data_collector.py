#!/usr/bin/env python3
"""
手动启动 Market Pulse 数据收集器
将市场数据写入 S3

用法:
    python scripts/start_data_collector.py              # 启动并持续运行
    python scripts/start_data_collector.py --duration 60  # 运行 60 秒后停止
    python scripts/start_data_collector.py --tickers AAPL,MSFT  # 只收集指定 tickers
"""
import os
import sys
import time
import signal
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instance
service = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("\n🛑 收到停止信号，正在关闭数据收集器...")
    if service:
        try:
            service.stop()
            stats = service.data_collector.get_collection_stats()
            logger.info(f"✅ 数据收集器已停止")
            logger.info(f"   总共收集: {stats.get('bars_collected', 0)} 条数据")
        except Exception as e:
            logger.error(f"停止数据收集器时出错: {e}")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description='启动 Market Pulse 数据收集器'
    )
    parser.add_argument(
        '--duration',
        type=int,
        help='运行时长（秒），默认持续运行直到 Ctrl+C',
        default=None
    )
    parser.add_argument(
        '--tickers',
        type=str,
        help='要收集的股票代码（逗号分隔），默认: 所有支持的 tickers',
        default=None
    )
    parser.add_argument(
        '--delayed',
        action='store_true',
        help='使用延迟 WebSocket（15分钟延迟）',
        default=None  # None means check environment variable
    )
    parser.add_argument(
        '--realtime',
        action='store_true',
        help='强制使用实时数据（需要付费计划）',
        default=False
    )
    
    args = parser.parse_args()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 检查环境变量
    polygon_api_key = os.getenv("POLYGON_API_KEY")
    s3_bucket = os.getenv("AWS_S3_PULSE_BUCKET")
    
    if not polygon_api_key:
        logger.error("❌ POLYGON_API_KEY 环境变量未设置")
        logger.error("   设置方法: export POLYGON_API_KEY=your-api-key")
        sys.exit(1)
    
    if not s3_bucket:
        logger.error("❌ AWS_S3_PULSE_BUCKET 环境变量未设置")
        logger.error("   设置方法: export AWS_S3_PULSE_BUCKET=your-bucket-name")
        sys.exit(1)
    
    # 解析 tickers
    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
    
    # 确定是否使用延迟数据
    # 优先级: --realtime > --delayed > 环境变量 > 默认延迟
    use_delayed = True  # 默认使用延迟数据（免费）
    if args.realtime:
        use_delayed = False
        logger.warning("⚠️  使用实时数据模式（需要付费计划）")
    elif args.delayed is not None:
        use_delayed = args.delayed
    else:
        # 检查环境变量
        env_delayed = os.getenv("POLYGON_USE_DELAYED_WS", "").lower()
        if env_delayed in ("true", "1", "yes"):
            use_delayed = True
        elif env_delayed in ("false", "0", "no"):
            use_delayed = False
    
    logger.info("=" * 80)
    logger.info("🚀 启动 Market Pulse 数据收集器")
    logger.info("=" * 80)
    logger.info(f"S3 Bucket: {s3_bucket}")
    logger.info(f"数据模式: {'延迟数据 (15分钟延迟)' if use_delayed else '实时数据 (需要付费计划)'}")
    if tickers:
        logger.info(f"收集 Tickers: {', '.join(tickers)}")
    else:
        logger.info("收集所有支持的 Tickers")
    logger.info("")
    
    # 导入服务
    try:
        from app.services.marketpulse.pulse_service import MarketPulseService
        
        global service
        service = MarketPulseService(
            polygon_api_key=polygon_api_key,
            s3_bucket=s3_bucket,
            tickers=tickers,
            use_delayed_ws=use_delayed
        )
        
        # 启动数据收集器
        logger.info("📡 正在启动 WebSocket 连接...")
        service.start()
        
        if not service.started:
            logger.error("❌ 无法启动数据收集器")
            logger.error("   请检查:")
            logger.error("   1. POLYGON_API_KEY 是否正确")
            logger.error("   2. 网络连接是否正常")
            logger.error("   3. Polygon WebSocket 服务是否可用")
            sys.exit(1)
        
        logger.info("✅ 数据收集器已启动")
        logger.info("   数据将自动写入 S3")
        logger.info("   按 Ctrl+C 停止")
        logger.info("")
        
        # 显示初始统计
        stats = service.data_collector.get_collection_stats()
        logger.info(f"📊 初始状态:")
        logger.info(f"   WebSocket 连接: {'✅' if stats.get('websocket_connected') else '❌'}")
        logger.info(f"   已收集数据条数: {stats.get('bars_collected', 0)}")
        logger.info("")
        
        # 运行指定时长或持续运行
        if args.duration:
            logger.info(f"⏱️  将运行 {args.duration} 秒...")
            start_time = time.time()
            
            while time.time() - start_time < args.duration:
                time.sleep(5)  # 每 5 秒检查一次
                stats = service.data_collector.get_collection_stats()
                if stats.get('bars_collected', 0) > 0 and stats.get('bars_collected', 0) % 10 == 0:
                    logger.info(f"📊 已收集 {stats.get('bars_collected', 0)} 条数据...")
            
            logger.info(f"⏱️  运行时间已到，正在停止...")
            service.stop()
            
            # 显示最终统计
            final_stats = service.data_collector.get_collection_stats()
            logger.info("")
            logger.info("=" * 80)
            logger.info("📊 最终统计")
            logger.info("=" * 80)
            logger.info(f"总共收集: {final_stats.get('bars_collected', 0)} 条数据")
            if final_stats.get('last_bar_time'):
                logger.info(f"最后数据时间: {final_stats.get('last_bar_time')}")
        else:
            logger.info("🔄 持续运行中... (按 Ctrl+C 停止)")
            # 持续运行，定期显示统计
            last_count = 0
            while True:
                time.sleep(30)  # 每 30 秒显示一次统计
                stats = service.data_collector.get_collection_stats()
                current_count = stats.get('bars_collected', 0)
                
                if current_count > last_count:
                    logger.info(f"📊 已收集 {current_count} 条数据 (新增 {current_count - last_count} 条)")
                    last_count = current_count
                
                # 检查 WebSocket 连接状态
                if not stats.get('websocket_connected', False):
                    logger.warning("⚠️  WebSocket 连接已断开，尝试重新连接...")
                    try:
                        service.stop()
                        time.sleep(2)
                        service.start()
                        if service.started:
                            logger.info("✅ WebSocket 已重新连接")
                    except Exception as e:
                        logger.error(f"❌ 重新连接失败: {e}")
        
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        logger.error(f"❌ 启动数据收集器时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
