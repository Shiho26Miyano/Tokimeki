#!/bin/bash
#
# 快速修复 S3 ListBucket 权限问题
# 解决 "no identity-based policy allows the s3:ListBucket action" 错误
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔧 快速修复 S3 ListBucket 权限"
echo "================================"
echo ""

# 配置
USER_NAME="tokimeki-pulse-writer"
POLICY_NAME="MarketPulseS3AccessPolicy"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-989513605244}"
BUCKET_NAME="${AWS_S3_PULSE_BUCKET:-tokimeki-market-pulse-prod}"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

# 检查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI 未安装${NC}"
    exit 1
fi

# 检查 AWS 凭证
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS 凭证未配置${NC}"
    exit 1
fi

echo -e "${BLUE}📝 创建更新的策略文档（包含根目录 ListBucket 权限）...${NC}"
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

# 检查策略是否存在
if aws iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    echo -e "${YELLOW}⚠️  策略已存在，更新策略...${NC}"
    
    # 创建新版本
    NEW_VERSION=$(aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document "file://$TMP_POLICY" \
        --set-as-default \
        --query 'PolicyVersion.VersionId' \
        --output text 2>/dev/null)
    
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
    aws iam create-policy \
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
    
    # 附加到用户
    echo -e "${BLUE}🔗 附加策略到用户...${NC}"
    aws iam attach-user-policy \
        --user-name "$USER_NAME" \
        --policy-arn "$POLICY_ARN"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 策略已附加到用户${NC}"
    else
        echo -e "${RED}❌ 附加策略失败${NC}"
        rm -f "$TMP_POLICY"
        exit 1
    fi
fi

# 清理
rm -f "$TMP_POLICY"

echo ""
echo "================================"
echo -e "${GREEN}✅ 完成！${NC}"
echo ""
echo "💡 提示:"
echo "   - 等待 10-30 秒让权限生效"
echo "   - 然后测试: aws s3 ls s3://${BUCKET_NAME}/"
echo ""
