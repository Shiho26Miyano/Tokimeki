# 修复 Lambda 函数名称不匹配问题

## 问题

如果您的 Lambda 函数已经部署，但脚本显示"函数不存在"，可能是因为：

1. **函数名称不同** - 例如您创建的函数名是 `market-pulse-compute` 而不是 `market-pulse-compute-agent`
2. **区域不同** - 函数在不同的 AWS 区域
3. **账户不同** - 使用了不同的 AWS 凭证

## 解决方案

### 步骤 1: 查找实际的函数名称

运行查找脚本：

```bash
python3 scripts/find_lambda_functions.py
```

这会显示所有 Lambda 函数，特别是 Market Pulse 相关的函数。

### 步骤 2: 更新配置

如果函数名称不同，有两种方法：

#### 方法 A: 使用环境变量（临时）

```bash
export COMPUTE_FUNCTION_NAME=your-actual-compute-function-name
export LEARNING_FUNCTION_NAME=your-actual-learning-function-name
export AWS_REGION=your-region

python3 scripts/check_lambda_status.py
python3 scripts/trigger_lambda_agents.py
```

#### 方法 B: 使用配置脚本（持久）

```bash
./scripts/update_lambda_config.sh \
  --compute-name your-actual-compute-function-name \
  --learning-name your-actual-learning-function-name \
  --region your-region

# 然后加载配置
source .lambda-config

# 使用脚本
python3 scripts/check_lambda_status.py
python3 scripts/trigger_lambda_agents.py
```

### 步骤 3: 验证

运行检查脚本验证函数是否存在：

```bash
python3 scripts/check_lambda_status.py
```

应该显示：
- ✅ Compute Agent: 已部署
- ✅ Learning Agent: 已部署

## 常见函数名称变体

如果您的函数名称类似以下之一，请使用相应的名称：

- `market-pulse-compute` (而不是 `market-pulse-compute-agent`)
- `market-pulse-learning` (而不是 `market-pulse-learning-agent`)
- `compute-agent` (而不是 `market-pulse-compute-agent`)
- `learning-agent` (而不是 `market-pulse-learning-agent`)

## 检查所有区域

如果函数在不同区域，可以检查所有区域：

```bash
python3 scripts/find_lambda_functions.py --all-regions
```

## 更新脚本中的默认值

如果您想永久更改默认函数名称，编辑以下文件：

- `scripts/trigger_lambda_agents.py` - 第 27-28 行
- `scripts/check_lambda_status.py` - 第 27-28 行
- `scripts/deploy-lambda-functions.sh` - 第 21-22 行

## 示例

假设您的函数名称是：
- Compute Agent: `market-pulse-compute`
- Learning Agent: `market-pulse-learning`
- 区域: `us-east-1`

```bash
# 方法 1: 环境变量
export COMPUTE_FUNCTION_NAME=market-pulse-compute
export LEARNING_FUNCTION_NAME=market-pulse-learning
export AWS_REGION=us-east-1
python3 scripts/trigger_lambda_agents.py

# 方法 2: 配置脚本
./scripts/update_lambda_config.sh \
  --compute-name market-pulse-compute \
  --learning-name market-pulse-learning \
  --region us-east-1
source .lambda-config
python3 scripts/trigger_lambda_agents.py
```
