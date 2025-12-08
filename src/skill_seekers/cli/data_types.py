#!/usr/bin/env python3
"""
Data Types for Skill Seekers

Contains dataclasses and type definitions used across the project.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


@dataclass
class Lesson:
    """
    教学课程内容的标准化表示。
    从各种 transcript 格式（如 .srt, .vtt, .txt）解析后生成此对象。
    
    Attributes:
        title: 课程标题（从文件名或内容推断）
        content: 清理后的正文内容（去除时间戳和格式化字符）
        source_path: 原始文件的路径
        sections: 可选的章节列表（未来支持基于时间间隔的分段）
    """
    title: str
    content: str
    source_path: str
    sections: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """验证必填字段。"""
        if not self.title:
            raise ValueError("Lesson title cannot be empty")
        if not self.content:
            raise ValueError("Lesson content cannot be empty")
    
    @classmethod
    def from_file(cls, file_path: str, content: str, title: Optional[str] = None) -> "Lesson":
        """
        从文件路径和内容创建 Lesson 实例的便捷方法。
        
        Args:
            file_path: 原始文件路径
            content: 解析后的文本内容
            title: 可选的标题，如果未提供则从文件名推断
            
        Returns:
            Lesson 实例
        """
        if not title:
            # 从文件名推断标题
            title = Path(file_path).stem.replace('_', ' ').replace('-', ' ').title()
        return cls(title=title, content=content, source_path=file_path)
    
    def word_count(self) -> int:
        """返回内容的词数。"""
        return len(self.content.split())
    
    def char_count(self) -> int:
        """返回内容的字符数。"""
        return len(self.content)
