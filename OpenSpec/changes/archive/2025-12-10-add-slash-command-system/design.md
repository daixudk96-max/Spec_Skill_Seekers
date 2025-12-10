## Context

Skill_Seekers 需要实现类似 OpenSpec 的 slash 命令系统，让用户能够通过 AI 编程助手（如 Antigravity、Claude Code、Cursor）使用 `/skill-seekers-proposal` 等命令来创建 Claude Skills。

### 背景约束
- OpenSpec 使用 TypeScript + npm 分发
- Skill_Seekers 使用 Python + pip 分发
- 需要保持与 OpenSpec 相同的工具支持列表
- 工作流不依赖外部 LLM API，由 AI 编程助手本身执行

## Goals / Non-Goals

### Goals
- 实现 `skill-seekers init` 命令，自动生成工作流文件
- 支持与 OpenSpec 相同的 20+ AI 工具
- 提供三个标准化工作流：proposal、apply、archive
- 工作流调用现有 `skill-seekers` CLI 命令

### Non-Goals
- 不实现 OpenSpec 的 spec validation/archive 逻辑（这是代码 spec，不是 skill spec）
- 不添加新的外部依赖
- 不修改现有的 SkillSpec 核心逻辑

## Decisions

### Decision 1: Python 配置器架构
采用与 OpenSpec 类似的配置器模式：
- `SlashCommandConfigurator` 基类定义接口
- 每个 AI 工具有对应的子类
- 通过注册表统一管理

**替代方案**：
- ❌ 直接复用 OpenSpec npm 包：需要双栈（Node+Python），增加用户安装复杂度
- ❌ 简单的配置字典：缺乏扩展性，难以处理工具特定逻辑

### Decision 2: 外置模板文件
选择将模板内容作为独立的 Markdown 文件存放在包内（`src/skill_seekers/cli/slash_templates/`），而非内嵌在 Python 代码中。

**理由**：
- 用户可直接编辑模板文件，无需修改代码
- 模板更新可独立于代码发布
- 便于本地化和定制
- 通过 `importlib.resources` 读取，兼容 pip 全局安装

**文件结构**：
```
src/skill_seekers/cli/slash_templates/
├── proposal.md     # /skill-seekers-proposal 模板
├── apply.md        # /skill-seekers-apply 模板
└── archive.md      # /skill-seekers-archive 模板
```

### Decision 3: 工作流命令调用
工作流内容直接调用 `skill-seekers` CLI 命令：
```
skill-seekers scrape --spec-first --template <template>
skill-seekers show-spec <spec.yaml>
skill-seekers apply-spec <spec.yaml>
```

**不调用 OpenSpec 命令**：这是独立系统，专注于 Claude Skills 生成。

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| 模板内容更新需要发布新版本 | 提供 `skill-seekers update` 命令，用户可按需更新 |
| AI 工具配置变化频繁 | 参考 OpenSpec 的工具列表，保持同步 |
| 工作流与 OpenSpec 工作流冲突 | 使用独立命名空间 `/skill-seekers-*` |

## Open Questions
- 是否需要支持自定义模板？（建议 v1 不支持，后续迭代）

## Decision 4: AI编程助手作为内容增强器 (核心设计)
工作流设计让 **AI编程助手本身** 承担内容增强角色，替代原有的外部API调用。

### 工作流程
```
1. skill-seekers scrape --output-raw     → 输出原始数据 scraped_data.json
2. AI编程助手读取原始数据               → 分析内容结构
3. AI编程助手生成增强内容               → 摘要、要点、练习等
4. 写入 spec.yaml                       → 包含增强后的内容
5. skill-seekers apply-spec spec.yaml   → 生成最终skill
```

### 关键优势
- **零API成本**：不需要额外的LLM API调用
- **交互式优化**：用户可以与AI助手对话调整内容
- **上下文理解**：AI助手可以看到整个项目上下文
- **质量等同或更优**：AI编程助手（如Antigravity）本身就是强大的LLM

### 实现要点
- `--output-raw` 标志确保输出原始数据供AI助手读取
- 工作流模板包含详细的增强指导（生成摘要、要点、练习等）
- AI助手遵循工作流步骤，主动分析并增强内容

