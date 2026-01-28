#!/bin/bash
# 测试 S3 访问权限脚本

set -e

echo "🔍 测试 S3 访问权限..."
echo "=" | head -c 60 && echo ""

# 尝试从 .env 文件加载环境变量
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    echo ""
    echo "📄 从 .env 文件加载环境变量..."
    # 加载 .env 文件（格式: KEY=value）
    set -a
    source <(grep -v '^#' "$ENV_FILE" | grep -v '^$' | sed 's/^/export /')
    set +a
    echo "✅ 已加载 .env 文件"
fi

# 检查环境变量
echo ""
echo "1. 检查环境变量:"
BUCKET="${AWS_S3_PULSE_BUCKET:-tokimeki-market-pulse-prod}"
echo "   AWS_S3_PULSE_BUCKET: $BUCKET"
echo "   AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:+✅ 已设置}"
echo "   AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:+✅ 已设置}"
echo "   AWS_REGION: ${AWS_REGION:-未设置 (默认: us-east-2)}"

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo ""
    echo "❌ AWS 凭证未设置！"
    echo ""
    echo "请设置环境变量："
    echo "  方法 1: 使用 .env 文件（推荐）"
    echo "    ./scripts/add_aws_to_env.sh"
    echo ""
    echo "  方法 2: 手动设置"
    echo "    export AWS_ACCESS_KEY_ID=your-access-key-id"
    echo "    export AWS_SECRET_ACCESS_KEY=your-secret-access-key"
    echo "    export AWS_S3_PULSE_BUCKET=tokimeki-market-pulse-prod"
    echo "    export AWS_REGION=us-east-2"
    exit 1
fi

# 检查 AWS CLI 是否安装
if ! command -v aws &> /dev/null; then
    echo ""
    echo "❌ AWS CLI 未安装"
    echo "   请安装: pip install awscli"
    exit 1
fi

# 测试 AWS 凭证
echo ""
echo "2. 验证 AWS 凭证:"
if aws sts get-caller-identity &> /dev/null; then
    echo "   ✅ 凭证有效"
    aws sts get-caller-identity --output table
else
    echo "   ❌ 凭证无效或无法连接 AWS"
    exit 1
fi

# 测试 S3 访问
echo ""
echo "3. 测试 S3 访问:"
REGION="${AWS_REGION:-us-east-2}"

# 测试 head_bucket
echo "   测试 head_bucket..."
if aws s3api head-bucket --bucket "$BUCKET" --region "$REGION" 2>&1; then
    echo "   ✅ head_bucket 成功"
else
    echo "   ❌ head_bucket 失败"
    echo "   可能原因:"
    echo "   - 缺少 s3:ListBucket 权限"
    echo "   - Bucket 不存在"
    echo "   - 区域不正确"
    exit 1
fi

# 测试 list_objects
echo "   测试 list_objects..."
if aws s3 ls "s3://$BUCKET/" --region "$REGION" &> /dev/null; then
    echo "   ✅ list_objects 成功"
    echo ""
    echo "   Bucket 内容:"
    aws s3 ls "s3://$BUCKET/" --region "$REGION" | head -10
else
    echo "   ❌ list_objects 失败"
    exit 1
fi

# 测试特定路径
echo ""
echo "4. 测试特定路径:"
for prefix in "raw-data/" "processed-data/" "pulse-events/" "learning-results/"; do
    echo "   检查 $prefix..."
    if aws s3 ls "s3://$BUCKET/$prefix" --region "$REGION" &> /dev/null; then
        count=$(aws s3 ls "s3://$BUCKET/$prefix" --region "$REGION" 2>/dev/null | wc -l | tr -d ' ')
        echo "   ✅ $prefix: 找到 $count 个对象"
    else
        echo "   ⚠️  $prefix: 路径不存在或无法访问"
    fi
done

echo ""
echo "✅ 所有 S3 访问测试通过！"
echo ""
echo "💡 如果应用仍然报错，请确保："
echo "   1. 环境变量在应用启动前已设置"
echo "   2. 如果应用正在运行，重启应用以加载新的环境变量"
echo "   3. 检查应用日志查看详细错误信息"
