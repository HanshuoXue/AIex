# Program Match Flow

这是一个基于 Prompt Flow 的智能程序匹配系统，使用 LLM 来评估候选人与新西兰大学项目的匹配度。

## 文件结构

- `flow.dag.yaml` - Prompt Flow 流程定义
- `match_prompt.jinja2` - LLM 提示模板
- `match_evaluator.py` - Python 处理逻辑
- `requirements.txt` - 依赖包
- `data.jsonl` - 测试数据
- `README.md` - 说明文档

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置连接

在 Prompt Flow 中配置 Azure OpenAI 连接：

```bash
pf connection create --file azure_openai_connection.yaml
```

### 3. 测试流程

```bash
# 测试单个样例
pf flow test --flow . --inputs candidate_profile='{"bachelor_major":"computer science",...}' program_details='{"program":"Master of CS",...}'

# 批量测试
pf flow test --flow . --data data.jsonl
```

### 4. 运行流程

```bash
pf flow run --flow . --data data.jsonl --stream
```

## API 集成

流程已集成到 FastAPI 中，提供以下端点：

- `POST /match` - 使用 Prompt Flow 的智能匹配
- `POST /match/detailed` - 返回详细评估结果
- `POST /match/legacy` - 原有规则引擎匹配（备用）

## 评分标准

- **学术匹配 (35 分)**: GPA 兼容性、学术背景相关性
- **英语能力 (25 分)**: IELTS 总分和分项要求
- **兴趣匹配 (20 分)**: 候选人兴趣与项目领域重合度
- **地理偏好 (10 分)**: 城市/校区偏好匹配
- **预算兼容 (10 分)**: 学费与预算的匹配度

## 输出格式

```json
{
  "eligible": true,
  "overall_score": 85,
  "detailed_scores": {
    "academic_fit": 30,
    "english_proficiency": 22,
    "field_alignment": 18,
    "location_preference": 8,
    "budget_compatibility": 7
  },
  "reasoning": {
    "academic_fit": "Strong CS background matches program requirements",
    "english_proficiency": "IELTS score exceeds minimum requirements",
    "field_alignment": "High overlap in AI/ML interests",
    "location_preference": "Auckland preference matches campus location",
    "budget_compatibility": "Budget slightly below tuition but manageable",
    "overall_assessment": "Excellent match with strong academic fit and aligned interests"
  },
  "red_flags": [],
  "strengths": [
    "Strong technical background",
    "Relevant work experience",
    "High English proficiency"
  ]
}
```

## 注意事项

1. 确保 Azure OpenAI 连接配置正确
2. 输入数据必须是有效的 JSON 字符串格式
3. 流程会自动处理评估错误并返回默认响应
4. 可以根据需要调整提示模板中的评分标准
