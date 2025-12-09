# Design: Standardize Spec-Driven Skill Workflow

## Context

Skill_Seekers transforms documentation, GitHub repos, PDFs, and transcripts into Claude AI skills. The current pipeline directly generates SKILL.md from scraped data using AI, with no intermediate review step.

This design merges the detailed implementation approach from `add-spec-driven-skill-generation` with the focused scope from `adopt-openspec-skill-workflow`, while following the authentic anthropics/skills patterns observed in real examples like `mcp-builder`, `skill-creator`, `brand-guidelines`, and `webapp-testing`.

### Stakeholders
- **End Users**: Want predictable, controllable skill output
- **AI Assistants**: Need clear specifications to follow during generation
- **Developers**: Maintain the skill generation pipeline

### Constraints
- Must maintain backward compatibility with existing workflows
- Minimal changes to existing scrapers and parsers
- Preserve OpenSpec methodology rigor in adapted format
- Support feedback loop for re-scraping when spec is rejected
- **No MCP tooling** (explicitly deferred)

## Goals / Non-Goals

### Goals
- Enable users to review and approve skill structure before generation
- **Control ALL output** (SKILL.md, references/, scripts/, assets/)
- Provide **pre-built templates** based on real anthropics/skills examples
- Support **feedback loop** for re-scraping when spec is rejected
- Use **Unified Multi-Source Scraping** for conflict resolution
- Make skill output deterministic once spec is approved

### Non-Goals
- Replace the existing direct generation workflow (remains as option)
- Modify scraping or parsing logic (except for feedback re-scrape)
- Require spec for every skill generation (opt-in feature)
- MCP tool surface (explicitly deferred)

## Decisions

### Decision 1: Complete SkillSpec Data Structure

**What**: Create a `SkillSpec` dataclass that defines the **complete** skill output structure following [Anthropic Agent Skills Spec](https://github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md).

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class SkillSpec:
    """Complete Skill 输出规格定义 - 控制所有输出内容
    
    Based on Anthropic Agent Skills Spec v1.0 (2025-10-16)
    """
    
    # === SKILL.md Frontmatter (Required per spec) ===
    name: str                           # kebab-case skill name, must match folder name
    description: str                    # When Claude should use this skill
    
    # === SKILL.md Frontmatter (Optional per spec) ===
    license: Optional[str] = None       # Short license name or bundled file reference
    allowed_tools: List[str] = field(default_factory=list)  # Pre-approved tools
    metadata: Dict[str, str] = field(default_factory=dict)  # Client-specific properties
    
    # === SKILL.md Body (No restrictions per spec, but structured for generation) ===
    sections: List["SectionSpec"] = field(default_factory=list)
    examples: List["ExampleSpec"] = field(default_factory=list)
    guidelines: List[str] = field(default_factory=list)
    
    # === Bundled Resources (Optional directories) ===
    references: List["ReferenceSpec"] = field(default_factory=list)  # references/ folder
    scripts: List["ScriptSpec"] = field(default_factory=list)        # scripts/ folder
    assets: List["AssetSpec"] = field(default_factory=list)          # assets/ folder
    
    # === Generation Control ===
    template_type: Optional[str] = None  # developer-guide, meta-skill, enterprise-brand, tool-integration
    source_config: Dict[str, Any] = field(default_factory=dict)     # For re-scrape on rejection


@dataclass  
class SectionSpec:
    """SKILL.md 章节规格
    
    Based on patterns observed in real skills like mcp-builder, skill-creator
    """
    title: str                          # 章节标题 (e.g., "## Overview", "## Process")
    purpose: str                        # 章节目的描述
    expected_content: List[str] = field(default_factory=list)  # 期望包含的内容类型
    subsections: List["SectionSpec"] = field(default_factory=list)  # 嵌套子章节
    priority: str = "required"          # required | optional


@dataclass
class ExampleSpec:
    """示例规格"""
    title: str                          # 示例标题
    code_language: Optional[str] = None # 代码语言 (python, bash, etc.)
    description: str = ""               # 示例说明


@dataclass
class ReferenceSpec:
    """references/ 文件夹内容规格
    
    Based on patterns in mcp-builder (reference/mcp_best_practices.md, etc.)
    and skill-creator (references/workflows.md, references/output-patterns.md)
    """
    filename: str                       # e.g., "api_docs.md", "workflows.md"
    purpose: str                        # 为什么需要这个参考文件
    content_sources: List[str] = field(default_factory=list)  # 从哪些数据源提取内容
    max_words: int = 10000              # 最大字数限制
    include_toc: bool = False           # 是否包含目录（>100行时推荐）


@dataclass
class ScriptSpec:
    """scripts/ 文件夹内容规格
    
    Based on patterns in webapp-testing (scripts/with_server.py)
    and skill-creator (scripts/init_skill.py, scripts/package_skill.py)
    """
    filename: str                       # e.g., "validate.py", "with_server.py"
    purpose: str                        # 脚本目的
    language: str = "python"            # python, bash, etc.
    supports_help: bool = True          # 是否支持 --help 参数
    

@dataclass
class AssetSpec:
    """assets/ 文件夹内容规格
    
    Based on patterns in brand-guidelines (assets for brand materials)
    and frontend design skills (assets/template/)
    """
    filename: str                       # e.g., "template.html", "logo.png"
    asset_type: str                     # template, icon, font, boilerplate
    source: Optional[str] = None        # 从哪里获取
    copy_only: bool = True              # 是否仅复制（不加载到上下文）
```

### Decision 2: Templates from Real anthropics/skills

**What**: Pre-built templates derived from actual skills in the official repository.

**Why**: User requested templates based on real examples, not invented patterns.

**Template Definitions** (extracted from actual skills + project patterns):

```python
SKILL_TEMPLATES = {
    "technical-guide": {
        # 产出类别: 技术开发指南
        # Based on: mcp-builder skill
        "description": "技术指南、SDK文档、框架教程",
        "sections": [
            {"title": "## Overview", "priority": "required"},
            {"title": "# Process", "priority": "required", "subsections": [
                {"title": "## Phase 1: Research and Planning", "priority": "required"},
                {"title": "## Phase 2: Implementation", "priority": "required"},
                {"title": "## Phase 3: Review and Test", "priority": "required"},
            ]},
            {"title": "# Reference Files", "priority": "required"},
        ],
        "default_references": [
            {"filename": "best_practices.md", "purpose": "Core guidelines"},
            {"filename": "examples.md", "purpose": "Working examples"},
        ],
        "scripts_expected": True,
        "assets_expected": False,
    },
    
    "workflow-skill": {
        # 产出类别: 工作流/元技能
        # Based on: skill-creator skill
        "description": "教授如何创建或管理事物的技能",
        "sections": [
            {"title": "## About", "priority": "required"},
            {"title": "## Core Principles", "priority": "required"},
            {"title": "## Process", "priority": "required", "subsections": [
                {"title": "### Step 1: ...", "priority": "required"},
                {"title": "### Step 2: ...", "priority": "required"},
                # dynamically generated based on content
            ]},
        ],
        "default_references": [
            {"filename": "workflows.md", "purpose": "Sequential workflows and conditional logic"},
            {"filename": "output-patterns.md", "purpose": "Template and example patterns"},
        ],
        "scripts_expected": True,
        "assets_expected": False,
    },
    
    "course-tutorial": {
        # 产出类别: 课程/教程内容 (基于项目的 transcript_scraper)
        # Based on: Skill_Seekers transcript_scraper.py output structure
        "description": "网课逐字稿、培训课程、教程视频转技能",
        "sections": [
            {"title": "## 📝 课程摘要", "priority": "required", 
             "expected_content": ["2-3段课程概述", "核心主题和价值"]},
            {"title": "## 🎯 关键要点", "priority": "required",
             "expected_content": ["5-10个核心概念列表", "关键知识点"]},
            {"title": "## 💡 核心概念详解", "priority": "required",
             "expected_content": ["最重要的3-5个概念详细解释"]},
            {"title": "## 📋 实践练习", "priority": "required",
             "expected_content": ["3道练习题", "巩固知识"]},
            {"title": "## 🔗 延伸学习", "priority": "optional",
             "expected_content": ["2-3个进一步学习方向"]},
        ],
        "default_references": [
            {"filename": "concepts.md", "purpose": "详细概念解释"},
            {"filename": "exercises.md", "purpose": "补充练习题"},
        ],
        "scripts_expected": False,
        "assets_expected": False,
    },
    
    "brand-enterprise": {
        # 产出类别: 企业品牌/规范
        # Based on: brand-guidelines skill
        "description": "公司品牌、风格指南、企业规范",
        "sections": [
            {"title": "## Overview", "priority": "required"},
            {"title": "## Guidelines", "priority": "required", "subsections": [
                {"title": "### Colors", "priority": "required"},
                {"title": "### Typography", "priority": "required"},
            ]},
            {"title": "## Features", "priority": "optional"},
            {"title": "## Technical Details", "priority": "optional"},
        ],
        "default_references": [],  # brand-guidelines doesn't use references
        "scripts_expected": False,
        "assets_expected": True,  # brand assets like logos, fonts
    },
    
    "tool-utility": {
        # 产出类别: 工具集成/测试
        # Based on: webapp-testing skill
        "description": "测试工具、CLI工具、集成辅助工具",
        "sections": [
            {"title": "# Quick Start", "priority": "required"},
            {"title": "## Decision Tree", "priority": "optional"},
            {"title": "## Examples", "priority": "required"},
            {"title": "## Common Pitfalls", "priority": "optional"},
            {"title": "## Best Practices", "priority": "required"},
            {"title": "## Reference Files", "priority": "optional"},
        ],
        "default_references": [],
        "scripts_expected": True,
        "assets_expected": False,
    },
}
```

### Decision 3: Feedback Loop Workflow

**What**: When user rejects the spec, capture feedback and re-scrape data.

**Why**: User specifically requested this feature for iterative refinement.

```python
@dataclass
class SpecFeedback:
    """用户反馈数据结构"""
    approved: bool
    rejection_reason: Optional[str] = None
    suggested_changes: List[str] = field(default_factory=list)
    additional_sources: List[str] = field(default_factory=list)   # 需要补充抓取的来源
    remove_sections: List[str] = field(default_factory=list)      # 需要移除的章节
    add_sections: List[str] = field(default_factory=list)         # 需要添加的章节
    focus_hints: List[str] = field(default_factory=list)          # 抓取时重点关注的内容


def handle_spec_rejection(feedback: SpecFeedback, original_config: Dict) -> Dict:
    """基于反馈生成新的抓取配置"""
    new_config = original_config.copy()
    
    # 添加新的数据源
    if feedback.additional_sources:
        new_config.setdefault('sources', []).extend(feedback.additional_sources)
    
    # 添加抓取提示词（影响AI增强）
    new_config['scrape_hints'] = {
        'focus_on': feedback.add_sections + feedback.focus_hints,
        'avoid': feedback.remove_sections,
        'user_feedback': feedback.rejection_reason,
        'suggested_changes': feedback.suggested_changes,
    }
    
    return new_config
```

**Workflow**:
```
1. scrape_data(config) → raw_data
2. generate_spec(raw_data, template) → SkillSpec
3. user_review(spec) → SpecFeedback
4. IF feedback.approved:
     apply_spec(spec, raw_data) → skill_folder
   ELSE:
     new_config = handle_spec_rejection(feedback, config)
     GOTO 1  # Re-scrape with new config
```

### Decision 4: Conflict Resolution via Unified Multi-Source

**What**: Use existing `merge_sources.py` and conflict detection for resolving spec vs data conflicts.

**Why**: User requested using existing Unified Multi-Source Scraping.

**Integration**:
```python
from skill_seekers.cli.merge_sources import MergeEngine
from skill_seekers.cli.conflict_detector import ConflictDetector

def resolve_spec_conflicts(spec: SkillSpec, scraped_data: Dict) -> SkillSpec:
    """使用 Unified Multi-Source 方法解决冲突"""
    
    # 检测冲突
    detector = ConflictDetector()
    conflicts = detector.detect(spec.to_dict(), scraped_data)
    
    if conflicts:
        # 使用合并引擎解决
        merger = MergeEngine(strategy='ai_assisted')
        resolved = merger.resolve(conflicts)
        
        # 更新 spec
        spec = spec.with_updates(resolved)
        
        # 记录冲突解决日志供用户查看
        spec.conflict_log = conflicts
    
    return spec
```

### Decision 5: CLI Interface (No MCP)

**What**: Add CLI flags for spec-first workflow.

**Why**: Scope excludes MCP; CLI is the primary interface.

```bash
# Spec-first generation with template
skill-seekers scrape --config config.json --spec-first --template developer-guide

# Review generated spec (displays in terminal, exports to file)
skill-seekers show-spec --spec skill_spec.json

# Apply approved spec
skill-seekers apply-spec --spec skill_spec.json

# Reject and re-scrape with feedback
skill-seekers reject-spec --spec skill_spec.json \
  --reason "missing API examples" \
  --add-source "https://docs.example.com/api" \
  --add-section "API Reference"

# List available templates
skill-seekers templates list

# Auto-approve for CI/automation
skill-seekers scrape --config config.json --spec-first --auto-approve
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Added complexity for simple skills | Make spec-first opt-in, default to direct generation |
| Re-scrape may be slow | Cache intermediate data, only re-scrape delta |
| Template may not fit all cases | Allow template customization and `none` template |
| Conflict resolution may lose data | Show diff to user before applying resolution |

## Migration Plan

1. **Phase 1 (Non-breaking)**: Add SkillSpec dataclass and templates
2. **Phase 2 (Non-breaking)**: Add spec_generator.py with feedback support
3. **Phase 3 (Non-breaking)**: Add CLI `--spec-first` flag
4. **Phase 4 (Non-breaking)**: Integrate with Unified Multi-Source conflict resolution

No breaking changes. Existing workflows continue to work.

## Open Questions / Assumptions

- Assume templates can be stored locally with section/reference defaults; users may tweak before approval
- Assume CLI will host approval/rejection prompts; exact UX to be finalized in apply phase
- Assume merge/conflict tooling already exists in repo and can be invoked during apply
