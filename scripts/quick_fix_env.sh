#!/bin/bash
# 快速设置环境变量脚本

echo "🔧 快速设置 AWS 环境变量"
echo "=" | head -c 60 && echo ""
echo ""

# 检查是否已有 .env 文件
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    echo "📄 发现 .env 文件，将加载其中的变量"
    source "$ENV_FILE"
fi

# 提示用户输入
echo "请输入 AWS 凭证（如果已设置环境变量，直接按 Enter 跳过）:"
echo ""

if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    read -p "AWS_ACCESS_KEY_ID: " AWS_ACCESS_KEY_ID
    export AWS_ACCESS_KEY_ID
else
    echo "✅ AWS_ACCESS_KEY_ID 已设置"
fi

if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    read -sp "AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY
    echo ""
    export AWS_SECRET_ACCESS_KEY
else
    echo "✅ AWS_SECRET_ACCESS_KEY 已设置"
fi

# 设置默认值
export AWS_S3_PULSE_BUCKET="${AWS_S3_PULSE_BUCKET:-tokimeki-market-pulse-prod}"
export AWS_REGION="${AWS_REGION:-us-east-2}"

echo ""
echo "✅ 环境变量已设置:"
echo "   AWS_S3_PULSE_BUCKET: $AWS_S3_PULSE_BUCKET"
echo "   AWS_REGION: $AWS_REGION"
echo "   AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "   AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."
echo ""

# 验证凭证
echo "🔍 验证 AWS 凭证..."
if aws sts get-caller-identity &> /dev/null; then
    echo "✅ AWS 凭证有效"
    aws sts get-caller-identity --output table
else
    echo "❌ AWS 凭证无效或无法连接"
    exit 1
fi

echo ""
echo "💡 要永久保存这些环境变量，可以："
echo "   1. 创建 .env 文件（推荐）:"
echo "      echo 'export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID' >> .env"
echo "      echo 'export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY' >> .env"
echo "      echo 'export AWS_S3_PULSE_BUCKET=$AWS_S3_PULSE_BUCKET' >> .env"
echo "      echo 'export AWS_REGION=$AWS_REGION' >> .env"
echo ""
echo "   2. 然后在启动应用前运行: source .env"
echo ""
echo "   3. 或者使用启动脚本:"
echo "      source .env && python main.py"
echo ""
