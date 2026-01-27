# Market Pulse 分层架构设计 v3（极简版）

> 基于第一性原理：删除一切不必要的部分，只保留核心功能

**设计原则**：参考 [设计原则文档](./design-principles.md)

---

## 核心价值

Market Pulse 只做三件事：
1. **采集**：实时市场数据 → S3
2. **计算**：Pulse 指标（5个）
3. **展示**：今日事件

---

## 极简架构（3层）

```
┌─────────────────────────────────┐
│ Layer 1: Data Collection        │
│ WebSocket → S3 (raw-data/)      │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│ Layer 2: Processing (Lambda)    │
│ 读取 raw-data/ → 计算指标 →      │
│ 写入 processed-data/            │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│ Layer 3: API + Frontend         │
│ 读取 processed-data/ → 展示      │
└─────────────────────────────────┘
```

---

## Layer 1: Data Collection（数据采集层）

### 职责
- 连接 Polygon WebSocket
- 接收 bar 数据
- **5分钟窗口聚合**（避免小文件）
- 写入 S3 (raw-data/)

### 组件
- `MarketPulsePolygonService` - WebSocket 连接
- `MarketPulseDataCollector` - 数据收集和聚合

### 输出
- `raw-data/v1/date=YYYY-MM-DD/ticker=SPY/bar_5m_HH-MM.jsonl.gz`

### 删除的功能
- ❌ 数据验证和清洗（Lambda 处理）
- ❌ 多数据源支持（只支持 Polygon）
- ❌ 实时计算（只存储，不计算）

---

## Layer 2: Processing（处理层）

### 职责
- 读取 raw-data/
- **只计算 5 个 Pulse 指标**：
  1. Stress Index（压力指数）
  2. Velocity（价格速度）
  3. Volume Surge（成交量激增）
  4. Volatility（波动率）
  5. Breadth（广度）
- 写入 processed-data/

### 组件
- AWS Lambda Agent
- EventBridge 触发（每 5 分钟）

### 输出
- `processed-data/v1/date=YYYY-MM-DD/pulse-events.jsonl.gz`

### 删除的功能
- ❌ 学习模式（没人用）
- ❌ 生成 Insights（没人用）
- ❌ 每日总结（用户可以直接看事件）
- ❌ 复杂的事件检测（只计算指标）

---

## Layer 3: API + Frontend（接口和展示层）

### 职责
- 读取 processed-data/
- 返回 JSON 给前端
- 前端展示今日事件

### 组件
- FastAPI（2 个端点）
- Frontend（JavaScript + Chart.js）

### API 端点（只保留 2 个）

#### 1. GET /api/v1/market-pulse/current
返回最新的 pulse 事件

```json
{
  "timestamp": "2026-01-26T10:05:00Z",
  "stress": 0.65,
  "regime": "high_volatility",
  "velocity": 1.2,
  "volume_surge": {"surge_ratio": 2.1, "is_surge": true},
  "volatility": 1.5,
  "breadth": "positive"
}
```

#### 2. GET /api/v1/market-pulse/events/today
返回今天所有的 pulse 事件

```json
{
  "events": [
    {"timestamp": "...", "stress": 0.65, ...},
    {"timestamp": "...", "stress": 0.72, ...}
  ],
  "count": 214
}
```

### 删除的端点
- ❌ `GET /history` - 历史数据
- ❌ `GET /summary` - 每日总结
- ❌ `GET /insights` - Agent insights
- ❌ `GET /collection/stats` - 采集统计
- ❌ `POST /calculate` - 手动触发

---

## 数据流（极简版）

```
1. WebSocket → bar 数据（实时）
   ↓
2. Data Collector → 5分钟窗口聚合 → S3 (raw-data/)
   ↓
3. EventBridge (每5分钟) → Lambda
   ↓
4. Lambda → 读取 raw-data/ → 计算5个指标 → 写入 processed-data/
   ↓
5. API → 读取 processed-data/ → 返回 JSON
   ↓
6. Frontend → 显示今日事件
```

---

## S3 结构（极简版）

```
s3://bucket/
├── raw-data/v1/
│   └── date=2026-01-26/ticker=SPY/bar_5m_10-00.jsonl.gz
│   └── date=2026-01-26/ticker=SPY/bar_5m_10-05.jsonl.gz
│   └── ...
└── processed-data/v1/
    └── date=2026-01-26/pulse-events.jsonl.gz
```

**删除的结构**：
- ❌ `daily-summaries/` - 不需要总结
- ❌ `insights/` - 不需要 insights
- ❌ `_manifest.json` - 暂时不需要（未来可以加）

---

## 代码结构（极简版）

```
app/services/marketpulse/
├── polygon_service.py      # WebSocket 连接（保留）
├── data_collector.py       # 数据采集和聚合（保留，简化）
├── aws_storage.py          # S3 存储（保留，删除 DynamoDB）
└── pulse_service.py        # 业务逻辑（简化，合并 AgentReader）

app/api/v1/endpoints/
└── market_pulse.py         # 只保留 2 个端点

docs/features/marketpulse/
└── aws-lambda-compute-agent.py     # 简化，只计算指标
```

**删除的文件**：
- ❌ `agent_reader.py` - 合并到 `pulse_service.py`
- ❌ `pulse_calculator.py` - 删除 fallback

---

## 环境变量（极简版）

**只保留必要的**：
```bash
POLYGON_API_KEY=xxx
AWS_S3_PULSE_BUCKET=xxx
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
```

**删除的**：
- ❌ `AWS_DYNAMODB_PULSE_TABLE` - 不需要 DynamoDB
- ❌ `POLYGON_USE_DELAYED_WS` - 默认实时，不需要配置

---

## 代码减少对比

| 组件 | v2 版本 | v3 版本 | 减少 |
|------|---------|---------|------|
| `pulse_service.py` | 198 | ~100 | -50% |
| `agent_reader.py` | 230 | 0 (合并) | -100% |
| `pulse_calculator.py` | 391 | 0 (删除) | -100% |
| `aws_storage.py` | 439 | ~200 | -55% |
| `market_pulse.py` (API) | 260 | ~80 | -69% |
| `aws-lambda-compute-agent.py` | 677 | ~300 | -56% |
| **总计** | **~2195** | **~680** | **-69%** |

---

## 功能对比

| 功能 | v2 版本 | v3 版本 |
|------|---------|---------|
| 实时数据采集 | ✅ | ✅ |
| Pulse 指标计算 | ✅ | ✅ |
| 今日事件展示 | ✅ | ✅ |
| 历史数据查询 | ✅ | ❌ 删除 |
| 每日总结 | ✅ | ❌ 删除 |
| Insights | ✅ | ❌ 删除 |
| Fallback 计算 | ✅ | ❌ 删除 |
| DynamoDB | ✅ (可选) | ❌ 删除 |
| Collection Stats | ✅ | ❌ 删除 |

---

## 实施步骤

### Phase 1: 删除（立即）
1. ❌ 删除 `PulseCalculator` fallback
2. ❌ 删除 DynamoDB 支持
3. ❌ 删除历史数据查询
4. ❌ 删除 Insights 和 Summary

### Phase 2: 简化（接下来）
5. 合并 `AgentReader` 到 `Service`
6. 简化 API 端点（只保留 2 个）
7. 简化 Lambda Agent（只计算指标）

### Phase 3: 优化（最后）
8. 实现 5 分钟窗口聚合
9. 优化 S3 存储结构
10. 添加 TTL 缓存（可选）

---

## 验证标准

每个删除的决定都要验证：
- ✅ **如果删除后系统无法工作** → 保留
- ✅ **如果删除后没人抱怨** → 删除
- ✅ **如果删除后可以快速加回来** → 删除

**目标**：代码减少 70%，功能保留 100% 核心价值

---

## 相关文档

- [设计原则](./design-principles.md) - 第一性原理设计方法
- [架构概述](./architecture.md) - 架构概览
- [快速启动](./market-pulse-quickstart.md) - 快速上手
