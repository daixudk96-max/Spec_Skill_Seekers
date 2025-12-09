---
description: Implement an approved OpenSpec change and keep tasks in sync.
---
<!-- OPENSPEC:START -->
**Guardrails**
- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Refer to `openspec/AGENTS.md` (located inside the `openspec/` directory—run `ls openspec` or `openspec update` if you don't see it) if you need additional OpenSpec conventions or clarifications.
- 在任何时刻，你必须思考当前过程可以如何与 codex 进行协作，调用 Codex MCP 工具作为你客观全面分析的保障。
- codex 只能给出参考，你**必须有自己的思考，甚至需要对 codex 的回答提出质疑**。尽信书则不如无书，你与 codex 的最终使命都是达成统一、全面、精准的意见，所以你们必须不断争辩以找到通向真理的唯一途径。

**Steps**
Track these steps as TODOs and complete them one by one.
1. Read `changes/<id>/proposal.md`, `design.md` (if present), and `tasks.md` to confirm scope and acceptance criteria.
2. **[Codex 协作]** 在对需求形成初步分析后，将用户需求、初始思路告知 codex，并要求其完善需求分析和实施计划。
3. Work through tasks sequentially, keeping edits minimal and focused on the requested change.
4. **[Codex 协作]** 在实施具体编码任务前，**必须向 codex 索要代码实现原型（要求 codex 仅给出 unified diff patch，严禁对代码做任何真实修改）**。获取代码原型后，你**只能以此为逻辑参考，再次对代码修改进行重写**，形成企业生产级别、可读性极高、可维护性极高的代码后，才能实施具体编程修改任务。
5. **[Codex 协作]** 无论何时，只要完成切实编码行为后，**必须立即使用 codex review 代码改动和对应需求完成程度**。
6. Confirm completion before updating statuses—make sure every item in `tasks.md` is finished.
7. Update the checklist after all work is done so each task is marked `- [x]` and reflects reality.
8. Reference `openspec list` or `openspec show <item>` when additional context is required.

**Reference**
- Use `openspec show <id> --json --deltas-only` if you need additional context from the proposal while implementing.
- **Codex Tool Invocation Specification**:
  - 工具概述: codex MCP 提供工具 `codex`，用于执行 AI 辅助的编码任务，**通过 MCP 协议调用**，无需使用命令行。
  - **必选参数**:
    - `PROMPT` (string): 发送给 codex 的任务指令
    - `cd` (Path): codex 执行任务的工作目录根路径
  - **可选参数**:
    - `sandbox` (string): 沙箱策略 - `"read-only"`(默认/最安全) | `"workspace-write"` | `"danger-full-access"`
    - `SESSION_ID` (UUID | null): 用于继续之前的会话以与 codex 进行多轮交互，默认为 None（开启新会话）
    - `skip_git_repo_check` (boolean): 是否允许在非 Git 仓库中运行，默认 False
    - `return_all_messages` (boolean): 是否返回所有消息（包括推理、工具调用等），默认 False
    - `image` (List[Path] | null): 附加图片文件到初始提示词
    - `model` (string | null): 指定使用的模型
    - `yolo` (boolean | null): 无需审批运行所有命令（跳过沙箱），默认 False
    - `profile` (string | null): 从 `~/.codex/config.toml` 加载的配置文件名称
  - **返回值**: `{ "success": true, "SESSION_ID": "uuid-string", "agent_messages": "回复内容", "all_messages": [] }` 或失败时 `{ "success": false, "error": "错误信息" }`
  - **调用规范**:
    - 每次调用必须保存返回的 `SESSION_ID`，以便后续继续对话
    - `cd` 参数必须指向存在的目录，否则工具会静默失败
    - 严禁 codex 对代码进行实际修改，使用 `sandbox="read-only"` 以避免意外，并要求 codex 仅给出 unified diff patch
  - **推荐用法**: 如需详细追踪 codex 的推理过程和工具调用，设置 `return_all_messages=True`；对于精准定位、debug、代码原型快速编写等任务，优先使用 codex 工具
  - **注意事项**: 始终追踪 `SESSION_ID` 避免会话混乱；确保 `cd` 指向正确目录；检查返回值的 `success` 字段处理可能的错误
<!-- OPENSPEC:END -->
