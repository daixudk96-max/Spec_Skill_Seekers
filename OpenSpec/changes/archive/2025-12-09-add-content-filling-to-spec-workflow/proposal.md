# Add Content Filling to Spec-Driven Workflow

## Summary

`build_from_spec()` 目前只生成模板框架（章节标题、purpose 说明、expected_content 提示），但**没有从 `source_config` 实际提取内容来填充章节**。这违背了 spec-first-skill-workflow spec 中"Apply spec to generate complete skill folder"的要求。

## Problem Statement

当用户运行 `skill-seekers apply-spec output/skill/spec.yaml` 时：

**期望行为：**
- SKILL.md 应包含从 source_config（如 transcript 内容）实际生成的内容
- references/ 下的文件应包含提取/总结的实际内容
- 各章节应有具体的课程摘要、关键要点、练习题等

**实际行为：**
- SKILL.md 只输出模板提示如 `*2-3段课程概述，核心主题和价值*` 和 `Expected content: - 课程背景 - 核心主题`
- references/ 文件只包含 `<!-- TODO: Populate with content from scraped data -->`
- 没有任何实际内容被提取或生成

## Root Cause

在 `src/skill_seekers/cli/unified_skill_builder.py` 中：

1. **`_format_section_from_spec()`** (L196-219): 只输出 section 的 purpose 和 expected_content 作为占位符
2. **`_generate_references_from_spec()`** (L221-243): 只写入 TODO 注释而非实际内容
3. **`_generate_skill_md_from_spec()`** (L129-194): 不访问 `source_config` 数据

## Proposed Solution

采用**混合方法（Hybrid Approach）**：

1. **确定性提取**：对结构化数据（课程标题、时间戳、原始 transcript 块）直接提取
2. **LLM 增强**：对需要综合的章节（摘要、要点、练习题）使用 Claude API 生成
3. **优雅降级**：当 API 不可用时，回退到确定性提取而非空内容

### Content Synthesizer

实现一个 `ContentSynthesizer` 类：
- 接收 SkillSpec + source_config
- 根据 section.purpose 和 section.expected_content 生成实际内容
- 支持 LLM 模式和 fallback 模式

## Scope

### In Scope
- 修改 `UnifiedSkillBuilder` 以支持内容填充
- 新增 `ContentSynthesizer` 组件
- 更新 `_format_section_from_spec()` 以生成实际内容
- 更新 `_generate_references_from_spec()` 以填充参考文件

### Out of Scope
- MCP 工具集成（保持现有 CLI 工作流）
- 新增 CLI 命令（使用现有 apply-spec）
- 修改 SkillSpec 数据结构

## Dependencies

- 依赖现有 `TranscriptScraper._enhance_with_llm()` 的 prompt 模式
- 需要 ANTHROPIC_API_KEY 环境变量（可选，用于 LLM 模式）

## Related Changes

- 修改 spec-first-skill-workflow spec，新增 content-filling 能力
