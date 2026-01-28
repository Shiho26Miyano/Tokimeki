#!/bin/bash
#
# 一键修复 S3 权限并触发 Lambda Agents
# 解决 Dashboard 显示"数据未就绪"的问题
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔧 一键修复和触发脚本"
echo "================================"
echo ""

# 步骤 1: 修复 S3 权限
echo -e "${BLUE}步骤 1: 修复 S3 权限...${NC}"
if [ -f "scripts/fix_s3_permissions.sh" ]; then
    ./scripts/fix_s3_permissions.sh
    echo ""
    echo -e "${YELLOW}等待 15 秒让 IAM 权限生效...${NC}"
    sleep 15
else
    echo -e "${YELLOW}⚠️  找不到 fix_s3_permissions.sh${NC}"
fi
echo ""

# 步骤 2: 验证 S3 访问
echo -e "${BLUE}步骤 2: 验证 S3 访问...${NC}"
if aws s3 ls s3://tokimeki-market-pulse-prod/ &> /dev/null; then
    echo -e "${GREEN}✅ S3 访问正常${NC}"
else
    echo -e "${RED}❌ S3 访问失败${NC}"
    echo "   请检查权限是否已正确配置"
    echo "   或手动运行: ./scripts/fix_s3_permissions.sh"
    exit 1
fi
echo ""

# 步骤 3: 触发 Compute Agent
echo -e "${BLUE}步骤 3: 触发 Compute Agent...${NC}"
DATE=$(date -u +%Y-%m-%d)
if python3 scripts/trigger_lambda_agents.py --compute --date "$DATE" 2>&1 | tee /tmp/compute_output.log; then
    echo -e "${GREEN}✅ Compute Agent 已触发${NC}"
else
    echo -e "${YELLOW}⚠️  Compute Agent 可能失败，检查日志:${NC}"
    cat /tmp/compute_output.log | tail -20
fi
echo ""

# 等待一下
echo "等待 5 秒..."
sleep 5
echo ""

# 步骤 4: 触发 Learning Agent
echo -e "${BLUE}步骤 4: 触发 Learning Agent...${NC}"
if python3 scripts/trigger_lambda_agents.py --learning --date "$DATE" 2>&1 | tee /tmp/learning_output.log; then
    echo -e "${GREEN}✅ Learning Agent 已触发${NC}"
else
    echo -e "${YELLOW}⚠️  Learning Agent 可能失败，检查日志:${NC}"
    cat /tmp/learning_output.log | tail -20
fi
echo ""

# 步骤 5: 验证数据
echo -e "${BLUE}步骤 5: 验证数据...${NC}"
echo "检查 S3 中的数据..."
python3 scripts/view_s3_data.py --check-dashboard --date "$DATE" 2>&1 | tail -30
echo ""

# 总结
echo "================================"
echo -e "${GREEN}✅ 完成！${NC}"
echo ""
echo "💡 下一步:"
echo "   1. 刷新 Dashboard 页面"
echo "   2. 如果还是没有数据，检查:"
echo "      - Lambda 函数是否正确部署"
echo "      - Lambda 函数是否有 S3 读写权限"
echo "      - 原始数据是否存在: aws s3 ls s3://tokimeki-market-pulse-prod/raw-data/$DATE/"
echo ""
