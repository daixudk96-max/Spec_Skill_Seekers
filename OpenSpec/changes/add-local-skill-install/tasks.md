# Tasks: add-local-skill-install

## 实施任务列表

### Phase 1: 核心功能

- [x] **T1**: 创建 `install_skill.py` 模块
  - 实现 `get_claude_skills_dir()` 跨平台目录解析
  - 实现 `install_skill()` 核心安装逻辑
  - 支持目录和 `.zip` 文件输入
  - 实现目标目录自动创建 (`mkdir -p` 语义)

- [x] **T2**: 实现冲突处理
  - 实现 `--overwrite` 覆盖模式
  - 实现 `--backup` 备份模式
  - 实现 `--dry-run` 预览模式
  - 添加 `--overwrite` 与 `--backup` 互斥验证
  - 添加回滚机制

- [x] **T2.5**: 实现安全和原子性操作
  - 实现 ZIP 安全验证（路径穿越、符号链接）
  - 实现原子性安装（先临时目录后移动）
  - 处理 ZIP 无顶层目录的情况

### Phase 2: CLI 集成

- [x] **T3**: 添加 `install` 子命令到 `main.py`
  - 解析器配置
  - `_handle_install()` 处理函数

- [x] **T4**: 扩展 `package` 命令
  - 添加 `--install` 标志
  - 处理 `--install` 与 `--upload` 的执行顺序
  - 调用 `install_skill()` 函数

### Phase 3: 测试

- [x] **T5**: 编写单元测试 `test_install_skill.py`
  - 测试目录解析（Windows/macOS/Linux，环境变量覆盖）
  - 测试正常安装流程（目录和 ZIP）
  - 测试冲突处理策略
  - 测试回滚机制
  - 测试 ZIP 安全验证（路径穿越、符号链接）
  - 测试原子性安装

- [x] **T6**: 更新 `test_package_skill.py`
  - 添加 `--install` 标志测试
  - 添加 `--install --upload` 顺序测试

### Phase 4: 文档和工作流

- [x] **T7**: 更新 README.md
  - 添加 `install` 命令文档
  - 添加 `package --install` 用法

- [x] **T8**: 更新 `/skill-seekers-archive` workflow
  - 添加 `--install` 选项说明

## 依赖关系

```
T1 → T2 → T2.5 → T3 → T4 → T5 → T6 → T7 → T8
```

## 并行化

- T5 和 T6 可与 T7 和 T8 并行
- T2 和 T2.5 可部分并行
