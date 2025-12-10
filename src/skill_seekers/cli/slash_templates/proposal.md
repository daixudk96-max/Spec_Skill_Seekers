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

### 4. 生成/修订 spec.yaml
基于分析结果增强 spec.yaml：
- 写入增强后的 **摘要**（synopsis）
- 提取 **关键信息**（key points）
- 建议 **练习/示例**（exercises, examples）
- 标注需要补充的素材

### 5. 交付物
- `scraped_data.json`（原始数据）
- `spec.yaml`（草稿规格）
- 未决问题清单

## 输出
- 来源与模板选择说明
- 风险与假设清单
- 生成的文件路径与下一步建议
