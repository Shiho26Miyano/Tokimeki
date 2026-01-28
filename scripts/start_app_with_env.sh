#!/bin/bash
# 启动应用并自动加载 .env 文件

echo "🚀 启动应用（自动加载 .env 文件）..."
echo "=" | head -c 60 && echo ""
echo ""

# 检查 .env 文件
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  未找到 .env 文件"
    echo "   运行 ./scripts/add_aws_to_env.sh 来创建"
    exit 1
fi

# 加载 .env 文件
echo "📄 加载 .env 文件..."
set -a
source <(grep -v '^#' "$ENV_FILE" | grep -v '^$' | sed 's/^/export /')
set +a
echo "✅ 环境变量已加载"
echo ""

# 验证关键环境变量
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "⚠️  警告: AWS 凭证未在 .env 文件中设置"
    echo "   应用可能无法访问 S3"
    echo ""
fi

# 启动应用
echo "🚀 启动应用..."
echo ""
python main.py
