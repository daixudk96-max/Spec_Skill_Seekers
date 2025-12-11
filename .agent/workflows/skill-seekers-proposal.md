---
description: skill-seekers-proposal workflow
---
<!-- SKILL_SEEKERS:START -->
# /skill-seekers-proposal

## 角色
- 你是 AI 编程助手，负责读取 `--output-raw` 的原始数据并完成内容增强。

## 目标
- 为 Skill Seekers 生成初始 SkillSpec（spec-first），便于后续 apply。
- 输出原始抓取数据供二次分析，避免直接依赖外部 LLM API。

## 步骤

### 1. 确认输入
询问用户提供以下信息：
- **来源类型**：docs（文档网站）/ repo（GitHub 仓库）/ pdf（PDF 文件）/ transcript（音视频转录）
- **模板类型**：technical-guide / workflow-skill / course-tutorial / brand-enterprise / tool-utility
- **技能名称与描述**：技能的标题和简短说明

### 2. 执行抓取（需用户同意后再运行）
```bash
skill-seekers scrape --spec-first --output-raw \
  --template <template> \
  --name "<skill_name>" \
  --url <source_url> \
  --description "<short goal>"
```
- 可加 `--auto-approve` 跳过交互。
- 对于 GitHub 仓库，使用 `skill-seekers github` 命令。
- 对于 PDF 文件，使用 `skill-seekers pdf` 命令。

### 3. 分析原始数据
阅读生成的 `scraped_data.json`，执行以下分析：
- 提炼 **章节结构**：识别主要主题和子主题
- 总结 **要点**：提取核心概念和关键信息
- 识别 **缺口**：标记需要补充的内容领域
- 评估 **风险与假设**：记录数据质量问题或不确定性

### 3.5 分段总结（仅 transcript 类型）

> **适用条件**：当来源类型为 `transcript` 时执行

**目的**：对转录文本进行语义分段和结构化总结

**执行步骤**：

1. **读取原始 transcript**
   - 阅读 `scraped_data.json` 中的原始内容
   - 记录文件名和时间戳信息

2. **语义分段**
   - 根据标志词分段：'好'、'下一个'、'第一个'、'首先'、'其次'、'最后'
   - **注意**：不按篇幅分段，只在明确标志处分段

3. **子分段识别**
   - 在主分段内识别话题转换
   - 创建层次结构 (id: "1.1", "1.2")

4. **撰写全面总结**
   - `summary_full`：详尽准确，让未读原文者能完全理解
   - `summary_brief`：2-3 句核心内容
   - `key_points`：列表形式的重点
   - `examples_simplified`：保留并简化例子
   - `reason`：解释分段原因

5. **同音字修正**
   - 根据上下文推断正确用词
   - 记录在 `homophone_notes`

6. **输出 segmented_summary.json**
```json
{
  "version": "1.0",
  "source_file": "原文件名.txt",
  "total_segments": 3,
  "segments": [
    {
      "id": "1",
      "timestamp": "00:00 - 08:05",
      "marker": "好",
      "reason": "分段原因",
      "summary_full": "详细总结...",
      "summary_brief": "简短摘要",
      "key_points": ["要点1"],
      "examples_simplified": ["例子"],
      "homophone_notes": ["修正说明"],
      "subsegments": [{"id": "1.1", "topic": "子话题", "summary": "子总结"}]
    }
  ],
  "metadata": {"generated_by": "AI_assistant", "generated_at": "ISO时间"}
}
```

### 3.6 综合生成 Spec（使用分段总结 + 原文）

> **适用条件**：已完成 Step 3.5，存在 `segmented_summary.json`

**输入**：
- `scraped_data.json`（原始数据，用于验证准确性）
- `segmented_summary.json`（分段总结）

**处理**：
- 对照原文验证总结准确性
- 将分段结构融入 `spec.yaml` 的 lessons
- 使用分段总结增强 sections 内容

### 4. 生成/修订 spec.yaml
基于分析结果增强 spec.yaml：
- 写入增强后的 **摘要**（synopsis）
- 提取 **关键信息**（key points）
- 建议 **练习/示例**（exercises, examples）
- 标注需要补充的素材

### 5. 交付物
- `scraped_data.json`（原始数据）
- `segmented_summary.json`（分段总结，仅 transcript 类型）
- `spec.yaml`（草稿规格）
- 未决问题清单

## 输出
- 来源与模板选择说明
- 风险与假设清单
- 生成的文件路径与下一步建议

<!-- SKILL_SEEKERS:END -->
