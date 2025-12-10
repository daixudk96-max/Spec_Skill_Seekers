# Design: Content Filling for Spec-Driven Workflow

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      apply-spec CLI                          │
│              skill-seekers apply-spec spec.yaml              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  UnifiedSkillBuilder                         │
│         build_from_spec() orchestrates generation            │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌────────────┐  ┌─────────────┐  ┌─────────────┐
   │ SKILL.md   │  │ references/ │  │  scripts/   │
   │ Generator  │  │  Generator  │  │  Generator  │
   └─────┬──────┘  └──────┬──────┘  └─────────────┘
         │                │
         ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                  ContentSynthesizer                          │
│       synthesize_section_content()                           │
│       synthesize_reference_content()                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────┐     │
│  │  LLM Provider   │    │  Fallback Extractor         │     │
│  │ (Claude API)    │    │  (Pattern-based extraction) │     │
│  └─────────────────┘    └─────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      source_config                           │
│  (from SkillSpec, contains raw transcript/lesson data)       │
└─────────────────────────────────────────────────────────────┘
```

## ContentSynthesizer Design

### Class Signature

```python
class ContentSynthesizer:
    def __init__(
        self,
        spec: SkillSpec,
        source_config: Dict[str, Any],
        use_llm: bool = True,
    ):
        self.spec = spec
        self.source_config = source_config
        self.use_llm = use_llm and self._check_api_key()
        self._llm_client = None
    
    def synthesize_section_content(
        self,
        section: SectionSpec,
    ) -> str:
        """Generate actual content for a section."""
        ...
    
    def synthesize_reference_content(
        self,
        ref: ReferenceSpec,
    ) -> str:
        """Generate content for a reference file."""
        ...
```

### Content Generation Strategy by Section Purpose

| Section Purpose | LLM Mode | Fallback Mode |
|----------------|----------|---------------|
| 课程摘要 (Summary) | 从 transcript 生成 2-3 段概述 | 提取 transcript 前 500 字 |
| 关键要点 (Key Points) | 识别并列出 5-10 个要点 | 提取带时间戳的段落标题 |
| 核心概念详解 | 深度解释 3-5 个概念 | 提取包含"概念"/"定义"的段落 |
| 实践练习 | 生成 3 道练习题 + 答案 | 跳过（标记为"需 LLM 生成"）|
| 延伸学习 | 推荐相关资源 | 跳过 |
| Overview | 总结原始文档 | 原始 README 内容 |

### LLM Prompt Template

```python
SECTION_PROMPT_TEMPLATE = """
你是一个教育内容专家。根据以下原始材料，为 "{section_title}" 章节生成内容。

**章节目标**: {section_purpose}

**期望内容**:
{expected_content_list}

**原始材料** (课程转录文本):
{source_content}

请生成专业、简洁、有教育价值的内容。使用 markdown 格式。
"""
```

### Fallback Extraction Logic

```python
def _extract_fallback_content(self, section: SectionSpec) -> str:
    """Deterministic extraction when LLM unavailable."""
    source_text = self._get_source_text()
    
    # 根据 section title 选择提取策略
    if "摘要" in section.title or "Overview" in section.title:
        return self._extract_summary(source_text, max_chars=500)
    elif "要点" in section.title or "Key" in section.title:
        return self._extract_key_points(source_text)
    elif "概念" in section.title:
        return self._extract_concepts(source_text)
    else:
        return f"*[需要 LLM 增强以生成 {section.title} 内容]*\n"
```

## Integration with UnifiedSkillBuilder

### Modified _format_section_from_spec

```python
def _format_section_from_spec(self, section: SectionSpec) -> str:
    """Format a SectionSpec into markdown content with actual content."""
    content = f"{section.title}\n\n"
    
    # NEW: Generate actual content via synthesizer
    if self.content_synthesizer:
        generated_content = self.content_synthesizer.synthesize_section_content(section)
        content += generated_content + "\n\n"
    else:
        # Fallback to old placeholder behavior
        if section.purpose:
            content += f"*{section.purpose}*\n\n"
        if section.expected_content:
            content += "Expected content:\n"
            for item in section.expected_content:
                content += f"- {item}\n"
            content += "\n"
    
    # Recursively add subsections
    for subsection in section.subsections:
        content += self._format_section_from_spec(subsection)
    
    return content
```

## Error Handling

1. **No API Key**: 自动降级到 fallback 模式，记录 warning
2. **API Error**: 降级到 fallback 模式，继续生成
3. **Empty source_config**: 使用占位符 + warning
4. **Rate Limit**: 实现重试逻辑 with exponential backoff

## Performance Considerations

- LLM 调用针对每个 section 单独进行（允许并行）
- 大 transcript 需分块处理（max 4000 chars per section）
- 缓存生成结果避免重复调用

## Backward Compatibility

- 如果 `content_synthesizer` 为 None，保持现有占位符行为
- 新增 `--no-llm` CLI 标志强制 fallback 模式
- 不修改 SkillSpec 数据模型
