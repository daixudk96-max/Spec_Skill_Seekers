# fix-content-synthesizer-extraction

## Summary

修复 `ContentSynthesizer._get_source_text()` 无法正确处理数组格式的 `source_config.lessons.lessons` 结构，导致生成的 SKILL.md 和 references/*.md 文件显示原始 JSON 数据而非格式化 markdown 内容。

## Problem

### 现象
- SKILL.md 第 12-50 行显示原始 JSON 结构
- references/*.md 文件包含 `source_config` 的 JSON 序列化结果
- LLM 内容增强实际执行了，但输入的"源文本"是 JSON 而非可读文本

### 根本原因
`content_synthesizer.py#L94-123` 的 `_get_source_text()` 方法期望如下结构：
```python
# 预期结构 1
{"lessons": {"content": "原始文本字符串"}}

# 预期结构 2  
{"lessons": {"lessons": {"content": "原始文本字符串"}}}
```

但实际 `spec_enhanced.yaml` 的结构是：
```yaml
source_config:
  lessons:
    source_type: transcript
    lessons:           # <- 这是数组！
    - title: "第一部分"
      summary: "..."
      key_points: [...]
      segments: [...]
```

当找不到预期的 `content` 字段时，代码执行 fallback：
```python
return json.dumps(self.source_config, ensure_ascii=False, indent=2)
```

### 影响范围
- 所有使用 `segmented_summary.json` 增强的 transcript 工作流
- 已存档的 `add-transcript-semantic-segmentation` 变更引入了此数据结构

---

## Proposed Changes

### Core Module

#### [MODIFY] [content_synthesizer.py](file:///C:/open%20skills/Skill_Seekers/src/skill_seekers/core/content_synthesizer.py)

扩展 `_get_source_text()` 方法以支持数组格式的 lessons：

1. 检测 `lessons.lessons` 是否为 list
2. 如果是 list，遍历并拼接每个 lesson 的 `summary_full` / `summary` / `key_points`
3. 优先使用 `segments` 中的 `summary_full`（更详细）
4. 保持原有的 `content` 字符串格式兼容

---

### Test Updates

#### [MODIFY] [test_content_synthesizer.py](file:///C:/open%20skills/Skill_Seekers/tests/test_content_synthesizer.py)

添加新测试用例：

1. `test_extract_from_lessons_array` - 测试数组格式的 lessons 数据
2. `test_extract_from_segmented_summary` - 测试 segmented_summary 格式

---

## Verification Plan

### Automated Tests

```bash
# 运行现有和新增测试
pytest tests/test_content_synthesizer.py -v

# 运行完整测试套件确保无回归
pytest tests/ -v --ignore=tests/test_integration.py
```

### Manual Verification

使用现有的 `output/live-streaming-talent-v2/spec_enhanced.yaml` 重新生成 SKILL：

```bash
cd "C:\open skills\Skill_Seekers"
python -m skill_seekers apply-spec output/live-streaming-talent-v2/spec_enhanced.yaml --output output/live-streaming-talent-v3 --no-llm
```

验证标准：
1. `SKILL.md` 不应包含 `{"lessons": ...` 等 JSON 结构
2. 各章节应显示可读的中文内容摘要
3. `references/*.md` 应包含格式化的 markdown 而非 JSON

---

## User Review Required

> [!IMPORTANT]
> 此修复涉及 `_get_source_text()` 的核心逻辑变更，需确认是否还有其他使用此方法的场景需要兼容。
