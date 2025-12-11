# Add Local Skill Install Command

## Why

当前 Skill_Seekers 工作流中，用户在生成技能后需要**手动**将技能文件夹复制到 Claude 本地技能目录（如 `~/.claude/skills`）。这增加了额外的操作步骤，降低了工作效率，也不利于自动化脚本集成。

用户反馈希望在归档后直接将技能写入 Claude 本地目录，实现一键完成从生成到安装的完整流程。

## What

实现本地技能安装功能：

1. **独立 `install` 命令**：接受技能目录或 `.zip` 文件，安装到 Claude skills 目录
2. **`package --install` 便捷选项**：打包后自动安装
3. **跨平台路径检测**：自动识别 Windows / macOS / Linux 的 Claude skills 目录
4. **冲突处理策略**：`--overwrite`、`--backup`、`--dry-run` 选项
5. **回滚机制**：安装失败时自动清理

## How

详见 [design.md](./design.md) 技术设计文档。

## Constraints

- 不改变现有 `package` 和 `upload` 命令的核心行为
- 保持向后兼容
- 明确的错误提示和回滚机制
- 支持环境变量 `CLAUDE_SKILLS_DIR` 覆盖默认路径
