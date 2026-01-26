Design Doc: Market Pulse Dashboard + Daily Learning Agent (Tokimeki)

1. 背景与目标
背景
你已经有 Tokimeki 网站（Railway 部署，React 前端）。你购买了 Polygon Stocks Starter，希望用 Polygon 数据构建一个“市场脉搏（Pulse）”看板，并把每天/每5分钟生成的总结事件存到 AWS，供 agent 迭代学习与输出每日洞察。

目标
Tokimeki 新增一个 Tab：Market Pulse
后端从 Polygon 获取数据并实时/准实时计算 Pulse 指标
将 Pulse 汇总写入 AWS（事件日志）
每天运行一个 Agent：读事件→产出 “Daily Summary + Learnings” → 回写 AWS
Tokimeki 前端展示：今日脉搏、历史曲线、每日总结、可解释性结论

非目标（v0 不做）
自动交易/下单
高频 tick 级微结构全量重建
复杂多资产全市场扫描

2. 用户体验
A. 今日状态：Regime / Stress / Drivers
B. Pulse 曲线
C. 指标卡片
D. Daily Summary

3. 架构
Polygon → Railway → AWS → Agent → Tokimeki

4. Pulse Event
{ ts, stress, velocity, volume, regime }

5. 指标
Price Velocity, Volume Surge, Volatility Burst, Breadth, Stress Index

6. AWS
S3 + DynamoDB（可选）

7. Agent
EventBridge → Lambda → LLM → Summary

8. Railway
market_data, pulse, storage, api

9. 安全
IAM 最小权限

10. 里程碑
MVP → v1 → v2
