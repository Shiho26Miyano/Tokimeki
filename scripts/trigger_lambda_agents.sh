#!/bin/bash
#
# 手动触发 Compute Agent 和 Learning Agent Lambda 函数
#
# 用法:
#   ./scripts/trigger_lambda_agents.sh                    # 触发两个agent（使用今天日期）
#   ./scripts/trigger_lambda_agents.sh --compute           # 只触发 Compute Agent
#   ./scripts/trigger_lambda_agents.sh --learning          # 只触发 Learning Agent
#   ./scripts/trigger_lambda_agents.sh --date 2026-01-26   # 指定日期
#

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Lambda 函数名称
COMPUTE_FUNCTION_NAME="market-pulse-compute-agent"
LEARNING_FUNCTION_NAME="market-pulse-learning-agent"

# AWS 区域（从环境变量或默认值）
AWS_REGION="${AWS_REGION:-us-east-2}"

# 默认日期（今天）
DATE=$(date -u +%Y-%m-%d)

# 解析参数
TRIGGER_COMPUTE=false
TRIGGER_LEARNING=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --compute)
            TRIGGER_COMPUTE=true
            shift
            ;;
        --learning)
            TRIGGER_LEARNING=true
            shift
            ;;
        --date)
            DATE="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --compute          只触发 Compute Agent"
            echo "  --learning         只触发 Learning Agent"
            echo "  --date DATE        指定日期 (YYYY-MM-DD)，默认今天"
            echo "  --region REGION    AWS 区域，默认 us-east-2"
            echo "  -h, --help        显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                          # 触发两个agent（今天）"
            echo "  $0 --compute                # 只触发 Compute Agent"
            echo "  $0 --date 2026-01-26        # 指定日期触发两个agent"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 如果没有指定，默认触发两个
if [ "$TRIGGER_COMPUTE" = false ] && [ "$TRIGGER_LEARNING" = false ]; then
    TRIGGER_COMPUTE=true
    TRIGGER_LEARNING=true
fi

echo "🚀 手动触发 Lambda Agents"
echo "================================"
echo "日期: $DATE"
echo "区域: $AWS_REGION"
echo ""

# 检查 AWS CLI 是否安装
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI 未安装${NC}"
    echo "   请安装: https://aws.amazon.com/cli/"
    exit 1
fi

# 检查 AWS 凭证
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS 凭证未配置${NC}"
    echo "   请配置 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY"
    exit 1
fi

# 创建临时目录存储响应
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

# ============================================================================
# 触发 Compute Agent
# ============================================================================

if [ "$TRIGGER_COMPUTE" = true ]; then
    echo -e "${BLUE}⚡ 触发 Compute Agent...${NC}"
    echo "   函数名: $COMPUTE_FUNCTION_NAME"
    
    # 检查函数是否存在
    if ! aws lambda get-function --function-name "$COMPUTE_FUNCTION_NAME" --region "$AWS_REGION" &> /dev/null; then
        echo -e "${RED}❌ Lambda 函数不存在: $COMPUTE_FUNCTION_NAME${NC}"
        echo "   请先部署 Lambda 函数"
        exit 1
    fi
    
    # 创建 payload
    PAYLOAD=$(cat <<EOF
{
    "date": "$DATE"
}
EOF
)
    
    # 触发 Lambda
    RESPONSE_FILE="$TMP_DIR/compute-response.json"
    if aws lambda invoke \
        --function-name "$COMPUTE_FUNCTION_NAME" \
        --payload "$PAYLOAD" \
        --region "$AWS_REGION" \
        "$RESPONSE_FILE" &> /dev/null; then
        
        # 显示结果
        if [ -f "$RESPONSE_FILE" ]; then
            echo -e "${GREEN}✅ Compute Agent 执行完成${NC}"
            echo "   响应:"
            cat "$RESPONSE_FILE" | python3 -m json.tool 2>/dev/null || cat "$RESPONSE_FILE"
            echo ""
        fi
    else
        echo -e "${RED}❌ Compute Agent 执行失败${NC}"
        echo "   查看日志: aws logs tail /aws/lambda/$COMPUTE_FUNCTION_NAME --follow --region $AWS_REGION"
        exit 1
    fi
fi

# ============================================================================
# 触发 Learning Agent
# ============================================================================

if [ "$TRIGGER_LEARNING" = true ]; then
    echo -e "${BLUE}🧠 触发 Learning Agent...${NC}"
    echo "   函数名: $LEARNING_FUNCTION_NAME"
    
    # 检查函数是否存在
    if ! aws lambda get-function --function-name "$LEARNING_FUNCTION_NAME" --region "$AWS_REGION" &> /dev/null; then
        echo -e "${RED}❌ Lambda 函数不存在: $LEARNING_FUNCTION_NAME${NC}"
        echo "   请先部署 Lambda 函数"
        exit 1
    fi
    
    # 创建 payload
    PAYLOAD=$(cat <<EOF
{
    "date": "$DATE"
}
EOF
)
    
    # 触发 Lambda
    RESPONSE_FILE="$TMP_DIR/learning-response.json"
    if aws lambda invoke \
        --function-name "$LEARNING_FUNCTION_NAME" \
        --payload "$PAYLOAD" \
        --region "$AWS_REGION" \
        "$RESPONSE_FILE" &> /dev/null; then
        
        # 显示结果
        if [ -f "$RESPONSE_FILE" ]; then
            echo -e "${GREEN}✅ Learning Agent 执行完成${NC}"
            echo "   响应:"
            cat "$RESPONSE_FILE" | python3 -m json.tool 2>/dev/null || cat "$RESPONSE_FILE"
            echo ""
        fi
    else
        echo -e "${RED}❌ Learning Agent 执行失败${NC}"
        echo "   查看日志: aws logs tail /aws/lambda/$LEARNING_FUNCTION_NAME --follow --region $AWS_REGION"
        exit 1
    fi
fi

# ============================================================================
# 总结
# ============================================================================

echo "================================"
echo -e "${GREEN}✅ 完成！${NC}"
echo ""
echo "💡 提示:"
echo "   - 检查 S3 数据: python3 scripts/view_s3_data.py --check-dashboard --date $DATE"
echo "   - 查看 Compute Agent 日志: aws logs tail /aws/lambda/$COMPUTE_FUNCTION_NAME --follow --region $AWS_REGION"
echo "   - 查看 Learning Agent 日志: aws logs tail /aws/lambda/$LEARNING_FUNCTION_NAME --follow --region $AWS_REGION"
