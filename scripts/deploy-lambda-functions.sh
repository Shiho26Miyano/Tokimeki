#!/bin/bash
# 部署 Lambda 函数 - 更新 Compute Agent 和 Learning Agent
#
# 使用方法:
#   ./scripts/deploy-lambda-functions.sh
#
# 需要设置环境变量:
#   - AWS_REGION (默认: us-east-2)
#   - S3_BUCKET_NAME (Lambda 函数使用的 S3 bucket)

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
AWS_REGION=${AWS_REGION:-us-east-2}
COMPUTE_FUNCTION_NAME="market-pulse-compute-agent"
LEARNING_FUNCTION_NAME="market-pulse-learning-agent"

# 必需的环境变量（创建函数时需要）
LAMBDA_ROLE_ARN=${LAMBDA_ROLE_ARN:-""}
S3_BUCKET_NAME=${S3_BUCKET_NAME:-""}

# Lambda 函数文件路径
COMPUTE_SOURCE="docs/features/marketpulse/aws-lambda-compute-agent.py"
LEARNING_SOURCE="docs/features/marketpulse/aws-lambda-learning-agent.py"

# 部署包文件名
COMPUTE_ZIP="lambda-compute-agent.zip"
LEARNING_ZIP="lambda-learning-agent.zip"

echo "🚀 开始部署 Lambda 函数..."
echo ""

# 检查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI 未安装。请先安装 AWS CLI。${NC}"
    exit 1
fi

# 检查源文件
if [ ! -f "$COMPUTE_SOURCE" ]; then
    echo -e "${RED}❌ 找不到 Compute Agent 源文件: $COMPUTE_SOURCE${NC}"
    exit 1
fi

if [ ! -f "$LEARNING_SOURCE" ]; then
    echo -e "${RED}❌ 找不到 Learning Agent 源文件: $LEARNING_SOURCE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 源文件检查通过${NC}"
echo ""

# ============================================================================
# 步骤 1: 准备 Compute Agent 部署包
# ============================================================================

echo "📦 步骤 1: 准备 Compute Agent 部署包..."

# 创建临时目录
TEMP_DIR=$(mktemp -d)
COMPUTE_TEMP="$TEMP_DIR/compute"

mkdir -p "$COMPUTE_TEMP"

# 复制并重命名文件
cp "$COMPUTE_SOURCE" "$COMPUTE_TEMP/lambda_function.py"

# 创建 zip 文件
cd "$COMPUTE_TEMP"
zip -q -r "$COMPUTE_ZIP" lambda_function.py
cd - > /dev/null

# 移动到项目根目录
mv "$COMPUTE_TEMP/$COMPUTE_ZIP" .

echo -e "${GREEN}✅ Compute Agent 部署包已创建: $COMPUTE_ZIP${NC}"
echo "   文件大小: $(ls -lh $COMPUTE_ZIP | awk '{print $5}')"
echo ""

# ============================================================================
# 步骤 2: 准备 Learning Agent 部署包
# ============================================================================

echo "📦 步骤 2: 准备 Learning Agent 部署包..."

LEARNING_TEMP="$TEMP_DIR/learning"
mkdir -p "$LEARNING_TEMP"

# 复制并重命名文件
cp "$LEARNING_SOURCE" "$LEARNING_TEMP/lambda_function.py"

# 创建 zip 文件
cd "$LEARNING_TEMP"
zip -q -r "$LEARNING_ZIP" lambda_function.py
cd - > /dev/null

# 移动到项目根目录
mv "$LEARNING_TEMP/$LEARNING_ZIP" .

echo -e "${GREEN}✅ Learning Agent 部署包已创建: $LEARNING_ZIP${NC}"
echo "   文件大小: $(ls -lh $LEARNING_ZIP | awk '{print $5}')"
echo ""

# 清理临时目录
rm -rf "$TEMP_DIR"

# ============================================================================
# 步骤 3: 更新 Compute Agent Lambda 函数
# ============================================================================

echo "⚡ 步骤 3: 更新 Compute Agent Lambda 函数..."

if aws lambda get-function --function-name "$COMPUTE_FUNCTION_NAME" --region "$AWS_REGION" &> /dev/null; then
    # 函数存在，更新代码
    echo "   更新现有函数: $COMPUTE_FUNCTION_NAME"
    
    aws lambda update-function-code \
        --function-name "$COMPUTE_FUNCTION_NAME" \
        --zip-file "fileb://$COMPUTE_ZIP" \
        --region "$AWS_REGION" \
        --output json > /dev/null
    
    echo -e "${GREEN}✅ Compute Agent 已更新${NC}"
    
    # 等待更新完成
    echo "   等待更新完成..."
    aws lambda wait function-updated \
        --function-name "$COMPUTE_FUNCTION_NAME" \
        --region "$AWS_REGION"
    
    echo -e "${GREEN}✅ Compute Agent 更新完成${NC}"
else
    echo -e "${YELLOW}⚠️  函数 $COMPUTE_FUNCTION_NAME 不存在${NC}"
    echo ""
    echo "可能的原因："
    echo "  1. 函数在不同的区域（当前检查: $AWS_REGION）"
    echo "  2. 函数名称不同"
    echo "  3. AWS 凭证/账户不同"
    echo ""
    echo "💡 诊断步骤："
    echo "  1. 运行查找脚本: python3 scripts/find_lambda_functions.py"
    echo "  2. 检查函数是否在其他区域"
    echo "  3. 如果函数已存在，使用以下命令更新代码："
    echo ""
    echo "   aws lambda update-function-code \\"
    echo "       --function-name $COMPUTE_FUNCTION_NAME \\"
    echo "       --zip-file fileb://$COMPUTE_ZIP \\"
    echo "       --region YOUR_REGION"
    echo ""
    echo "  或者如果函数不存在，创建新函数："
    echo ""
    echo "   aws lambda create-function \\"
    echo "       --function-name $COMPUTE_FUNCTION_NAME \\"
    echo "       --runtime python3.11 \\"
    echo "       --role arn:aws:iam::YOUR_ACCOUNT_ID:role/market-pulse-lambda-role \\"
    echo "       --handler lambda_function.lambda_handler \\"
    echo "       --zip-file fileb://$COMPUTE_ZIP \\"
    echo "       --timeout 900 \\"
    echo "       --memory-size 512 \\"
    echo "       --region $AWS_REGION \\"
    echo "       --environment Variables=\"{S3_BUCKET_NAME=your-bucket-name}\""
    echo ""
fi

echo ""

# ============================================================================
# 步骤 4: 更新 Learning Agent Lambda 函数
# ============================================================================

echo "🧠 步骤 4: 更新 Learning Agent Lambda 函数..."

if aws lambda get-function --function-name "$LEARNING_FUNCTION_NAME" --region "$AWS_REGION" &> /dev/null; then
    # 函数存在，更新代码
    echo "   更新现有函数: $LEARNING_FUNCTION_NAME"
    
    aws lambda update-function-code \
        --function-name "$LEARNING_FUNCTION_NAME" \
        --zip-file "fileb://$LEARNING_ZIP" \
        --region "$AWS_REGION" \
        --output json > /dev/null
    
    echo -e "${GREEN}✅ Learning Agent 已更新${NC}"
    
    # 等待更新完成
    echo "   等待更新完成..."
    aws lambda wait function-updated \
        --function-name "$LEARNING_FUNCTION_NAME" \
        --region "$AWS_REGION"
    
    echo -e "${GREEN}✅ Learning Agent 更新完成${NC}"
else
    echo -e "${YELLOW}⚠️  函数 $LEARNING_FUNCTION_NAME 不存在${NC}"
    echo ""
    echo "可能的原因："
    echo "  1. 函数在不同的区域（当前检查: $AWS_REGION）"
    echo "  2. 函数名称不同"
    echo "  3. AWS 凭证/账户不同"
    echo ""
    echo "💡 诊断步骤："
    echo "  1. 运行查找脚本: python3 scripts/find_lambda_functions.py"
    echo "  2. 检查函数是否在其他区域"
    echo "  3. 如果函数已存在，使用以下命令更新代码："
    echo ""
    echo "   aws lambda update-function-code \\"
    echo "       --function-name $LEARNING_FUNCTION_NAME \\"
    echo "       --zip-file fileb://$LEARNING_ZIP \\"
    echo "       --region YOUR_REGION"
    echo ""
    echo "  或者如果函数不存在，创建新函数："
    echo ""
    echo "   aws lambda create-function \\"
    echo "       --function-name $LEARNING_FUNCTION_NAME \\"
    echo "       --runtime python3.11 \\"
    echo "       --role arn:aws:iam::YOUR_ACCOUNT_ID:role/market-pulse-lambda-role \\"
    echo "       --handler lambda_function.lambda_handler \\"
    echo "       --zip-file fileb://$LEARNING_ZIP \\"
    echo "       --timeout 900 \\"
    echo "       --memory-size 1024 \\"
    echo "       --region $AWS_REGION \\"
    echo "       --environment Variables=\"{S3_BUCKET_NAME=your-bucket-name}\""
    echo ""
fi

echo ""

# ============================================================================
# 步骤 5: 验证部署
# ============================================================================

echo "✅ 步骤 5: 验证部署..."

# 检查 Compute Agent
if aws lambda get-function --function-name "$COMPUTE_FUNCTION_NAME" --region "$AWS_REGION" &> /dev/null; then
    COMPUTE_VERSION=$(aws lambda get-function \
        --function-name "$COMPUTE_FUNCTION_NAME" \
        --region "$AWS_REGION" \
        --query 'Configuration.Version' \
        --output text)
    echo -e "${GREEN}✅ Compute Agent: 版本 $COMPUTE_VERSION${NC}"
else
    echo -e "${RED}❌ Compute Agent: 函数不存在${NC}"
fi

# 检查 Learning Agent
if aws lambda get-function --function-name "$LEARNING_FUNCTION_NAME" --region "$AWS_REGION" &> /dev/null; then
    LEARNING_VERSION=$(aws lambda get-function \
        --function-name "$LEARNING_FUNCTION_NAME" \
        --region "$AWS_REGION" \
        --query 'Configuration.Version' \
        --output text)
    echo -e "${GREEN}✅ Learning Agent: 版本 $LEARNING_VERSION${NC}"
else
    echo -e "${RED}❌ Learning Agent: 函数不存在${NC}"
fi

echo ""
echo -e "${GREEN}🎉 部署完成！${NC}"
echo ""
echo "📋 部署包文件："
echo "   - $COMPUTE_ZIP"
echo "   - $LEARNING_ZIP"
echo ""
echo "💡 提示："
echo "   - 可以手动删除 zip 文件：rm $COMPUTE_ZIP $LEARNING_ZIP"
echo "   - 查看日志：aws logs tail /aws/lambda/$COMPUTE_FUNCTION_NAME --follow"
echo "   - 测试函数：aws lambda invoke --function-name $COMPUTE_FUNCTION_NAME --payload '{}' response.json"
echo ""
