---
description: Implement an approved OpenSpec change and keep tasks in sync.
---
<!-- OPENSPEC:START -->
**Guardrails**
- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Refer to `openspec/AGENTS.md` (located inside the `openspec/` directory—run `ls openspec` or `openspec update` if you don't see it) if you need additional OpenSpec conventions or clarifications.

**Steps**
Track these steps as TODOs and complete them one by one.
1. Read `changes/<id>/proposal.md`, `design.md` (if present), and `tasks.md` to confirm scope and acceptance criteria.
2. Work through tasks sequentially, keeping edits minimal and focused on the requested change.
   - **编码前**：必须向 codex 索要代码实现原型（要求 codex 仅给出 unified diff patch，严禁对代码做任何真实修改）。获取后以此为逻辑参考，重写形成企业生产级别、高可读性、高可维护性的代码。
   - **编码后**：必须立即使用 codex review 代码改动和对应需求完成程度。
   - **独立思考**：codex 仅为参考，你必须有自己的判断，甚至对 codex 回答提出质疑。最终目标是与 codex 达成统一、全面、精准的意见。
3. Confirm completion before updating statuses—make sure every item in `tasks.md` is finished.
4. Update the checklist after all work is done so each task is marked `- [x]` and reflects reality.
5. Reference `openspec list` or `openspec show <item>` when additional context is required.

**Reference**
- Use `openspec show <id> --json --deltas-only` if you need additional context from the proposal while implementing.

**Codex Tool Invocation Specification**

**1. 工具概述**
codex MCP 提供了一个工具 `codex`，用于执行 AI 辅助的编码任务。该工具**通过 MCP 协议调用**，无需使用命令行。

**2. 工具参数**
必选参数：
- PROMPT (string): 发送给 codex 的任务指令
- cd (Path): codex 执行任务的工作目录根路径

可选参数：
- sandbox (string): 沙箱策略，可选值：
  - "read-only" (默认): 只读模式，最安全
  - "workspace-write": 允许在工作区写入
  - "danger-full-access": 完全访问权限
- SESSION_ID (UUID | null): 用于继续之前的会话以与codex进行多轮交互，默认为 None（开启新会话）
- skip_git_repo_check (boolean): 是否允许在非 Git 仓库中运行，默认 False
- return_all_messages (boolean): 是否返回所有消息（包括推理、工具调用等），默认 False
- image (List[Path] | null): 附加一个或多个图片文件到初始提示词，默认为 None
- model (string | null): 指定使用的模型，默认为 None（使用用户默认配置）
- yolo (boolean | null): 无需审批运行所有命令（跳过沙箱），默认 False
- profile (string | null): 从 `~/.codex/config.toml` 加载的配置文件名称，默认为 None（使用用户默认配置）

返回值：
```json
{
  "success": true,
  "SESSION_ID": "uuid-string",
  "agent_messages": "agent回复的文本内容",
  "all_messages": []  // 仅当 return_all_messages=True 时包含
}
```
或失败时：
```json
{
  "success": false,
  "error": "错误信息"
}
```

**3. 使用方式**
开启新对话：
- 不传 SESSION_ID 参数（或传 None）
- 工具会返回新的 SESSION_ID 用于后续对话

继续之前的对话：
- 将之前返回的 SESSION_ID 作为参数传入
- 同一会话的上下文会被保留

**4. 调用规范**
必须遵守：
- 每次调用 codex 工具时，必须保存返回的 SESSION_ID，以便后续继续对话
- cd 参数必须指向存在的目录，否则工具会静默失败
- 严禁codex对代码进行实际修改，使用 sandbox="read-only" 以避免意外，并要求codex仅给出unified diff patch即可

推荐用法：
- 如需详细追踪 codex 的推理过程和工具调用，设置 return_all_messages=True
- 对于精准定位、debug、代码原型快速编写等任务，优先使用 codex 工具

**5. 注意事项**
- 会话管理：始终追踪 SESSION_ID，避免会话混乱
- 工作目录：确保 cd 参数指向正确且存在的目录
- 错误处理：检查返回值的 success 字段，处理可能的错误
<!-- OPENSPEC:END -->
