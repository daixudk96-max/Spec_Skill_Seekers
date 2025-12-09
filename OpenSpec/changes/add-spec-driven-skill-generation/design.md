# Design: Spec-Driven Skill Generation

## Context

Skill_Seekers transforms documentation, GitHub repos, PDFs, and transcripts into Claude AI skills. The current pipeline directly generates SKILL.md from scraped data using AI, with no intermediate review step.

OpenSpec provides a proven methodology for spec-driven development where stakeholders agree on specifications before implementation. This design adapts OpenSpec's core patterns for the skill generation domain.

### Stakeholders
- **End Users**: Want predictable, controllable skill output
- **AI Assistants**: Need clear specifications to follow during generation
- **Developers**: Maintain the skill generation pipeline

### Constraints
- Must maintain backward compatibility with existing workflows
- Minimal changes to existing scrapers and parsers
- Preserve OpenSpec methodology rigor in adapted format
- Support feedback loop for re-scraping when spec is rejected

## Goals / Non-Goals

### Goals
- Enable users to review and approve skill structure before generation
- **Control ALL output** (SKILL.md, references/, scripts/, assets/)
- Provide **pre-built templates** based on Anthropic skills format
- Support **feedback loop** for re-scraping when spec is rejected
- Use **Unified Multi-Source Scraping** for conflict resolution
- Make skill output deterministic once spec is approved

### Non-Goals
- Replace the existing direct generation workflow (remains as option)
- Modify scraping or parsing logic (except for feedback re-scrape)
- Require spec for every skill generation (opt-in feature)

## Decisions

### Decision 1: Complete SkillSpec Data Structure

**What**: Create a `SkillSpec` dataclass that defines the **complete** skill output structure following [Anthropic Agent Skills Spec](https://github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md).

```python
@dataclass
class SkillSpec:
    """Complete Skill 输出规格定义 - 控制所有输出内容"""
    
    # === SKILL.md Frontmatter (Required) ===
    name: str                           # kebab-case skill name
    description: str                    # When Claude should use this skill
    
    # === SKILL.md Frontmatter (Optional) ===
    license: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    
    # === SKILL.md Body ===
    sections: List[SectionSpec] = field(default_factory=list)
    examples: List[ExampleSpec] = field(default_factory=list)
    guidelines: List[str] = field(default_factory=list)
    
    # === Bundled Resources ===
    references: List[ReferenceSpec] = field(default_factory=list)  # references/ folder
    scripts: List[ScriptSpec] = field(default_factory=list)        # scripts/ folder
    assets: List[AssetSpec] = field(default_factory=list)          # assets/ folder
    
    # === Generation Control ===
    template_type: Optional[str] = None  # framework, tutorial, api, enterprise
    source_config: Dict[str, Any] = field(default_factory=dict)     # For re-scrape

@dataclass  
class SectionSpec:
    """SKILL.md 章节规格"""
    title: str                          # 章节标题 (e.g., "## Overview")
    purpose: str                        # 章节目的 (SHALL/MUST 格式)
    expected_content: List[str]         # 期望包含的内容类型
    priority: str = "required"          # required | optional
    
@dataclass
class ReferenceSpec:
    """references/ 文件夹内容规格"""
    filename: str                       # e.g., "api_docs.md"
    purpose: str                        # 为什么需要这个参考文件
    content_sources: List[str]          # 从哪些数据源提取内容
    max_words: int = 10000              # 最大字数限制

@dataclass
class ScriptSpec:
    """scripts/ 文件夹内容规格"""
    filename: str                       # e.g., "validate.py"
    purpose: str                        # 脚本目的
    language: str                       # python, bash, etc.
    
@dataclass
class AssetSpec:
    """assets/ 文件夹内容规格"""
    filename: str                       # e.g., "template.html"
    asset_type: str                     # template, icon, font, boilerplate
    source: Optional[str] = None        # 从哪里获取
```

### Decision 2: Feedback Loop Workflow

**What**: When user rejects the spec, capture feedback and re-scrape data.

**Why**: User requested this feature to enable iterative refinement.

```python
class SpecFeedback:
    """用户反馈数据结构"""
    approved: bool
    rejection_reason: Optional[str]
    suggested_changes: List[str]
    additional_sources: List[str]       # 需要补充抓取的来源
    remove_sections: List[str]          # 需要移除的章节
    add_sections: List[str]             # 需要添加的章节

def handle_spec_rejection(feedback: SpecFeedback, original_config: Dict) -> Dict:
    """基于反馈生成新的抓取配置"""
    new_config = original_config.copy()
    
    # 添加新的数据源
    if feedback.additional_sources:
        new_config['sources'].extend(feedback.additional_sources)
    
    # 添加抓取提示词（影响AI增强）
    new_config['scrape_hints'] = {
        'focus_on': feedback.add_sections,
        'avoid': feedback.remove_sections,
        'user_feedback': feedback.rejection_reason
    }
    
    return new_config
```

**Workflow**:
```
1. scrape_data(config) → raw_data
2. generate_spec(raw_data) → SkillSpec
3. user_review(spec) → SpecFeedback
4. IF feedback.approved:
     apply_spec(spec, raw_data) → skill_folder
   ELSE:
     new_config = handle_spec_rejection(feedback, config)
     GOTO 1  # Re-scrape with new config
```

### Decision 3: Skill Templates

**What**: Pre-built templates based on [anthropics/skills](https://github.com/anthropics/skills) repository.

**Why**: User requested templates for common skill types.

**Template Types**:

| Template | Use Case | Example |
|----------|----------|---------|
| `framework` | Library/framework docs | React, Vue, Django |
| `api` | API reference documentation | REST APIs, SDKs |
| `tutorial` | Learning/course content | Transcripts, guides |
| `enterprise` | Enterprise workflows | Brand guidelines, policies |

**Template Structure**:
```
templates/
├── framework/
│   ├── template.json        # SkillSpec defaults
│   └── examples/
├── api/
│   ├── template.json
│   └── examples/
├── tutorial/
│   ├── template.json
│   └── examples/
└── enterprise/
    ├── template.json
    └── examples/
```

**Example `framework/template.json`**:
```json
{
  "template_type": "framework",
  "sections": [
    {"title": "## Overview", "priority": "required"},
    {"title": "## Installation", "priority": "required"},
    {"title": "## Core Concepts", "priority": "required"},
    {"title": "## API Reference", "priority": "required"},
    {"title": "## Examples", "priority": "required"},
    {"title": "## Best Practices", "priority": "optional"}
  ],
  "references": [
    {"filename": "api_docs.md", "purpose": "Complete API reference"},
    {"filename": "tutorials.md", "purpose": "Step-by-step guides"}
  ]
}
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
    
    return spec
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
