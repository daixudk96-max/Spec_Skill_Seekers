# Tasks: Add Transcript Semantic Segmentation

## Phase 1: 工作流文档更新

### 1.1 更新 skill-seekers-proposal.md
- [x] 新增 Step 3.5: 分段总结（适用于 transcript）
- [x] 新增 Step 3.6: 综合生成 Spec（使用分段总结 + 原文）
- [x] 更新交付物列表

---

## Phase 2: 数据结构定义

### 2.1 定义 segmented_summary.json 模式
- [x] 在 design.md 中已定义结构
- [x] 无需独立 schema 文件（AI 助手按格式输出即可）

---

## Phase 3: Spec 生成增强

### 3.1 扩展 SpecGenerator
- [x] 添加 `load_segmented_summary()` 方法
- [x] 添加 `_merge_segmented_summary()` 方法
- [x] 添加 `_attach_segments_to_lessons()` 方法
- [x] 修改 `__init__()` 添加 `segmented_summary` 参数
- [x] 修改 `from_transcript_scraper()` 传递分段数据
- [x] 修改 `generate()` 调用 merge 逻辑

### 3.2 添加测试
- [x] 添加 `TestSegmentedSummary` 测试类（6 个测试）
- [x] 所有 25 个测试通过

### 3.3 更新 README
- [x] 添加分段总结功能说明
- [x] 添加 API 使用示例

---

## 验证结果

| 检查项 | 状态 |
|--------|------|
| 向后兼容 | ✅ 无分段数据时正常工作 |
| 测试通过 | ✅ 25/25 passed |
| Codex 代码审查 | ✅ 已确认满足需求 |
