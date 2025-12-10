# Tasks for add-content-filling-to-spec-workflow

## 1. Core Implementation

### 1.1 Create ContentSynthesizer Class
- [x] 创建 `src/skill_seekers/core/content_synthesizer.py`
- [x] 实现 `ContentSynthesizer` 类，接收 SkillSpec 和 source_config
- [x] 实现 `synthesize_section_content()` 方法 - 根据 section 定义生成内容
- [x] 实现 `synthesize_reference_content()` 方法 - 填充参考文件
- [x] 实现 LLM 调用逻辑（复用 TranscriptScraper 的 prompt 模式）
- [x] 实现 fallback 模式（无 API 时的确定性提取）

### 1.2 Modify UnifiedSkillBuilder
- [x] 修改 `build_from_spec()` 以初始化 ContentSynthesizer
- [x] 修改 `_format_section_from_spec()` 调用 synthesizer
- [x] 修改 `_generate_references_from_spec()` 调用 synthesizer
- [x] 修改 `_generate_skill_md_from_spec()` 以包含生成的内容

### 1.3 Update apply-spec Command
- [x] 确保 `_handle_apply_spec()` 传递完整的 source_config 到 builder
- [x] 添加 `--no-llm` 标志以强制使用 fallback 模式
- [x] 添加进度输出以显示内容生成状态

## 2. Content Extraction Strategies

### 2.1 课程类内容（course-tutorial 模板）
- [x] 课程摘要：从 transcript 前 500 字生成 2-3 段概述
- [x] 关键要点：提取带时间戳的关键知识点
- [x] 核心概念详解：识别并展开 3-5 个核心概念
- [x] 实践练习：基于内容生成 3 道练习题 (LLM placeholder)
- [x] 延伸学习：推荐相关资源 (LLM placeholder)

### 2.2 技术文档类内容（technical-guide 模板）
- [ ] Overview：从 README/首页提取项目介绍
- [ ] Process：从文档结构生成流程步骤
- [ ] Reference Files：汇总 API 文档

## 3. Testing

### 3.1 Unit Tests
- [x] 创建 `tests/test_content_synthesizer.py`
- [x] 测试 LLM 模式内容生成 (mocked)
- [x] 测试 fallback 模式内容生成
- [x] 测试空 source_config 处理

### 3.2 Integration Tests
- [x] 测试完整 apply-spec 流程
- [x] 测试生成的 SKILL.md 包含实际内容
- [x] 测试 references/ 文件包含实际内容

### 3.3 Manual Verification
- [x] 使用 `output/live-streaming-talent/spec.yaml` 手动测试
- [x] 确认生成内容与 transcript 内容相关

## 4. Documentation

- [ ] 更新 README.md 中 Spec-Driven Skill Generation 部分
- [ ] 添加内容填充的说明和示例

## Dependencies
- Task 1.1 → Task 1.2 (ContentSynthesizer 需先完成)
- Task 1.2 → Task 3 (测试需实现完成后进行)

## Parallelizable
- Task 2.1 和 2.2 可并行开发
- Task 3.1 可与 Task 1 并行（先写测试）
