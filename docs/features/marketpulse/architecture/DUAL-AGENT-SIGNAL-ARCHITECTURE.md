# Dual Agent Signal Architecture

## 🎯 设计方案总结

### 1. Compute Agent 公式（已确认）

```
Return = (Close - Open) / Open
Vol = Std(Return over last 20 bars) + 1e-6
Signal = Return / Vol
```

**说明**：
- `Return`: 当前 bar 的收益率（开收盘价差）
- `Vol`: 过去 20 个 bars 的收益率标准差 + 小常数（防止除零）
- `Signal`: 标准化信号（Return 相对于波动率的倍数）

### 2. Learning Agent 设计

**模型**：线性回归 / Ridge（先用简单模型）

**特征**：8 个特征
- `ret_1`: 前 1 个 bar 的 Return
- `ret_2`: 前 2 个 bar 的 Return
- `range`: 当前 bar 的 (High - Low) / Open
- `vol_norm`: 当前 Vol 相对于历史平均的标准化值
- `rolling_mean_5`: 过去 5 个 bars 的 Return 均值
- `rolling_mean_10`: 过去 10 个 bars 的 Return 均值
- `rolling_std_5`: 过去 5 个 bars 的 Return 标准差
- `rolling_std_10`: 过去 10 个 bars 的 Return 标准差

**训练频率**：每 1 小时

**目标**：预测 Compute Agent 的 Signal

**评估指标**：
- R² Score（决定系数）
- MAE（平均绝对误差）
- 收敛标准：MAE < 0.1 持续 50 个 bars 或 R² > 0.9 持续 1 天

### 3. 股票列表（10 个）

```
AAPL, MSFT, AMZN, NVDA, TSLA, META, GOOGL, JPM, XOM, SPY
```

### 4. Dashboard 表格结构

| Metric | Description & Formula | Compute Agent | Learning Agent | Difference | Convergence |
|--------|---------------------|---------------|----------------|------------|-------------|
| Signal | Return = (Close-Open)/Open<br>Vol = Std(Return, 20) + 1e-6<br>Signal = Return/Vol | 0.52 | 0.48 | 0.04 | 85% |
| Accuracy (R²) | R² score vs Compute Agent | 100% | 85% | -15% | ⏳ |
| MAE | Mean Absolute Error | 0.0 | 0.08 | +0.08 | ⏳ |
| Training Iterations | Number of training runs | - | 24 | - | - |
| Converged | MAE < 0.1 & R² > 0.9 | ✅ | ⏳ | - | - |

### 5. 收敛标准

- **MAE < 0.1** 持续 50 个 bars
- **或 R² > 0.9** 持续 1 天

**UI 显示**：
- ✅ Converged（已收敛）
- ⏳ Not yet（未收敛）

---

## 🏗️ 架构设计

### 数据流

```
1. Data Collector (WebSocket)
   ↓
   Raw bars → S3 (raw-data/YYYY-MM-DD/ticker/timestamp.json)
   
2. Compute Agent Lambda (每 5 分钟触发)
   ↓
   读取 raw-data/ → 计算 Signal → 存储到 processed-data/YYYY-MM-DD/compute-signals.json
   
3. Learning Agent Lambda (每 1 小时触发)
   ↓
   读取 processed-data/ → 提取特征 → 训练模型 → 预测 Signal → 存储到 processed-data/YYYY-MM-DD/learning-signals.json
   
4. API Endpoint (/api/v1/market-pulse/dual-signal)
   ↓
   读取两个 Agent 的结果 → 计算对比指标 → 返回 JSON
   
5. Dashboard (Excel 风格表格)
   ↓
   显示 10 个股票的对比表格
```

### S3 数据结构

```
raw-data/
  YYYY-MM-DD/
    ticker/
      timestamp.json

processed-data/
  YYYY-MM-DD/
    compute-signals.json      # Compute Agent 结果
    learning-signals.json      # Learning Agent 结果
    learning-models.json       # 模型信息（R², MAE, 收敛状态）
```

### Compute Agent Lambda

**触发**：EventBridge 每 5 分钟

**处理流程**：
1. 读取今天所有 ticker 的 raw-data
2. 对每个 ticker 计算 Signal（使用最新 bar）
3. 存储到 `processed-data/YYYY-MM-DD/compute-signals.json`

**输出格式**：
```json
{
  "date": "2026-01-26",
  "processed_at": "2026-01-26T10:00:00Z",
  "signals": [
    {
      "ticker": "AAPL",
      "timestamp": "2026-01-26T10:00:00Z",
      "return": 0.0012,
      "vol": 0.0023,
      "signal": 0.52
    },
    ...
  ]
}
```

### Learning Agent Lambda

**触发**：EventBridge 每 1 小时

**处理流程**：
1. 读取过去 N 小时（至少 20 个 bars）的 compute-signals
2. 提取特征（8 个特征）
3. 训练线性回归 / Ridge 模型
4. 预测当前 Signal
5. 计算 R² 和 MAE
6. 检查收敛状态
7. 存储结果到 `processed-data/YYYY-MM-DD/learning-signals.json`

**输出格式**：
```json
{
  "date": "2026-01-26",
  "processed_at": "2026-01-26T10:00:00Z",
  "models": {
    "AAPL": {
      "signal_predicted": 0.48,
      "signal_actual": 0.52,
      "r2_score": 0.85,
      "mae": 0.08,
      "training_iterations": 24,
      "converged": false,
      "features": {
        "ret_1": 0.001,
        "ret_2": -0.0005,
        ...
      }
    },
    ...
  }
}
```

### API 端点

**GET /api/v1/market-pulse/dual-signal**

**查询参数**：
- `ticker` (可选): 过滤特定股票

**响应格式**：
```json
{
  "success": true,
  "timestamp": "2026-01-26T10:00:00Z",
  "stocks": [
    {
      "ticker": "AAPL",
      "compute_agent": {
        "signal": 0.52,
        "return": 0.0012,
        "vol": 0.0023
      },
      "learning_agent": {
        "signal": 0.48,
        "r2_score": 0.85,
        "mae": 0.08,
        "training_iterations": 24,
        "converged": false
      },
      "difference": {
        "signal_diff": 0.04,
        "r2_diff": -0.15,
        "mae_diff": 0.08
      },
      "convergence": {
        "status": "⏳",
        "progress": 85
      }
    },
    ...
  ]
}
```

### Dashboard 设计

**Excel 风格表格**，显示 10 个股票的对比：

| Ticker | Compute Signal | Learning Signal | Difference | R² | MAE | Iterations | Converged |
|--------|---------------|----------------|-------------|-----|-----|------------|-----------|
| AAPL   | 0.52          | 0.48           | 0.04        | 85% | 0.08 | 24         | ⏳        |
| MSFT   | 0.35          | 0.32           | 0.03        | 92% | 0.06 | 18         | ✅        |
| ...    | ...           | ...            | ...         | ... | ... | ...        | ...       |

**颜色编码**：
- 收敛：绿色 ✅
- 未收敛：黄色 ⏳
- R² > 0.9：绿色背景
- R² < 0.7：红色背景

---

## 🚀 实现计划

1. ✅ 创建架构文档（本文档）
2. ⏳ 更新 Compute Agent Lambda（新公式）
3. ⏳ 更新 Learning Agent Lambda（监督学习）
4. ⏳ 创建 API 端点（对比数据）
5. ⏳ 创建 Dashboard（Excel 风格表格）
6. ⏳ 更新数据收集器（10 个股票）

---

## 📝 注意事项

1. **数据一致性**：确保 Compute Agent 和 Learning Agent 使用相同的数据源
2. **特征工程**：8 个特征需要从历史 bars 中提取
3. **模型持久化**：Learning Agent 需要保存模型参数（可选，简化版可以每次重新训练）
4. **收敛检测**：需要维护历史状态（过去 50 个 bars 的 MAE 或过去 1 天的 R²）
5. **错误处理**：当数据不足时（< 20 bars），Learning Agent 应该跳过训练
