# AWS 资源清单

## 必需资源

### S3 Bucket
- **名称**: `your-bucket-name` (自定义)
- **用途**: 存储原始数据和处理结果
- **结构**:
  ```
  raw-data/YYYY-MM-DD/ticker/timestamp.json
  processed-data/YYYY-MM-DD/pulse-events.json
  daily-summaries/YYYY-MM-DD.json
  ```

## 可选资源

### DynamoDB Table
- **名称**: `tokimeki-pulse-events` (可选)
- **用途**: 快速查询（如果不用，只使用 S3）
- **Key**: `timestamp` (String)

## 环境变量

```bash
AWS_S3_PULSE_BUCKET=your-bucket-name
AWS_DYNAMODB_PULSE_TABLE=tokimeki-pulse-events  # 可选
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-2
```

## 快速创建

```bash
# S3 Bucket
aws s3 mb s3://your-bucket-name --region us-east-2

# DynamoDB (可选)
aws dynamodb create-table \
  --table-name tokimeki-pulse-events \
  --attribute-definitions AttributeName=timestamp,AttributeType=S \
  --key-schema AttributeName=timestamp,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

更多信息见 [Lambda 部署指南](./lambda-deployment-guide.md)
