#!/usr/bin/env python3
"""
测试双 Agent 系统是否正常运行
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1/market-pulse"

def test_compute_agent():
    """测试计算 Agent"""
    print("=" * 60)
    print("🧪 测试计算 Agent")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/compute-agent", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ Agent 类型: {data.get('agent_type')}")
        print(f"✅ 功能数量: {len(data.get('features', []))}")
        print(f"✅ 数据时间戳: {data.get('data', {}).get('timestamp', 'N/A')}")
        print(f"✅ Stress: {data.get('data', {}).get('stress', 'N/A')}")
        print(f"✅ Regime: {data.get('data', {}).get('regime', 'N/A')}")
        print()
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False

def test_learning_agent():
    """测试学习 Agent"""
    print("=" * 60)
    print("🧪 测试学习 Agent")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/learning-agent", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ Agent 类型: {data.get('agent_type')}")
        print(f"✅ 功能数量: {len(data.get('features', []))}")
        print(f"✅ 数据时间戳: {data.get('data', {}).get('timestamp', 'N/A')}")
        print(f"✅ Stress: {data.get('data', {}).get('stress', 'N/A')}")
        print(f"✅ Regime: {data.get('data', {}).get('regime', 'N/A')}")
        
        # 检查增强功能
        anomalies = data.get('data', {}).get('anomalies', [])
        prediction = data.get('data', {}).get('prediction', {})
        insights = data.get('data', {}).get('insights', [])
        
        print(f"✅ 异常检测: {len(anomalies)} 个异常")
        if anomalies:
            print(f"   - {anomalies}")
        
        print(f"✅ 预测功能: {'有' if prediction else '无'}")
        if prediction:
            print(f"   - 下一小时压力: {prediction.get('next_hour_stress', 'N/A')}")
            print(f"   - 置信度: {prediction.get('confidence', 'N/A')}")
        
        print(f"✅ 洞察: {len(insights)} 条")
        if insights:
            for i, insight in enumerate(insights[:3], 1):
                print(f"   {i}. {insight}")
        
        # 检查学习元数据
        meta = data.get('learning_metadata', {})
        print(f"✅ 学习元数据:")
        print(f"   - 最后更新: {meta.get('last_updated', 'N/A')}")
        print(f"   - 有基准: {meta.get('has_baseline', False)}")
        print(f"   - 有模式: {meta.get('has_patterns', False)}")
        print(f"   - 有模型: {meta.get('has_model', False)}")
        print()
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False

def test_compare():
    """测试双 Agent 对比"""
    print("=" * 60)
    print("🧪 测试双 Agent 对比")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/compare", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 时间戳: {data.get('timestamp', 'N/A')}")
        print()
        
        # 计算 Agent 信息
        compute = data.get('compute_agent', {})
        print("📊 计算 Agent:")
        print(f"   - 延迟: {compute.get('latency_ms', 'N/A')} ms")
        print(f"   - 功能数: {len(compute.get('features', []))}")
        print(f"   - Stress: {compute.get('data', {}).get('stress', 'N/A')}")
        print()
        
        # 学习 Agent 信息
        learning = data.get('learning_agent', {})
        print("📊 学习 Agent:")
        print(f"   - 延迟: {learning.get('latency_ms', 'N/A')} ms")
        print(f"   - 功能数: {len(learning.get('features', []))}")
        print(f"   - Stress: {learning.get('data', {}).get('stress', 'N/A')}")
        print(f"   - 异常数: {len(learning.get('data', {}).get('anomalies', []))}")
        print(f"   - 有预测: {'是' if learning.get('data', {}).get('prediction') else '否'}")
        print()
        
        # 对比信息
        comparison = data.get('comparison', {})
        print("📊 对比结果:")
        print(f"   - 延迟差异: {comparison.get('performance', {}).get('total_latency_ms', 'N/A')} ms")
        print(f"   - 功能优势: {comparison.get('value_difference', {}).get('has_anomalies', False)} (异常检测)")
        print(f"   - 功能优势: {comparison.get('value_difference', {}).get('has_prediction', False)} (预测)")
        print()
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False

def test_performance():
    """测试性能对比"""
    print("=" * 60)
    print("🧪 测试性能对比")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/performance", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ 状态码: {response.status_code}")
        print()
        
        compute = data.get('compute_agent', {})
        learning = data.get('learning_agent', {})
        comparison = data.get('comparison', {})
        
        print("⚡ 计算 Agent 性能:")
        print(f"   - 延迟: {compute.get('latency_ms', 'N/A')} ms")
        print(f"   - 可用性: {compute.get('uptime', 'N/A')}")
        print(f"   - 功能数: {compute.get('features_count', 'N/A')}")
        print()
        
        print("🧠 学习 Agent 性能:")
        print(f"   - 延迟: {learning.get('latency_ms', 'N/A')} ms")
        print(f"   - 可用性: {learning.get('uptime', 'N/A')}")
        print(f"   - 功能数: {learning.get('features_count', 'N/A')}")
        print(f"   - 模型准确率: {learning.get('model_accuracy', 'N/A')}")
        print(f"   - 预测准确率: {learning.get('prediction_accuracy', 'N/A')}")
        print(f"   - 最后学习: {learning.get('last_learning', 'N/A')}")
        print()
        
        print("📊 性能对比:")
        print(f"   - 延迟差异: {comparison.get('latency_difference_ms', 'N/A')} ms")
        print(f"   - 功能优势: {comparison.get('feature_advantage', 'N/A')} 个")
        print(f"   - 学习已启用: {comparison.get('learning_enabled', False)}")
        print()
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🚀 双 Agent 系统测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API 地址: {API_BASE}")
    print()
    
    results = {
        "compute_agent": test_compute_agent(),
        "learning_agent": test_learning_agent(),
        "compare": test_compare(),
        "performance": test_performance()
    }
    
    print("=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s}: {status}")
    
    print()
    all_passed = all(results.values())
    if all_passed:
        print("🎉 所有测试通过！双 Agent 系统运行正常！")
    else:
        print("⚠️  部分测试失败，请检查上述错误信息")
    print()

if __name__ == "__main__":
    main()
