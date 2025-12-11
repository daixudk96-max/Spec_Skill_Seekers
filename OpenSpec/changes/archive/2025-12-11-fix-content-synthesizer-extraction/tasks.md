# Tasks

## Phase 1: Core Fix

1. [x] 更新 `_get_source_text()` 方法支持数组格式
   - 文件: `src/skill_seekers/core/content_synthesizer.py`
   - 添加对 `lessons.lessons` 为 list 的处理分支
   - 遍历并拼接 `summary_full` / `summary` / `key_points`
   - 验证: 单元测试通过

2. [x] 添加新测试用例
   - 文件: `tests/test_content_synthesizer.py`
   - 添加 `test_extract_from_lessons_array`
   - 添加 `test_extract_from_segmented_summary`
   - 验证: `pytest tests/test_content_synthesizer.py -v`

## Phase 2: Validation

3. [x] 运行回归测试
   - 命令: `pytest tests/ -v --ignore=tests/test_integration.py`
   - 验证: 15/17 通过 (2 failed 为 LLM mock 问题，与变更无关)

4. [x] 手动验证生成结果
   - 使用 `spec_enhanced.yaml` 测试 ContentSynthesizer
   - 检查源文本不包含 JSON 片段 ✅
   - 内容正确提取为中文可读文本 ✅

---

## Dependencies

- 无外部依赖
- Phase 1 和 Phase 2 可顺序执行

## Risk Assessment

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 破坏原有字符串格式兼容性 | 低 | 高 | 保持 if-else 分支优先级 |
| 新格式提取内容不完整 | 中 | 中 | 测试多种 source_config 结构 |
