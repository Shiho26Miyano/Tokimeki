# Market Pulse 快速启动

## 前置要求

- Python 3.8+
- Polygon.io API key
- AWS 账户 (S3 bucket)

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置环境变量

创建 `.env` 文件:

```bash
POLYGON_API_KEY=your_api_key
AWS_S3_PULSE_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
POLYGON_USE_DELAYED_WS=false  # true=延迟数据, false=实时数据
```

## 3. 创建 S3 Bucket

```bash
aws s3 mb s3://your-bucket-name
```

## 4. 启动应用

```bash
uvicorn app.main:app --reload
```

## 5. 验证

### 检查数据收集

```bash
curl http://localhost:8000/api/v1/market-pulse/collection/stats
```

### 测试 WebSocket

```bash
python3 scripts/test_websocket_connection.py
```

### 查看今天的事件

```bash
curl http://localhost:8000/api/v1/market-pulse/events/today
```

## 下一步

- [架构概述](./architecture.md) - 了解系统架构
- [分层架构设计 v2](./architecture-layered-v2.md) - 深入理解架构
- [AWS 资源清单](./aws-storage-what-to-create.md) - 创建 AWS 资源
- [Lambda 部署指南](./lambda-deployment-guide.md) - 部署处理层
