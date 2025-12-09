#!/usr/bin/env python3
"""
Spec Feedback Handling for Skill_Seekers

Provides functions for handling user feedback on generated specs:
- handle_spec_rejection: Build re-scrape config from feedback
- apply_feedback_to_spec: Apply section changes to spec
- prompt_user_feedback: Interactive CLI for spec review
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

from skill_seekers.core.skill_spec import SectionSpec, SkillSpec, SpecFeedback


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    """Remove empty items and deduplicate while preserving order."""
    seen = set()
    result: List[str] = []
    for item in items or []:
        normalized = (item or "").strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def _parse_csv_list(raw: str) -> List[str]:
    """Parse a comma-separated string into a cleaned list."""
    if not raw:
        return []
    parts = [part.strip() for part in raw.split(",")]
    return _dedupe_preserve_order([p for p in parts if p])


def handle_spec_rejection(spec: SkillSpec, feedback: SpecFeedback) -> Dict:
    """
    Build a new scrape configuration based on reviewer feedback.
    
    The resulting dict can be fed back into the scraper to pull
    additional sources, focus on requested sections, and avoid
    unwanted areas.
    
    Args:
        spec: Current SkillSpec that was rejected
        feedback: User feedback with change requests
        
    Returns:
        Dict configuration for re-scraping
    """
    # 从现有 source_config 开始
    new_config = deepcopy(spec.source_config or {})

    # 合并额外数据源
    sources = list(new_config.get("sources", []))
    if feedback.additional_sources:
        sources.extend(feedback.additional_sources)
    new_config["sources"] = _dedupe_preserve_order(sources)

    # 添加需要移除的章节到排除列表
    exclude_sections = list(new_config.get("exclude_sections", []))
    if feedback.remove_sections:
        exclude_sections.extend(feedback.remove_sections)
    new_config["exclude_sections"] = _dedupe_preserve_order(exclude_sections)

    # 添加需要增加的章节到 focus 列表
    focus_sections = list(new_config.get("focus_sections", []))
    if feedback.add_sections:
        focus_sections.extend(feedback.add_sections)
    new_config["focus_sections"] = _dedupe_preserve_order(focus_sections)

    # 合并焦点提示
    focus_hints = list(new_config.get("focus_hints", []))
    if feedback.focus_hints:
        focus_hints.extend(feedback.focus_hints)
    new_config["focus_hints"] = _dedupe_preserve_order(focus_hints)

    # 保留拒绝原因供参考
    if feedback.rejection_reason:
        new_config["last_rejection_reason"] = feedback.rejection_reason

    # 保留建议的改动
    if feedback.suggested_changes:
        new_config["suggested_changes"] = feedback.suggested_changes

    return new_config


def apply_feedback_to_spec(spec: SkillSpec, feedback: SpecFeedback) -> SkillSpec:
    """
    Apply feedback changes directly to a SkillSpec.
    
    Modifies sections based on add/remove requests and resets status
    for re-review.
    
    Args:
        spec: Current SkillSpec to modify
        feedback: User feedback with change requests
        
    Returns:
        Updated SkillSpec (new instance)
    """
    # 创建深拷贝以避免修改原始对象
    updated = deepcopy(spec)

    # 移除指定的章节
    if feedback.remove_sections:
        remove_set = {s.lower() for s in feedback.remove_sections}
        updated.sections = [
            section for section in updated.sections
            if section.title.lower() not in remove_set
            and not any(keyword.lower() in section.title.lower() for keyword in remove_set)
        ]

    # 添加新章节（作为占位符）
    if feedback.add_sections:
        existing_titles = {s.title.lower() for s in updated.sections}
        for section_title in feedback.add_sections:
            if section_title.lower() not in existing_titles:
                # 创建新章节，带有正确的 markdown 标题格式
                title = section_title if section_title.startswith("#") else f"## {section_title}"
                updated.sections.append(SectionSpec(
                    title=title,
                    purpose=f"Added based on feedback: {section_title}",
                    priority="required",
                ))

    # 重置状态为待审批
    updated.meta.status = "pending"
    updated.meta.mark_updated()

    # 将 re-scrape 配置存入 source_config
    if feedback.has_changes():
        updated.source_config = handle_spec_rejection(updated, feedback)

    return updated


def prompt_user_feedback(spec: SkillSpec, interactive: bool = True) -> SpecFeedback:
    """
    Present a spec summary for review and collect user feedback.
    
    Args:
        spec: SkillSpec to review
        interactive: If True, prompt for input; if False, return pending feedback
        
    Returns:
        SpecFeedback capturing approval, rejections, or requested changes.
    """
    if not interactive:
        return SpecFeedback(
            approved=False,
            rejection_reason="Pending manual review (non-interactive mode)",
        )

    # 显示 spec 摘要
    print("\n" + "=" * 60)
    print("           SKILL SPEC REVIEW")
    print("=" * 60)
    print(spec.to_markdown())
    print("\n" + "-" * 60)
    print("Review options:")
    print("  [a]pprove - Accept this spec as-is")
    print("  [r]eject  - Reject and request re-scrape")
    print("  [c]hange  - Request modifications")
    print("-" * 60)

    choice = input("\nYour choice (a/r/c): ").strip().lower()

    # 批准
    if choice.startswith("a"):
        return SpecFeedback(approved=True)

    # 收集反馈详情
    print("\nPlease provide feedback details:")
    
    rejection_reason = input("  Rejection/change reason: ").strip() or None
    
    suggested_changes = _parse_csv_list(
        input("  Suggested changes (comma-separated, optional): ")
    )
    
    additional_sources = _parse_csv_list(
        input("  Additional sources to scrape (comma-separated, optional): ")
    )
    
    remove_sections = _parse_csv_list(
        input("  Sections to remove (comma-separated, optional): ")
    )
    
    add_sections = _parse_csv_list(
        input("  Sections to add (comma-separated, optional): ")
    )
    
    focus_hints = _parse_csv_list(
        input("  Focus hints for re-scrape (comma-separated, optional): ")
    )

    return SpecFeedback(
        approved=False,
        rejection_reason=rejection_reason,
        suggested_changes=suggested_changes,
        additional_sources=additional_sources,
        remove_sections=remove_sections,
        add_sections=add_sections,
        focus_hints=focus_hints,
    )


def create_feedback(
    approved: bool = False,
    rejection_reason: str = None,
    suggested_changes: List[str] = None,
    additional_sources: List[str] = None,
    remove_sections: List[str] = None,
    add_sections: List[str] = None,
    focus_hints: List[str] = None,
) -> SpecFeedback:
    """
    Convenience function to create SpecFeedback programmatically.
    
    Args:
        approved: Whether the spec is approved
        rejection_reason: Reason for rejection (if not approved)
        suggested_changes: List of suggested changes
        additional_sources: URLs or paths to scrape additionally
        remove_sections: Section titles to remove
        add_sections: Section titles to add
        focus_hints: Hints for re-scrape focus
        
    Returns:
        SpecFeedback instance
    """
    return SpecFeedback(
        approved=approved,
        rejection_reason=rejection_reason,
        suggested_changes=suggested_changes or [],
        additional_sources=additional_sources or [],
        remove_sections=remove_sections or [],
        add_sections=add_sections or [],
        focus_hints=focus_hints or [],
    )


__all__ = [
    "apply_feedback_to_spec",
    "create_feedback",
    "handle_spec_rejection",
    "prompt_user_feedback",
]
