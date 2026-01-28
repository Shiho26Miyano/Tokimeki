#!/bin/bash
#
# 重新创建 S3 IAM 策略
# 删除旧策略并创建新策略
#
# 用法:
#   ./scripts/recreate_s3_policy.sh                    # 使用默认配置
#   ./scripts/recreate_s3_policy.sh --bucket my-bucket # 指定 bucket
#   ./scripts/recreate_s3_policy.sh --profile admin    # 使用 AWS profile
#   ./scripts/recreate_s3_policy.sh --keep-old        # 保留旧版本（不删除）
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
KEEP_OLD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            export AWS_PROFILE
            shift 2
            ;;
        --bucket)
            BUCKET_NAME="$2"
            shift 2
            ;;
        --keep-old)
            KEEP_OLD=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--profile PROFILE] [--bucket BUCKET] [--keep-old]"
            exit 1
            ;;
    esac
done

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

echo "🔄 重新创建 S3 IAM 策略"
echo "================================"
echo "策略名称: $POLICY_NAME"
echo "IAM 用户: $USER_NAME"
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

# 步骤 1: 检查策略是否存在
echo -e "${BLUE}步骤 1: 检查现有策略...${NC}"
if $AWS_CMD iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    echo -e "${YELLOW}⚠️  策略已存在: $POLICY_NAME${NC}"
    
    # 检查是否附加到用户
    ATTACHED=$($AWS_CMD iam list-attached-user-policies \
        --user-name "$USER_NAME" \
        --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$ATTACHED" ]; then
        echo -e "${YELLOW}⚠️  策略已附加到用户: $USER_NAME${NC}"
        echo "   先分离策略..."
        $AWS_CMD iam detach-user-policy \
            --user-name "$USER_NAME" \
            --policy-arn "$POLICY_ARN" 2>/dev/null || true
        echo -e "${GREEN}✅ 策略已分离${NC}"
    fi
    
    # 列出所有版本
    echo "   列出策略版本..."
    VERSIONS=$($AWS_CMD iam list-policy-versions \
        --policy-arn "$POLICY_ARN" \
        --query 'Versions[?IsDefaultVersion==`false`].VersionId' \
        --output text 2>/dev/null || echo "")
    
    # 删除旧版本（如果不需要保留）
    if [ "$KEEP_OLD" = false ] && [ -n "$VERSIONS" ]; then
        echo "   删除旧版本..."
        for VERSION in $VERSIONS; do
            echo "     删除版本: $VERSION"
            $AWS_CMD iam delete-policy-version \
                --policy-arn "$POLICY_ARN" \
                --version-id "$VERSION" 2>/dev/null || true
        done
    fi
    
    # 删除策略（IAM 策略最多保留 5 个版本，需要先删除所有非默认版本）
    echo "   删除策略..."
    # 先删除默认版本
    DEFAULT_VERSION=$($AWS_CMD iam get-policy \
        --policy-arn "$POLICY_ARN" \
        --query 'Policy.DefaultVersionId' \
        --output text)
    
    if [ "$KEEP_OLD" = false ]; then
        # 删除默认版本（需要先删除所有其他版本）
        # 如果还有其他版本，先删除它们
        ALL_VERSIONS=$($AWS_CMD iam list-policy-versions \
            --policy-arn "$POLICY_ARN" \
            --query 'Versions[].VersionId' \
            --output text 2>/dev/null || echo "")
        
        for VERSION in $ALL_VERSIONS; do
            if [ "$VERSION" != "$DEFAULT_VERSION" ]; then
                $AWS_CMD iam delete-policy-version \
                    --policy-arn "$POLICY_ARN" \
                    --version-id "$VERSION" 2>/dev/null || true
            fi
        done
        
        # 现在删除默认版本
        $AWS_CMD iam delete-policy-version \
            --policy-arn "$POLICY_ARN" \
            --version-id "$DEFAULT_VERSION" 2>/dev/null || true
        
        # 删除策略
        $AWS_CMD iam delete-policy --policy-arn "$POLICY_ARN" 2>/dev/null || true
        echo -e "${GREEN}✅ 旧策略已删除${NC}"
    else
        echo -e "${YELLOW}⚠️  保留旧策略（使用 --keep-old 选项）${NC}"
        echo "   将创建新版本..."
    fi
else
    echo -e "${GREEN}✅ 策略不存在，将创建新策略${NC}"
fi

echo ""

# 步骤 2: 创建新策略文档
echo -e "${BLUE}步骤 2: 创建新策略文档...${NC}"
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

# 步骤 3: 创建策略
echo -e "${BLUE}步骤 3: 创建策略...${NC}"
if [ "$KEEP_OLD" = true ] && $AWS_CMD iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    # 创建新版本
    NEW_VERSION=$($AWS_CMD iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document "file://$TMP_POLICY" \
        --set-as-default \
        --query 'PolicyVersion.VersionId' \
        --output text)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 策略版本已创建${NC}"
        echo "   新版本: $NEW_VERSION"
    else
        echo -e "${RED}❌ 创建策略版本失败${NC}"
        rm -f "$TMP_POLICY"
        exit 1
    fi
else
    # 创建新策略
    $AWS_CMD iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document "file://$TMP_POLICY" \
        --description "Allow S3 access for Market Pulse bucket (recreated)" \
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

# 清理临时文件
rm -f "$TMP_POLICY"

# 步骤 4: 附加策略到用户
echo ""
echo -e "${BLUE}步骤 4: 附加策略到用户...${NC}"

# 检查用户是否存在
if ! $AWS_CMD iam get-user --user-name "$USER_NAME" &> /dev/null; then
    echo -e "${YELLOW}⚠️  IAM 用户不存在: $USER_NAME${NC}"
    echo "   策略已创建，但需要手动附加到用户"
    echo "   策略 ARN: $POLICY_ARN"
    exit 0
fi

# 附加策略
$AWS_CMD iam attach-user-policy \
    --user-name "$USER_NAME" \
    --policy-arn "$POLICY_ARN"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 策略已附加到用户${NC}"
else
    echo -e "${RED}❌ 附加策略失败${NC}"
    echo "   可能需要管理员权限"
    echo "   策略 ARN: $POLICY_ARN"
    exit 1
fi

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
    echo "   - 查看策略: aws --profile $AWS_PROFILE iam get-policy --policy-arn $POLICY_ARN"
    echo "   - 查看用户策略: aws --profile $AWS_PROFILE iam list-attached-user-policies --user-name $USER_NAME"
else
    echo "   - 查看策略: aws iam get-policy --policy-arn $POLICY_ARN"
    echo "   - 查看用户策略: aws iam list-attached-user-policies --user-name $USER_NAME"
fi
echo ""
