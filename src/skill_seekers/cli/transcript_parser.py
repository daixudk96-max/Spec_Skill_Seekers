#!/usr/bin/env python3
"""
Transcript Parser

解析各种 transcript 文件格式（.srt, .vtt, .txt, .md）并生成标准化的 Lesson 对象。

支持的格式：
- .srt (SubRip 字幕格式): 带时间戳的字幕文件
- .vtt (WebVTT 格式): 网络视频字幕格式
- .txt / .md: 纯文本/Markdown 文件

主要功能：
- 去除时间戳和序号
- 合并分散的字幕行为连贯段落
- 保留语义结构
"""

import re
import logging
from pathlib import Path
from typing import Optional

from data_types import Lesson

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptParser:
    """
    Transcript 文件解析器。
    
    将各种格式的字幕/转录文件转换为统一的 Lesson 对象。
    """
    
    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = {'.srt', '.vtt', '.txt', '.md'}
    
    # SRT 时间戳正则表达式: 00:00:00,000 --> 00:00:00,000
    SRT_TIMESTAMP_PATTERN = re.compile(
        r'^\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}$',
        re.MULTILINE
    )
    
    # VTT 时间戳正则表达式: 00:00:00.000 --> 00:00:00.000
    VTT_TIMESTAMP_PATTERN = re.compile(
        r'^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}',
        re.MULTILINE
    )
    
    # SRT 序号行正则表达式
    SRT_INDEX_PATTERN = re.compile(r'^\d+$', re.MULTILINE)
    
    # VTT 头部正则表达式
    VTT_HEADER_PATTERN = re.compile(r'^WEBVTT.*$', re.MULTILINE | re.IGNORECASE)
    
    def __init__(self, file_path: str):
        """
        初始化解析器。
        
        Args:
            file_path: transcript 文件路径
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        self.file_path = Path(file_path)
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"Transcript file not found: {file_path}")
        
        suffix = self.file_path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported format: {suffix}. "
                f"Supported formats: {self.SUPPORTED_EXTENSIONS}"
            )
        
        self.format = suffix
        logger.info(f"Initialized parser for {suffix} file: {file_path}")
    
    def parse(self) -> Lesson:
        """
        解析 transcript 文件并返回 Lesson 对象。
        
        Returns:
            Lesson: 标准化的课程内容对象
        """
        logger.info(f"Parsing transcript: {self.file_path}")
        
        # 读取文件内容
        content = self._read_file()
        
        # 根据格式选择解析方法
        if self.format == '.srt':
            parsed_content = self._parse_srt(content)
        elif self.format == '.vtt':
            parsed_content = self._parse_vtt(content)
        else:
            # .txt 和 .md 直接使用原始内容
            parsed_content = self._parse_plain_text(content)
        
        # 创建 Lesson 对象
        lesson = Lesson.from_file(
            file_path=str(self.file_path),
            content=parsed_content
        )
        
        logger.info(f"Parsed lesson: {lesson.title} ({lesson.word_count()} words)")
        return lesson
    
    def _read_file(self) -> str:
        """读取文件内容，自动处理编码。"""
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        # 最后尝试忽略错误
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _parse_srt(self, content: str) -> str:
        """
        解析 SRT 格式字幕。
        
        SRT 格式结构:
        1
        00:00:00,000 --> 00:00:02,000
        字幕文本行1
        字幕文本行2
        
        2
        00:00:02,500 --> 00:00:05,000
        下一段字幕
        """
        logger.debug("Parsing SRT format")
        
        # 移除时间戳行
        content = self.SRT_TIMESTAMP_PATTERN.sub('', content)
        
        # 移除序号行
        content = self.SRT_INDEX_PATTERN.sub('', content)
        
        # 规范化空白和合并行
        return self._normalize_content(content)
    
    def _parse_vtt(self, content: str) -> str:
        """
        解析 VTT 格式字幕。
        
        VTT 格式结构:
        WEBVTT
        
        00:00:00.000 --> 00:00:02.000
        字幕文本
        
        00:00:02.500 --> 00:00:05.000
        下一段字幕
        """
        logger.debug("Parsing VTT format")
        
        # 移除 WEBVTT 头部
        content = self.VTT_HEADER_PATTERN.sub('', content)
        
        # 移除时间戳行
        content = self.VTT_TIMESTAMP_PATTERN.sub('', content)
        
        # 移除可能的 cue ID 行（通常是数字或标识符）
        content = re.sub(r'^[a-zA-Z0-9_-]+$', '', content, flags=re.MULTILINE)
        
        # 规范化空白和合并行
        return self._normalize_content(content)
    
    def _parse_plain_text(self, content: str) -> str:
        """解析纯文本/Markdown 文件。"""
        logger.debug("Parsing plain text format")
        return self._normalize_content(content)
    
    def _normalize_content(self, content: str) -> str:
        """
        规范化内容：清理多余空白，合并分散的行。
        
        Args:
            content: 原始内容
            
        Returns:
            规范化后的内容
        """
        # 移除 HTML 标签（VTT 可能包含格式标签）
        content = re.sub(r'<[^>]+>', '', content)
        
        # 分割为行
        lines = content.split('\n')
        
        # 过滤空行和仅包含空白的行
        lines = [line.strip() for line in lines if line.strip()]
        
        # 合并连续的短行（可能是同一句话被分割了）
        merged_lines = []
        buffer = []
        
        for line in lines:
            # 如果这一行看起来是句子的继续（不以大写开头，或者不是新段落）
            if buffer and not self._is_new_sentence(line):
                buffer.append(line)
            else:
                if buffer:
                    merged_lines.append(' '.join(buffer))
                buffer = [line]
        
        if buffer:
            merged_lines.append(' '.join(buffer))
        
        # 用双换行符连接段落
        result = '\n\n'.join(merged_lines)
        
        # 最终清理
        result = re.sub(r'\n{3,}', '\n\n', result)  # 不超过两个连续换行
        result = re.sub(r' +', ' ', result)  # 合并多余空格
        
        return result.strip()
    
    def _is_new_sentence(self, line: str) -> bool:
        """
        判断一行是否是新句子的开始。
        
        Args:
            line: 要检查的行
            
        Returns:
            True 如果是新句子开始
        """
        if not line:
            return True
        
        # 以大写字母开头通常表示新句子（对于英文）
        # 对于中文，检查是否有明显的段落标记
        first_char = line[0]
        
        # 新段落标记
        paragraph_markers = ['#', '*', '-', '•', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        
        if first_char in paragraph_markers:
            return True
        
        # 英文大写开头
        if first_char.isupper():
            return True
        
        # 中文常见的段落开头
        if first_char in '第一二三四五六七八九十':
            return True
        
        return False


def parse_transcript(file_path: str) -> Lesson:
    """
    解析 transcript 文件的便捷函数。
    
    Args:
        file_path: transcript 文件路径
        
    Returns:
        Lesson: 标准化的课程内容对象
    """
    parser = TranscriptParser(file_path)
    return parser.parse()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python transcript_parser.py <transcript_file>")
        print("Supported formats: .srt, .vtt, .txt, .md")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        lesson = parse_transcript(file_path)
        print(f"\n✅ Successfully parsed transcript")
        print(f"   Title: {lesson.title}")
        print(f"   Source: {lesson.source_path}")
        print(f"   Word Count: {lesson.word_count()}")
        print(f"   Character Count: {lesson.char_count()}")
        print(f"\n--- Content Preview (first 500 chars) ---")
        print(lesson.content[:500])
        if len(lesson.content) > 500:
            print("...")
    except Exception as e:
        print(f"\n❌ Error parsing transcript: {e}")
        sys.exit(1)
