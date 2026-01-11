# 体重数据过滤配置说明

本工具支持在同步数据到佳明之前，根据您的健康指标过滤体重数据。您可以为每个账户配置独立的过滤规则。

## 功能说明

通过配置过滤器，您可以：
- 只同步特定体重范围内的数据（如：体重在 60-70kg 之间）
- 根据体脂率、BMI 等多个指标组合过滤
- 避免同步异常或不完整的数据记录
- 为不同家庭成员设置不同的过滤规则

## 配置方法

在 `users.json` 文件中，为每个用户的 `garmin` 配置添加 `filter` 字段：

```json
{
    "users": [
        {
            "username": "您的手机号/邮箱",
            "password": "小米账号密码",
            "model": "yunmai.scales.ms103",
            "token": { ... },
            "garmin": {
                "email": "您的佳明账号",
                "password": "佳明账号密码",
                "domain": "CN",
                "filter": {
                    "enabled": true,
                    "conditions": [
                        { "field": "Weight", "operator": "between", "value": [60, 70] }
                    ],
                    "logic": "and"
                }
            }
        }
    ]
}
```

## 配置参数详解

### filter 对象结构

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `enabled` | boolean | 否 | 是否启用过滤，默认 `true` |
| `conditions` | array | 是 | 过滤条件数组，支持多个条件 |
| `logic` | string | 否 | 多条件逻辑关系，`"and"` 或 `"or"`，默认 `"and"` |

### 条件 (condition) 对象结构

每个条件包含以下字段：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `field` | string | 是 | 要过滤的字段名（见下方支持字段） |
| `operator` | string | 是 | 比较操作符（见下方支持操作符） |
| `value` | number/array | 是 | 比较值（`between` 操作符需要两个值的数组） |

## 支持的字段

| 字段名 | 说明 | 数据类型 | 示例值 |
|--------|------|----------|--------|
| `Weight` | 体重 | float | 70.5 (kg) |
| `BMI` | 体脂率 | float | 23.8 |
| `BodyFat` | 身体质量指数 | float | 15.2 (%) |
| `BodyWater` | 体水率 | float | 58.3 (%) |
| `BoneMass` | 骨量 | float | 2.8 (kg) |
| `MetabolicAge` | 代谢年龄 | int | 28 (岁) |
| `MuscleMass` | 肌肉量 | float | 30.1 (kg) |
| `VisceralFat` | 内脏脂肪等级 | int | 5 |
| `BasalMetabolism` | 基础代谢 | int | 1650 (kcal) |

## 支持的操作符

| 操作符 | 说明 | 示例 |
|--------|------|------|
| `eq` | 等于 | `{ "field": "Weight", "operator": "eq", "value": 70 }` |
| `ne` | 不等于 | `{ "field": "Weight", "operator": "ne", "value": 70 }` |
| `gt` | 大于 | `{ "field": "Weight", "operator": "gt", "value": 70 }` |
| `gte` | 大于等于 | `{ "field": "Weight", "operator": "gte", "value": 60 }` |
| `lt` | 小于 | `{ "field": "Weight", "operator": "lt", "value": 80 }` |
| `lte` | 小于等于 | `{ "field": "Weight", "operator": "lte", "value": 70 }` |
| `between` | 在范围内（包含边界值） | `{ "field": "Weight", "operator": "between", "value": [60, 70] }` |

## 配置示例

### 示例 1：只同步体重在 60-70kg 之间的数据

```json
"filter": {
    "enabled": true,
    "conditions": [
        { "field": "Weight", "operator": "between", "value": [60, 70] }
    ],
    "logic": "and"
}
```

### 示例 2：体重 >= 60kg 且体脂率 < 25%

```json
"filter": {
    "enabled": true,
    "conditions": [
        { "field": "Weight", "operator": "gte", "value": 60 },
        { "field": "BodyFat", "operator": "lt", "value": 25 }
    ],
    "logic": "and"
}
```

### 示例 3：体重 < 60kg 或体重 > 80kg

```json
"filter": {
    "enabled": true,
    "conditions": [
        { "field": "Weight", "operator": "lt", "value": 60 },
        { "field": "Weight", "operator": "gt", "value": 80 }
    ],
    "logic": "or"
}
```

### 示例 4：BMI 在正常范围（18.5 - 24）

```json
"filter": {
    "enabled": true,
    "conditions": [
        { "field": "BMI", "operator": "between", "value": [18.5, 24] }
    ],
    "logic": "and"
}
```

### 示例 5：禁用过滤（同步所有数据）

```json
"filter": {
    "enabled": false
}
```

或者直接删除 `filter` 字段，系统将同步所有数据。

## 向后兼容性

- 如果 `filter` 字段不存在，系统会同步所有数据（默认行为）
- 如果 `filter.enabled` 为 `false`，过滤规则不会生效
- 过滤功能出错时，系统会记录错误并继续使用原始数据同步，不会中断同步流程

## 日志输出

启用过滤后，程序会输出详细的过滤信息：

```
INFO - Weight filter enabled: 2 condition(s) with 'AND' logic
INFO - Applying weight filter with 2 condition(s) using 'AND' logic
INFO - Filter applied: 15/20 records passed (5 filtered out)
INFO - Filter reduced records from 20 to 15 (5 filtered out)
```

## 常见问题

### Q: 如果所有数据都被过滤掉了怎么办？

A: 程序会生成空 FIT 文件并记录警告。您可以检查过滤配置是否过于严格，或查看原始数据是否符合条件。

### Q: 过滤配置错误会导致同步失败吗？

A: 不会。如果过滤配置有误，程序会记录错误并跳过过滤功能，继续使用原始数据同步。

### Q: 可以为不同用户设置不同的过滤规则吗？

A: 可以。`filter` 配置是针对每个佳明用户的，您可以为每个家庭成员设置不同的过滤条件。

### Q: 支持时间范围过滤吗？

A: 当前版本不支持时间范围过滤。如果需要此功能，请提交 issue 或 PR。
