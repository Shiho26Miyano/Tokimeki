# ETF Dashboard 数据来源说明

## 数据流程图

```
前端 (etf-dashboard-multi.js)
    ↓
API Endpoint: /api/v1/etf/dashboard/data
    ↓
ETFDashboardService (dashboard_service.py)
    ↓
    ├─→ ETFPolygonService (polygon_service.py) - 主要数据源
    │   └─→ Polygon.io API (实时数据)
    │
    ├─→ ETFYFinanceService (yfinance_service.py) - 备用数据源
    │   └─→ Yahoo Finance (通过yfinance库)
    │
    └─→ ETFAnalyticsService (analytics_service.py) - 计算指标
        └─→ 基于价格数据计算各种指标
```

## 数据源详情

### 1. **Polygon.io API** (主要数据源)
- **服务文件**: `app/services/etf/polygon_service.py`
- **API Key**: 从环境变量 `POLYGON_API_KEY` 读取
- **数据获取**:
  - **基本信息**: `get_ticker_details()` + `get_snapshot_ticker()` (实时价格)
  - **历史价格**: `list_aggs()` (日K线数据)
  - **实时数据**: `get_snapshot_ticker()` 获取最新报价
- **特点**:
  - 实时数据（如果API key可用）
  - 高质量的历史数据
  - 需要API key（付费服务）
  - 有速率限制，已实现重试和退避机制

### 2. **Yahoo Finance** (备用数据源)
- **服务文件**: `app/services/etf/yfinance_service.py`
- **库**: `yfinance` (Python库)
- **数据获取**:
  - **基本信息**: `ticker.info` 或 `ticker.fast_info`
  - **历史价格**: `ticker.history()`
  - **持仓信息**: `ticker.holdings` 或 `ticker.info['topHoldings']`
  - **分红历史**: `ticker.dividends`
- **特点**:
  - 免费使用
  - 数据可能有延迟（15分钟）
  - 某些ETF数据可能不完整
  - 经常返回404错误（已处理）

### 3. **数据优先级策略**

在 `ETFDashboardService` 中，数据获取遵循以下优先级：

1. **基本信息 (Basic Info)**:
   - 优先: Polygon.io (实时数据)
   - 备用: Yahoo Finance
   - 如果都失败: 从价格数据创建最小信息

2. **价格数据 (Price Data)**:
   - 优先: Polygon.io (历史K线)
   - 备用: Yahoo Finance

3. **持仓信息 (Holdings)**:
   - 主要: Yahoo Finance (更可靠)
   - Polygon.io 不提供持仓数据

4. **分红历史 (Dividends)**:
   - 主要: Yahoo Finance
   - Polygon.io 不提供分红数据

## 计算的指标

### 由 ETFAnalyticsService 计算：

1. **风险指标 (Risk Metrics)**:
   - 波动率 (Volatility): 30天、60天、1年
   - Beta: 相对市场敏感度
   - Sharpe Ratio: 风险调整收益
   - Sortino Ratio: 下行风险调整收益
   - 最大回撤 (Max Drawdown)
   - VaR (Value at Risk)

2. **技术指标 (Technical Indicators)**:
   - 移动平均线: SMA 20/50/200, EMA 12/26
   - RSI (相对强弱指标)
   - MACD (移动平均收敛散度)
   - 布林带 (Bollinger Bands)
   - ATR (平均真实波幅)

3. **持仓分析 (Holdings Analysis)**:
   - 持仓集中度
   - 行业分布
   - 板块分布
   - Top 10持仓

## 前端计算

在前端 (`etf-dashboard-multi.js`) 中还会计算：

1. **Composite Score**: 
   - 使用z-score方法
   - 权重: Performance 30%, Risk 25%, Efficiency 25%, Cost 10%, Liquidity 10%

2. **排名系统**:
   - 每个指标计算排名 (#1, #2, ...)
   - 根据指标类型判断"更好"的方向（高更好 vs 低更好）

3. **图表数据**:
   - 归一化增长曲线
   - 回撤曲线
   - 风险收益散点图

## 数据更新频率

- **实时数据**: Polygon.io snapshot API (如果可用)
- **历史数据**: 根据请求的 `date_range_days` 参数
- **缓存**: Polygon服务有30分钟的内存缓存
- **并发**: 多个ETF数据并发获取

## 错误处理

- 404错误: 正常处理（某些ETF可能没有某些数据）
- 速率限制: 自动重试和退避
- 数据缺失: 使用fallback数据源或返回空值
- 异常: 记录日志但不中断整个流程

## 配置

### 环境变量
- `POLYGON_API_KEY`: Polygon.io API密钥（可选，但推荐）

### 依赖包
- `polygon-api-client`: Polygon.io官方客户端
- `yfinance`: Yahoo Finance数据获取
- `pandas`: 数据处理
- `numpy`: 数值计算

## 数据质量

- **Polygon.io**: ⭐⭐⭐⭐⭐ (高质量，实时)
- **Yahoo Finance**: ⭐⭐⭐⭐ (良好，可能有延迟)
- **计算指标**: ⭐⭐⭐⭐⭐ (基于标准金融公式)

