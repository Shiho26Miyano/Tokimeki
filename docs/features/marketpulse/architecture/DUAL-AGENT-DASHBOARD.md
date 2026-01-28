# 双 Agent 对比 Dashboard（最新架构）

## 🎯 核心概念（目前实现）

- **双 Agent 架构（10 只股票批量对比）**  
  - **Compute Agent（计算 Agent）**：  
    - 从实时数据流生成因子信号  
    - 将当日所有股票信号写入 S3：`processed-data/{YYYY-MM-DD}/compute-signals.json`  
  - **Learning Agent（学习 Agent）**：  
    - 基于当日/历史 compute 信号训练模型  
    - 将模型及预测结果写入 S3：`processed-data/{YYYY-MM-DD}/learning-signals.json`
- **前端形态**：  
  - 一个「Excel 风格」的 **10 股对比表格**（AAPL, MSFT, AMZN, NVDA, TSLA, META, GOOGL, JPM, XOM, SPY）  
  - 每行是一只股票，列展示 Compute / Learning / 差值 / 收敛情况等

> 旧版文档里的「左右两张大卡片 + 时间序列图」是概念设计，目前实现已收敛为以 **表格为主、卡片和图表为辅** 的 Dashboard。

---

## 📊 前端设计（`static/index.html` + `static/js/components/market-pulse.js`）

### 1. 主区域布局

- **Tab 容器**：`#market-pulse-content`（`Market Pulse - Dual Signal Comparison`）  
- **刷新控制**：  
  - 按钮：`#market-pulse-refresh-btn`  
  - JS 中自动轮询：`MarketPulseDashboard.startAutoRefresh()` 每 30 秒刷新一次

### 2. Dual Signal 对比表格

HTML 结构见 `static/index.html`：

- 表格 ID：`#dual-signal-table`  
- 表体 ID：`#dual-signal-table-body`（由 JS 动态填充）  
- 列定义：
  - `Ticker`：股票代码
  - `Compute Signal`：计算 Agent 当日信号（`compute_agent.signal`）
  - `Learning Signal`：学习 Agent 预测信号（`learning_agent.signal`）
  - `Difference`：`signal_diff = learning - compute`
  - `R²`：`learning_agent.r2_score`，以百分比展示并根据区间着色  
  - `MAE`：`learning_agent.mae`
  - `Iterations`：`learning_agent.training_iterations`
  - `Converged`：✅/⏳
  - `Convergence`：进度条（0–100%，基于 R² 简化计算）

渲染逻辑位于 `MarketPulseDashboard.renderDualSignalTable(stocks)`：

- 遍历 `stocks` 数组，为每个 `stock` 生成 `<tr>`：  
  - 使用 `stock.compute_agent`、`stock.learning_agent`、`stock.difference`、`stock.convergence` 字段  
  - R² 使用背景色编码（高 → 绿，中 → 黄，低 → 红）  
  - 收敛进度使用 Bootstrap `progress` 组件

### 3. 数据加载与错误展示

- JS 类：`MarketPulseDashboard`（`static/js/components/market-pulse.js`）
- 关键方法：
  - `loadDualSignal()`  
    - `GET /api/v1/market-pulse/dual-signal`  
    - 控制台打印：`Dual signal API response: { ... }`  
    - 如果 `data.success` 且 `data.stocks` 非空，则调用 `renderDualSignalTable`  
    - 根据 `data.data_status.learning_agent_available` 决定是否展示「Learning Agent 尚未就绪」提示（不再阻塞渲染）
  - `showDualSignalError(message)`  
    - 将整行错误信息写入 `#dual-signal-table-body`
  - `showDualSignalWarning(message)`  
    - 在可选的警告区域 `#dual-signal-warning` 中展示黄色提示条

> 关键改动：**只要 `stocks` 有有效数据，就先渲染表格**，`data_status` 仅用于补充说明，不再导致整表「数据未就绪」。

---

## 🔄 后端架构 & 数据流（`market_pulse.py` + S3）

### 1. 总体数据流（当前实现）

```text
1. 数据采集器（Data Collector）
   → 写入 S3: raw-data/{YYYY-MM-DD}/...

2. Compute Agent（Lambda / 后端任务）
   → 读取 raw-data/
   → 计算 10 只股票的因子 & 信号
   → 写入:
      processed-data/{YYYY-MM-DD}/compute-signals.json

3. Learning Agent（Lambda）
   → 读取:
      processed-data/{YYYY-MM-DD}/compute-signals.json
      （及历史学习结果，视实现而定）
   → 训练/更新模型，生成预测信号 & 指标
   → 写入:
      processed-data/{YYYY-MM-DD}/learning-signals.json

4. FastAPI `/dual-signal` 端点
   → 同时读取 compute-signals.json & learning-signals.json
   → 聚合为 10 只股票的对比结构
   → 返回给前端 Dual Signal 表格
```

> 注意：旧文档里的 `learning-results/` 目录已被 **`processed-data/{date}/learning-signals.json`** 取代。

### 2. 关键 API 端点（FastAPI）

所有端点定义在 `app/api/v1/endpoints/market_pulse.py` 中。

- **当前脉冲 & 单 Agent 端点**（保持不变）：
  - `GET /api/v1/market-pulse/current`  
  - `GET /api/v1/market-pulse/events/today`  
  - `GET /api/v1/market-pulse/available-tickers`  
  - `GET /api/v1/market-pulse/compare`（单股票的「Compute vs Learning」深度对比）  
  - `GET /api/v1/market-pulse/compute-agent`  
  - `GET /api/v1/market-pulse/learning-agent`  
  - `GET /api/v1/market-pulse/performance`

- **Dual Signal Dashboard 专用端点（新增 & 前端实际调用）**  
  - `GET /api/v1/market-pulse/dual-signal`
    - 可选参数：`ticker`（限定返回某一只股票）
    - 核心实现：
      - 从环境变量 `AWS_S3_PULSE_BUCKET` 解析 bucket 名  
      - 使用 `AWSStorageService` 创建 S3 客户端  
      - 读取：
        - `processed-data/{today}/compute-signals.json`
        - `processed-data/{today}/learning-signals.json`
      - 支持 10 只核心股票（可选 ticker 过滤）
      - 将数据归并为数组：
        ```json
        {
          "ticker": "AAPL",
          "compute_agent": {
            "signal": 0.1234,
            "return": 0.001234,
            "vol": 0.012345
          },
          "learning_agent": {
            "signal": 0.2345,
            "r2_score": 0.91,
            "mae": 0.0123,
            "training_iterations": 50,
            "converged": true
          },
          "difference": {
            "signal_diff": 0.1111,
            "r2_diff": -0.09,
            "mae_diff": 0.0123
          },
          "convergence": {
            "status": "✅",
            "progress": 91
          }
        }
        ```
      - 响应顶层结构：
        - `success: bool`
        - `timestamp: ISO8601`
        - `date: YYYY-MM-DD`
        - `stocks: [...]`
        - `total_stocks: int`
        - `data_status`：
          - `compute_agent_available: bool`
          - `learning_agent_available: bool`
          - `compute_signals_count: int`
          - `learning_signals_count: int`

---

## ☁️ AWS 架构与权限（Market Pulse 专用）

### 1. S3 Bucket & 路径约定

- Bucket：`tokimeki-market-pulse-prod`
- 主要前缀：
  - `raw-data/`：原始行情数据（由数据采集器写入）
  - `processed-data/{YYYY-MM-DD}/compute-signals.json`：Compute Agent 输出
  - `processed-data/{YYYY-MM-DD}/learning-signals.json`：Learning Agent 输出
  - （兼容历史）`pulse-events/`、`learning-results/` 可能仍存在，但 Dual Signal 逻辑不依赖它们

### 2. IAM 用户与策略

- 运行应用的 IAM 用户：`tokimeki-pulse-writer`
- 推荐策略文件：`docs/features/marketpulse/MarketPulseS3AccessPolicy.json`  
  核心能力：
  - `s3:ListBucket` 针对 `tokimeki-market-pulse-prod`，并限制到相关前缀
  - `s3:GetBucketLocation`（解决部分 SDK 访问问题）
  - `s3:GetObject` / `s3:PutObject` / `s3:DeleteObject` 针对：
    - `raw-data/*`
    - `processed-data/*`
    - `pulse-events/*`
    - `learning-results/*`

> 具体手动修复步骤请参考：`FIX-S3-PERMISSIONS-MANUAL.md` 和 `WHY-ACCESS-DENIED.md`。

### 3. Lambda / 计算组件职责

- **Data Collector（后端服务或 Lambda）**
  - 持续从市场数据源收集 1 分钟 K 线 / Ticks  
  - 写入 `raw-data/` 前缀

- **Compute Agent Lambda**
  - 触发频率：数分钟级 / 手动触发（见 `scripts/trigger_lambda_agents.py --compute`）  
  - 读取 `raw-data/`，计算因子 & 信号  
  - 以批量形式写入 `compute-signals.json`：
    ```json
    {
      "signals": [
        { "ticker": "AAPL", "signal": 0.12, "return": 0.0012, "vol": 0.01 },
        ...
      ]
    }
    ```

- **Learning Agent Lambda**
  - 触发频率：小时级 / 手动触发（`--learning`）  
  - 读取 `compute-signals.json` 及历史模型信息  
  - 训练/更新模型，生成：
    - 每只股票的预测信号、R²、MAE、收敛状态  
  - 写入 `learning-signals.json`：
    ```json
    {
      "models": {
        "AAPL": {
          "signal_predicted": 0.23,
          "r2_score": 0.91,
          "mae": 0.012,
          "training_iterations": 50,
          "converged": true
        },
        ...
      }
    }
    ```

- **Web 应用 / FastAPI**
  - 使用 IAM 凭证访问 S3（通过 `AWSStorageService`）  
  - 组合 Compute + Learning 输出，提供 REST API 给前端

---

## 🚀 实施与运维 Checklist（更新版）

- **后端 & AWS**
  - [x] 确保 `AWS_S3_PULSE_BUCKET` 设置为 `tokimeki-market-pulse-prod`
  - [x] `tokimeki-pulse-writer` 已附加 `MarketPulseS3AccessPolicy`
  - [x] Data Collector 正常写入 `raw-data/`
  - [x] Compute Agent Lambda 正常写入 `compute-signals.json`
  - [x] Learning Agent Lambda 正常写入 `learning-signals.json`
  - [x] `/api/v1/market-pulse/dual-signal` 返回 `success: true` 且 `stocks.length == 10`

- **前端**
  - [x] `static/js/components/market-pulse.js` 已加载，并在 `#market-pulse-tab` 激活时初始化  
  - [x] 控制台能看到 `Dual signal API response: {...}` 日志  
  - [x] `#dual-signal-table-body` 中渲染出 10 行股票数据  
  - [x] 学习 Agent 尚未写入时，仅展示黄色提示，不再整表报错

这份文档现已与当前 **前端实现 + FastAPI 端点 + S3 / Lambda 工作流** 对齐，可作为 Market Pulse Dual Signal Dashboard 的权威设计说明。
