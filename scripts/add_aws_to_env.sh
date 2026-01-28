#!/bin/bash
# 添加 AWS 环境变量到 .env 文件

ENV_FILE=".env"

echo "🔧 添加 AWS 环境变量到 .env 文件"
echo "=" | head -c 60 && echo ""
echo ""

# 检查 .env 文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "创建新的 .env 文件..."
    touch "$ENV_FILE"
fi

# 检查是否已有 AWS 变量
if grep -q "^AWS_ACCESS_KEY_ID=" "$ENV_FILE"; then
    echo "⚠️  .env 文件中已存在 AWS_ACCESS_KEY_ID"
    read -p "是否要更新？(y/n): " update
    if [ "$update" != "y" ]; then
        echo "取消操作"
        exit 0
    fi
    # 删除旧的 AWS 变量
    sed -i.bak '/^AWS_/d' "$ENV_FILE"
    echo "已删除旧的 AWS 变量"
fi

echo ""
echo "请输入 AWS 凭证（直接按 Enter 保持当前值）:"
echo ""

# 读取现有值或提示输入
if grep -q "^AWS_ACCESS_KEY_ID=" "$ENV_FILE"; then
    current_key=$(grep "^AWS_ACCESS_KEY_ID=" "$ENV_FILE" | cut -d'=' -f2-)
    read -p "AWS_ACCESS_KEY_ID [$current_key]: " AWS_ACCESS_KEY_ID
    AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-$current_key}
else
    read -p "AWS_ACCESS_KEY_ID: " AWS_ACCESS_KEY_ID
fi

if grep -q "^AWS_SECRET_ACCESS_KEY=" "$ENV_FILE"; then
    current_secret=$(grep "^AWS_SECRET_ACCESS_KEY=" "$ENV_FILE" | cut -d'=' -f2-)
    read -sp "AWS_SECRET_ACCESS_KEY [***]: " AWS_SECRET_ACCESS_KEY
    echo ""
    AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-$current_secret}
else
    read -sp "AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY
    echo ""
fi

# 设置默认值
AWS_S3_PULSE_BUCKET="${AWS_S3_PULSE_BUCKET:-tokimeki-market-pulse-prod}"
AWS_REGION="${AWS_REGION:-us-east-2}"

# 添加到 .env 文件
echo "" >> "$ENV_FILE"
echo "# AWS Configuration for Market Pulse" >> "$ENV_FILE"
echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" >> "$ENV_FILE"
echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> "$ENV_FILE"
echo "AWS_S3_PULSE_BUCKET=$AWS_S3_PULSE_BUCKET" >> "$ENV_FILE"
echo "AWS_REGION=$AWS_REGION" >> "$ENV_FILE"

echo ""
echo "✅ 已添加 AWS 环境变量到 .env 文件"
echo ""
echo "📄 .env 文件现在包含:"
grep "^AWS_" "$ENV_FILE" | sed 's/=.*/=***/' || echo "  (未找到)"
echo ""
echo "💡 重要提示:"
echo "   1. .env 文件格式是 KEY=value（不是 export KEY=value）"
echo "   2. 应用不会自动加载 .env 文件"
echo "   3. 启动应用前需要手动加载:"
echo ""
echo "   方法 A: 使用 source（如果 .env 使用 export 格式）"
echo "      source .env"
echo "      python main.py"
echo ""
echo "   方法 B: 使用 export 命令（推荐）"
echo "      export \$(cat .env | grep -v '^#' | xargs)"
echo "      python main.py"
echo ""
echo "   方法 C: 使用 python-dotenv（需要安装）"
echo "      pip install python-dotenv"
echo "      # 然后在代码中添加: from dotenv import load_dotenv; load_dotenv()"
echo ""
