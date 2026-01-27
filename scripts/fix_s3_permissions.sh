#!/bin/bash
#
# 修复 IAM 用户 S3 访问权限
# 为 tokimeki-pulse-writer 用户添加 S3 读写权限
#
# 用法:
#   ./scripts/fix_s3_permissions.sh                    # 使用默认凭证
#   ./scripts/fix_s3_permissions.sh --profile admin    # 使用指定的 AWS profile
#   ./scripts/fix_s3_permissions.sh --bucket my-bucket  # 指定 bucket 名称
#

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 解析参数
AWS_PROFILE=""
BUCKET_NAME=""
if [ "$1" = "--profile" ] && [ -n "$2" ]; then
    AWS_PROFILE="$2"
    export AWS_PROFILE
    shift 2
fi
if [ "$1" = "--bucket" ] && [ -n "$2" ]; then
    BUCKET_NAME="$2"
    shift 2
fi

# 配置
USER_NAME="tokimeki-pulse-writer"
POLICY_NAME="MarketPulseS3AccessPolicy"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-989513605244}"
REGION="${AWS_REGION:-us-east-2}"

# 如果没有指定 bucket，尝试从环境变量获取
if [ -z "$BUCKET_NAME" ]; then
    BUCKET_NAME="${AWS_S3_PULSE_BUCKET:-tokimeki-market-pulse-prod}"
fi

POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

echo "🔧 修复 S3 访问权限"
echo "================================"
echo "IAM 用户: $USER_NAME"
echo "策略名称: $POLICY_NAME"
echo "S3 Bucket: $BUCKET_NAME"
echo ""

# 检查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI 未安装${NC}"
    echo "   安装方法: brew install awscli"
    exit 1
fi

# 检查 AWS 凭证
AWS_CMD="aws"
if [ -n "$AWS_PROFILE" ]; then
    AWS_CMD="aws --profile $AWS_PROFILE"
    echo -e "${BLUE}使用 AWS Profile: $AWS_PROFILE${NC}"
fi

if ! $AWS_CMD sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS 凭证未配置${NC}"
    echo "   运行: aws configure"
    echo "   或使用: $0 --profile YOUR_PROFILE"
    exit 1
fi

# 显示当前 AWS 身份
CALLER_IDENTITY=$($AWS_CMD sts get-caller-identity --output json)
CALLER_ARN=$(echo "$CALLER_IDENTITY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('Arn', 'Unknown'))")
echo -e "${BLUE}当前 AWS 身份: $CALLER_ARN${NC}"
echo ""

# 验证 bucket 是否存在
echo -e "${BLUE}🔍 验证 S3 bucket...${NC}"
if $AWS_CMD s3 ls "s3://${BUCKET_NAME}" &> /dev/null; then
    echo -e "${GREEN}✅ S3 bucket 可访问: ${BUCKET_NAME}${NC}"
else
    echo -e "${YELLOW}⚠️  无法访问 S3 bucket: ${BUCKET_NAME}${NC}"
    echo "   这可能是权限问题，我们将继续添加权限..."
fi
echo ""

# 创建策略文档
echo -e "${BLUE}📝 创建策略文档...${NC}"
TMP_POLICY=$(mktemp)
cat > "$TMP_POLICY" <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::${BUCKET_NAME}",
            "Condition": {
                "StringLike": {
                    "s3:prefix": [
                        "",
                        "raw-data/*",
                        "processed-data/*",
                        "pulse-events/*",
                        "learning-results/*"
                    ]
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::${BUCKET_NAME}/raw-data/*",
                "arn:aws:s3:::${BUCKET_NAME}/processed-data/*",
                "arn:aws:s3:::${BUCKET_NAME}/pulse-events/*",
                "arn:aws:s3:::${BUCKET_NAME}/learning-results/*"
            ]
        }
    ]
}
EOF

echo "   策略内容:"
cat "$TMP_POLICY" | python3 -m json.tool 2>/dev/null || cat "$TMP_POLICY"
echo ""

# 检查策略是否已存在
if $AWS_CMD iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    echo -e "${YELLOW}⚠️  策略已存在: $POLICY_NAME${NC}"
    echo "   更新策略..."
    
    # 获取当前默认版本
    DEFAULT_VERSION=$($AWS_CMD iam get-policy \
        --policy-arn "$POLICY_ARN" \
        --query 'Policy.DefaultVersionId' \
        --output text)
    
    echo "   当前版本: $DEFAULT_VERSION"
    
    # 创建新版本
    NEW_VERSION=$($AWS_CMD iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document "file://$TMP_POLICY" \
        --set-as-default \
        --query 'PolicyVersion.VersionId' \
        --output text)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 策略已更新${NC}"
        echo "   新版本: $NEW_VERSION"
    else
        echo -e "${RED}❌ 更新策略失败${NC}"
        rm -f "$TMP_POLICY"
        exit 1
    fi
else
    echo -e "${BLUE}📦 创建新策略...${NC}"
    
    # 创建策略
    $AWS_CMD iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document "file://$TMP_POLICY" \
        --description "Allow S3 access for Market Pulse bucket" \
        --query 'Policy.Arn' \
        --output text > /dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 策略已创建${NC}"
    else
        echo -e "${RED}❌ 创建策略失败${NC}"
        rm -f "$TMP_POLICY"
        exit 1
    fi
fi

# 检查用户是否存在
if ! $AWS_CMD iam get-user --user-name "$USER_NAME" &> /dev/null; then
    echo -e "${YELLOW}⚠️  IAM 用户不存在: $USER_NAME${NC}"
    echo "   提示: 如果使用不同的用户，请手动附加策略"
    echo "   策略 ARN: $POLICY_ARN"
    rm -f "$TMP_POLICY"
    exit 0
fi

# 检查策略是否已附加到用户
echo ""
echo -e "${BLUE}🔗 检查策略是否已附加到用户...${NC}"
ATTACHED=$($AWS_CMD iam list-attached-user-policies \
    --user-name "$USER_NAME" \
    --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" \
    --output text)

if [ -n "$ATTACHED" ]; then
    echo -e "${GREEN}✅ 策略已附加到用户${NC}"
else
    echo -e "${YELLOW}⚠️  策略未附加，正在附加...${NC}"
    
    # 附加策略到用户
    $AWS_CMD iam attach-user-policy \
        --user-name "$USER_NAME" \
        --policy-arn "$POLICY_ARN"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 策略已附加到用户${NC}"
    else
        echo -e "${RED}❌ 附加策略失败${NC}"
        echo "   可能需要管理员权限"
        echo "   策略 ARN: $POLICY_ARN"
        echo "   请手动在 AWS Console 中附加策略"
        rm -f "$TMP_POLICY"
        exit 1
    fi
fi

# 清理临时文件
rm -f "$TMP_POLICY"

# 验证
echo ""
echo "================================"
echo -e "${GREEN}✅ 完成！${NC}"
echo ""
echo "💡 提示:"
echo "   - 权限更改可能需要 1-5 分钟才能生效"
echo "   - 验证权限: python3 scripts/diagnose_data_collection.py --date $(date +%Y-%m-%d)"
echo "   - 测试 S3 访问: aws s3 ls s3://${BUCKET_NAME}/"
if [ -n "$AWS_PROFILE" ]; then
    echo "   - 查看用户策略: aws --profile $AWS_PROFILE iam list-attached-user-policies --user-name $USER_NAME"
else
    echo "   - 查看用户策略: aws iam list-attached-user-policies --user-name $USER_NAME"
fi
echo ""
