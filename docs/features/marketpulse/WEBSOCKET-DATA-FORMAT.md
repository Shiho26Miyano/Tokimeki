# WebSocket 数据格式说明

## 📡 Polygon.io WebSocket 返回的数据

### 1. 原始 WebSocket 消息格式

Polygon.io WebSocket 返回两种类型的消息：

#### A. 认证消息 (Authentication)
```json
[
  {
    "ev": "status",
    "status": "auth_success",
    "message": "authenticated"
  }
]
```

#### B. 聚合数据消息 (Aggregate Bar)
```json
[
  {
    "ev": "AM",  // Event type: "AM" = per-minute aggregate, "A" = per-second
    "sym": "SPY",  // Ticker symbol
    "v": 1234567,  // Volume
    "av": 1234567,  // Accumulated volume (for the day)
    "op": 450.25,  // Open price
    "vw": 450.30,  // Volume-weighted average price (VWAP)
    "o": 450.25,   // Open price (same as op)
    "c": 450.50,   // Close price
    "h": 450.75,   // High price
    "l": 450.20,   // Low price
    "a": 450.30,   // Average price
    "z": 1234567,  // Total volume (same as v)
    "s": 1234567890,  // Start timestamp (Unix milliseconds)
    "e": 1234567890   // End timestamp (Unix milliseconds)
  }
]
```

---

## 🔄 数据转换流程

### Step 1: WebSocket 接收原始消息
**位置**: `polygon_service.py` → `_on_message()`

原始消息可能是：
- 单个对象: `{"ev": "AM", "sym": "SPY", ...}`
- 数组: `[{"ev": "AM", ...}, ...]`

### Step 2: 解析聚合事件
**位置**: `polygon_service.py` → `_handle_aggregate()`

解析后的 bar 数据格式：
```python
{
    "ticker": "SPY",
    "timestamp": "2026-01-26T18:30:00Z",  # ISO format
    "open": 450.25,
    "high": 450.75,
    "low": 450.20,
    "close": 450.50,
    "volume": 1234567,
    "vwap": 450.30
}
```

### Step 3: 存储到 S3
**位置**: `data_collector.py` → `_on_raw_bar_received()`

最终存储到 S3 的格式：
```json
{
  "source": "polygon_websocket",
  "ticker": "SPY",
  "timestamp": "2026-01-26T18:30:00Z",
  "bar_data": {
    "open": 450.25,
    "high": 450.75,
    "low": 450.20,
    "close": 450.50,
    "volume": 1234567,
    "vwap": 450.30
  },
  "collected_at": "2026-01-26T18:30:01.123Z"
}
```

**S3 存储路径**: `raw-data/YYYY-MM-DD/ticker/timestamp.json`

---

## 📊 字段说明

### WebSocket 原始字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `ev` | string | 事件类型: "AM" (每分钟), "A" (每秒) |
| `sym` | string | 股票代码 (ticker symbol) |
| `v` | number | 成交量 (volume) |
| `av` | number | 累计成交量 (accumulated volume for the day) |
| `op` | number | 开盘价 (open price) |
| `o` | number | 开盘价 (open, 同 op) |
| `c` | number | 收盘价 (close price) |
| `h` | number | 最高价 (high price) |
| `l` | number | 最低价 (low price) |
| `a` | number | 平均价 (average price) |
| `vw` | number | 成交量加权平均价 (VWAP) |
| `z` | number | 总成交量 (total volume, 同 v) |
| `s` | number | 开始时间戳 (Unix milliseconds) |
| `e` | number | 结束时间戳 (Unix milliseconds) |

### 转换后的 Bar 数据字段

| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| `ticker` | string | 股票代码 | `sym` |
| `timestamp` | string | ISO 时间戳 | `s` (转换为 ISO) |
| `open` | number | 开盘价 | `op` 或 `o` |
| `high` | number | 最高价 | `h` |
| `low` | number | 最低价 | `l` |
| `close` | number | 收盘价 | `c` |
| `volume` | number | 成交量 | `v` |
| `vwap` | number | 成交量加权平均价 | `vw` |

---

## 🔍 实际数据示例

### WebSocket 原始消息示例
```json
[
  {
    "ev": "AM",
    "sym": "SPY",
    "v": 1234567,
    "av": 50000000,
    "op": 450.25,
    "vw": 450.30,
    "o": 450.25,
    "c": 450.50,
    "h": 450.75,
    "l": 450.20,
    "a": 450.30,
    "z": 1234567,
    "s": 1706287800000,
    "e": 1706287860000
  }
]
```

### 转换后的 Bar 数据示例
```python
{
    "ticker": "SPY",
    "timestamp": "2026-01-26T18:30:00Z",
    "open": 450.25,
    "high": 450.75,
    "low": 450.20,
    "close": 450.50,
    "volume": 1234567,
    "vwap": 450.30
}
```

### S3 存储格式示例
```json
{
  "source": "polygon_websocket",
  "ticker": "SPY",
  "timestamp": "2026-01-26T18:30:00Z",
  "bar_data": {
    "open": 450.25,
    "high": 450.75,
    "low": 450.20,
    "close": 450.50,
    "volume": 1234567,
    "vwap": 450.30
  },
  "collected_at": "2026-01-26T18:30:01.123Z"
}
```

---

## 📝 代码位置

- **WebSocket 连接**: `app/services/marketpulse/polygon_service.py`
  - `start_ws_aggregates()` - 启动 WebSocket
  - `_on_message()` - 接收消息
  - `_handle_aggregate()` - 解析聚合数据

- **数据收集**: `app/services/marketpulse/data_collector.py`
  - `_on_raw_bar_received()` - 处理接收到的 bar 数据
  - `_store_raw_bar()` - 存储到 S3

- **数据存储**: `app/services/marketpulse/aws_storage.py`
  - S3 存储逻辑

---

## 🔗 相关文档

- [架构设计](./architecture-layered-v3.md) - 了解数据流
- [AWS 部署](./AWS-SETUP-DUAL-AGENT.md) - 部署说明
- [Polygon.io 文档](https://polygon.io/docs/websockets) - 官方 WebSocket 文档
