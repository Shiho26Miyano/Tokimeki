#!/bin/bash
# 检查策略是否已附加到用户

echo "🔍 检查 MarketPulseS3AccessPolicy 是否已附加..."
echo "=" | head -c 60 && echo ""
echo ""

# 加载 .env
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source <(grep -v '^#' "$ENV_FILE" | grep -v '^$' | sed 's/^/export /')
    set +a
fi

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "❌ AWS 凭证未设置"
    echo "   请设置 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY"
    exit 1
fi

echo "📋 检查步骤："
echo ""
echo "1. 在 AWS Console 中："
echo "   - 进入 IAM → Users"
echo "   - 找到使用这些凭证的用户"
echo "   - 点击用户名 → Permissions 标签"
echo "   - 检查 'Attached policies' 列表"
echo ""
echo "2. 确认 MarketPulseS3AccessPolicy 在列表中"
echo ""
echo "3. 如果不在列表中："
echo "   - 点击 'Add permissions' → 'Attach policies directly'"
echo "   - 搜索 'MarketPulseS3AccessPolicy'"
echo "   - 勾选并点击 'Add permissions'"
echo ""
echo "4. 如果策略已附加但仍然 403："
echo "   - 等待 2-5 分钟让权限生效"
echo "   - 重启应用"
echo ""
echo "💡 提示："
echo "   策略必须附加到使用这些凭证的用户"
echo "   如果凭证对应的用户和策略附加的用户不一致，就会 403"
