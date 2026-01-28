#!/bin/bash
#
# 快速修复 S3 权限并启动数据收集器
# 解决两个常见问题：
# 1. S3 403 Forbidden 错误
# 2. Polygon 实时数据访问被拒绝（自动使用延迟数据）
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔧 快速修复和启动脚本"
echo "================================"
echo ""

# 步骤 1: 修复 S3 权限
echo -e "${BLUE}步骤 1: 检查并修复 S3 权限...${NC}"
if [ -f "scripts/fix_s3_permissions.sh" ]; then
    echo "   运行 S3 权限修复脚本..."
    ./scripts/fix_s3_permissions.sh
    echo ""
    echo -e "${YELLOW}⚠️  等待 10 秒让 IAM 权限生效...${NC}"
    sleep 10
else
    echo -e "${YELLOW}⚠️  找不到 fix_s3_permissions.sh 脚本${NC}"
    echo "   请手动运行: ./scripts/fix_s3_permissions.sh"
fi
echo ""

# 步骤 2: 设置延迟数据模式
echo -e "${BLUE}步骤 2: 配置延迟数据模式...${NC}"
if [ -z "$POLYGON_USE_DELAYED_WS" ]; then
    export POLYGON_USE_DELAYED_WS=true
    echo "   ✅ 设置 POLYGON_USE_DELAYED_WS=true (使用 15 分钟延迟数据)"
else
    echo "   ✅ POLYGON_USE_DELAYED_WS 已设置: $POLYGON_USE_DELAYED_WS"
fi
echo ""

# 步骤 3: 检查环境变量
echo -e "${BLUE}步骤 3: 检查必需的环境变量...${NC}"
MISSING_VARS=()

if [ -z "$POLYGON_API_KEY" ]; then
    MISSING_VARS+=("POLYGON_API_KEY")
fi

if [ -z "$AWS_S3_PULSE_BUCKET" ]; then
    MISSING_VARS+=("AWS_S3_PULSE_BUCKET")
fi

if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    MISSING_VARS+=("AWS_ACCESS_KEY_ID")
fi

if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    MISSING_VARS+=("AWS_SECRET_ACCESS_KEY")
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}❌ 缺少以下环境变量:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "请设置这些环境变量后重新运行此脚本"
    exit 1
else
    echo -e "${GREEN}✅ 所有必需的环境变量都已设置${NC}"
fi
echo ""

# 步骤 4: 启动数据收集器
echo -e "${BLUE}步骤 4: 启动数据收集器...${NC}"
echo ""
echo -e "${GREEN}🚀 启动数据收集器（使用延迟数据模式）...${NC}"
echo "   按 Ctrl+C 停止"
echo ""

# 运行数据收集器脚本（使用延迟模式）
python3 scripts/start_data_collector.py --delayed
