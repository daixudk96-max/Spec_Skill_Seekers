# Change: Add Slash Command System for AI Coding Assistants

## Why
Skill_Seekers 目前需要手动创建工作流文件，无法像 OpenSpec 那样通过 `init` 命令自动为各种 AI 工具生成 slash 命令工作流。用户希望能够通过 `/skill-seekers-proposal`、`/skill-seekers-apply`、`/skill-seekers-archive` 等命令在 AI 编程助手中触发标准化的技能创建工作流。

## What Changes
- 新增 Python 版 AI 工具配置器系统（借鉴 OpenSpec 的 `SlashCommandConfigurator` 架构）
- 新增 `skill-seekers init` CLI 命令，支持为多种 AI 工具生成工作流文件
- 新增 `skill-seekers update` CLI 命令，更新现有工作流文件
- 新增三个工作流模板：`skill-seekers-proposal`、`skill-seekers-apply`、`skill-seekers-archive`
- 支持与 OpenSpec 相同的 AI 工具列表（Antigravity、Claude Code、Cursor、Codex 等 20+ 工具）

## Impact
- **Affected specs**: 可能需要新增 `slash-command-system` capability spec
- **Affected code**:
  - `src/skill_seekers/cli/main.py` (添加 init/update 命令)
  - `src/skill_seekers/cli/configurators.py` (新增)
  - `src/skill_seekers/cli/slash_templates.py` (新增)
- **Dependencies**: 无新增外部依赖
