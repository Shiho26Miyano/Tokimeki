#!/bin/bash
#
# 更新现有 IAM 策略脚本
#
# 用法:
#   ./scripts/update_iam_policy.sh POLICY_NAME
#   ./scripts/update_iam_policy.sh MarketPulseLambdaInvokePolicy
#

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo "用法: $0 POLICY_NAME"
    echo ""
    echo "示例:"
    echo "  $0 MarketPulseLambdaInvokePolicy"
    exit 1
fi

POLICY_NAME="$1"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-989513605244}"
REGION="${AWS_REGION:-us-east-2}"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

echo "📝 更新 IAM 策略"
echo "================================"
echo "策略名称: $POLICY_NAME"
echo "策略 ARN: $POLICY_ARN"
echo ""

# 检查策略是否存在
if ! aws iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    echo -e "${RED}❌ 策略不存在: $POLICY_NAME${NC}"
    echo "   请检查策略名称是否正确"
    exit 1
fi

# 获取当前默认版本
echo -e "${BLUE}📋 获取当前策略内容...${NC}"
DEFAULT_VERSION=$(aws iam get-policy \
    --policy-arn "$POLICY_ARN" \
    --query 'Policy.DefaultVersionId' \
    --output text)

echo "   当前默认版本: $DEFAULT_VERSION"

# 显示当前策略内容
echo ""
echo -e "${BLUE}当前策略内容:${NC}"
aws iam get-policy-version \
    --policy-arn "$POLICY_ARN" \
    --version-id "$DEFAULT_VERSION" \
    --query 'PolicyVersion.Document' \
    --output json | python3 -m json.tool || cat

echo ""
echo "================================"
echo ""

# 创建新的策略文档
echo -e "${BLUE}📝 创建新策略版本...${NC}"
echo "请输入新的策略 JSON（输入完成后按 Ctrl+D）:"
echo ""

# 创建临时文件
TMP_POLICY=$(mktemp)
cat > "$TMP_POLICY"

# 验证 JSON 格式
if ! python3 -m json.tool "$TMP_POLICY" > /dev/null 2>&1; then
    echo -e "${RED}❌ JSON 格式无效${NC}"
    rm -f "$TMP_POLICY"
    exit 1
fi

# 创建新版本
echo ""
echo -e "${BLUE}🔄 创建新版本...${NC}"
NEW_VERSION=$(aws iam create-policy-version \
    --policy-arn "$POLICY_ARN" \
    --policy-document "file://$TMP_POLICY" \
    --set-as-default \
    --query 'PolicyVersion.VersionId' \
    --output text)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 策略已更新${NC}"
    echo "   新版本 ID: $NEW_VERSION"
    echo ""
    echo "💡 提示:"
    echo "   - 新版本已设置为默认版本"
    echo "   - 权限更改可能需要 1-5 分钟才能生效"
    echo "   - 可以删除旧版本以节省空间（IAM 最多保留 5 个版本）"
else
    echo -e "${RED}❌ 更新失败${NC}"
    rm -f "$TMP_POLICY"
    exit 1
fi

# 清理临时文件
rm -f "$TMP_POLICY"

# 显示更新后的策略
echo ""
echo -e "${BLUE}更新后的策略内容:${NC}"
aws iam get-policy-version \
    --policy-arn "$POLICY_ARN" \
    --version-id "$NEW_VERSION" \
    --query 'PolicyVersion.Document' \
    --output json | python3 -m json.tool || cat
