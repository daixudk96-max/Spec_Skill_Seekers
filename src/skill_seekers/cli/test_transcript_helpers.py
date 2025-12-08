#!/usr/bin/env python3
"""
Transcript Test Helpers

提供用于测试 transcript 处理功能的辅助函数和验证工具。
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional


def create_sample_srt(content: Optional[str] = None) -> str:
    """
    创建用于测试的样本 SRT 文件。
    
    Args:
        content: 可选的自定义内容，如果未提供则使用默认内容
        
    Returns:
        临时文件路径
    """
    if content is None:
        content = """1
00:00:00,000 --> 00:00:03,000
Welcome to this lesson on Python programming.

2
00:00:03,500 --> 00:00:07,000
Today we'll learn about data structures.

3
00:00:07,500 --> 00:00:12,000
Let's start with lists, which are
mutable sequences in Python.

4
00:00:12,500 --> 00:00:18,000
You can create a list using square brackets,
for example: my_list = [1, 2, 3]

5
00:00:18,500 --> 00:00:25,000
Next, let's look at dictionaries.
They store key-value pairs.
"""
    
    fd, path = tempfile.mkstemp(suffix='.srt', prefix='test_transcript_')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return path


def create_sample_vtt(content: Optional[str] = None) -> str:
    """
    创建用于测试的样本 VTT 文件。
    
    Returns:
        临时文件路径
    """
    if content is None:
        content = """WEBVTT

00:00:00.000 --> 00:00:03.000
Welcome to this lesson on JavaScript.

00:00:03.500 --> 00:00:07.000
Today we'll learn about async programming.

00:00:07.500 --> 00:00:12.000
Let's start with Promises, which represent
eventual completion of an operation.
"""
    
    fd, path = tempfile.mkstemp(suffix='.vtt', prefix='test_transcript_')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return path


def create_sample_txt(content: Optional[str] = None) -> str:
    """
    创建用于测试的样本 TXT 文件。
    
    Returns:
        临时文件路径
    """
    if content is None:
        content = """Introduction to Machine Learning

Machine learning is a subset of artificial intelligence.
It enables systems to learn from data.

Key Concepts:
- Supervised Learning
- Unsupervised Learning
- Reinforcement Learning

Practice involves training models on datasets.
"""
    
    fd, path = tempfile.mkstemp(suffix='.txt', prefix='test_transcript_')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return path


def verify_transcript_output(data: Dict[str, Any], min_lessons: int = 1) -> Dict[str, Any]:
    """
    验证 TranscriptScraper 输出数据的结构和完整性。
    
    Args:
        data: TranscriptScraper 返回的数据字典
        min_lessons: 期望的最小课程数
        
    Returns:
        包含验证结果的字典
        
    Raises:
        AssertionError: 如果验证失败
    """
    errors = []
    warnings = []
    
    # 验证顶层字段
    required_fields = ['name', 'type', 'generated_at', 'total_lessons', 'lessons']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # 验证类型
    if data.get('type') != 'transcript':
        errors.append(f"Invalid type: {data.get('type')}, expected 'transcript'")
    
    # 验证课程数量
    total_lessons = data.get('total_lessons', 0)
    if total_lessons < min_lessons:
        errors.append(f"Insufficient lessons: {total_lessons}, expected >= {min_lessons}")
    
    lessons = data.get('lessons', [])
    if len(lessons) != total_lessons:
        warnings.append(f"Lesson count mismatch: total_lessons={total_lessons}, actual={len(lessons)}")
    
    # 验证每个课程的结构
    lesson_fields = ['title', 'content', 'source_path', 'word_count', 'char_count']
    for i, lesson in enumerate(lessons):
        for field in lesson_fields:
            if field not in lesson:
                errors.append(f"Lesson {i}: missing field '{field}'")
        
        # 验证内容不为空
        if not lesson.get('content', '').strip():
            errors.append(f"Lesson {i}: content is empty")
        
        # 验证词数和字符数一致性
        content = lesson.get('content', '')
        expected_word_count = len(content.split())
        expected_char_count = len(content)
        
        if abs(lesson.get('word_count', 0) - expected_word_count) > 5:
            warnings.append(f"Lesson {i}: word_count mismatch")
        
        if lesson.get('char_count', 0) != expected_char_count:
            warnings.append(f"Lesson {i}: char_count mismatch")
    
    # 验证没有残留的时间戳（针对 SRT/VTT）
    timestamp_patterns = [
        r'\d{2}:\d{2}:\d{2},\d{3}',  # SRT timestamp
        r'\d{2}:\d{2}:\d{2}\.\d{3}',  # VTT timestamp
        r'-->'  # Arrow separator
    ]
    import re
    for i, lesson in enumerate(lessons):
        content = lesson.get('content', '')
        for pattern in timestamp_patterns:
            if re.search(pattern, content):
                errors.append(f"Lesson {i}: contains residual timestamp pattern: {pattern}")
    
    result = {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'summary': {
            'total_lessons': total_lessons,
            'total_words': data.get('total_words', 0),
            'error_count': len(errors),
            'warning_count': len(warnings)
        }
    }
    
    return result


def verify_lesson_structure(lesson) -> Dict[str, Any]:
    """
    验证单个 Lesson 对象的结构。
    
    Args:
        lesson: Lesson dataclass 实例
        
    Returns:
        验证结果字典
    """
    errors = []
    
    # 验证必填字段
    if not hasattr(lesson, 'title') or not lesson.title:
        errors.append("Missing or empty title")
    
    if not hasattr(lesson, 'content') or not lesson.content:
        errors.append("Missing or empty content")
    
    if not hasattr(lesson, 'source_path'):
        errors.append("Missing source_path")
    
    # 验证方法存在
    if not hasattr(lesson, 'word_count') or not callable(lesson.word_count):
        errors.append("Missing word_count method")
    
    if not hasattr(lesson, 'char_count') or not callable(lesson.char_count):
        errors.append("Missing char_count method")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def cleanup_temp_files(paths: List[str]):
    """清理临时测试文件。"""
    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


class TranscriptTestFixture:
    """
    测试 fixture，用于管理测试文件和清理。
    """
    
    def __init__(self):
        self.temp_files: List[str] = []
        self.temp_dirs: List[str] = []
    
    def create_srt(self, content: Optional[str] = None) -> str:
        path = create_sample_srt(content)
        self.temp_files.append(path)
        return path
    
    def create_vtt(self, content: Optional[str] = None) -> str:
        path = create_sample_vtt(content)
        self.temp_files.append(path)
        return path
    
    def create_txt(self, content: Optional[str] = None) -> str:
        path = create_sample_txt(content)
        self.temp_files.append(path)
        return path
    
    def create_temp_dir(self) -> str:
        import tempfile
        dir_path = tempfile.mkdtemp(prefix='test_transcript_')
        self.temp_dirs.append(dir_path)
        return dir_path
    
    def cleanup(self):
        cleanup_temp_files(self.temp_files)
        for dir_path in self.temp_dirs:
            import shutil
            try:
                shutil.rmtree(dir_path)
            except Exception:
                pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False


if __name__ == '__main__':
    # 演示用法
    print("Creating sample files...")
    
    with TranscriptTestFixture() as fixture:
        srt_path = fixture.create_srt()
        vtt_path = fixture.create_vtt()
        txt_path = fixture.create_txt()
        
        print(f"SRT: {srt_path}")
        print(f"VTT: {vtt_path}")
        print(f"TXT: {txt_path}")
        
        # 测试解析
        try:
            from transcript_parser import parse_transcript
            
            lesson = parse_transcript(srt_path)
            result = verify_lesson_structure(lesson)
            print(f"\nLesson validation: {'✅ PASS' if result['valid'] else '❌ FAIL'}")
            if result['errors']:
                for error in result['errors']:
                    print(f"  - {error}")
        except ImportError:
            print("\nSkipped parsing test (module not in path)")
    
    print("\n✅ Test fixtures cleaned up")
