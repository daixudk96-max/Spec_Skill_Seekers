#!/usr/bin/env python3
"""
Transcript Scraper

将 transcript 文件转换为 Claude AI Skill。
这是面向 unified_scraper 的主接口，遵循与 doc_scraper、github_scraper、pdf_scraper 相同的模式。

主要功能：
1. 读取并解析 transcript 文件（.srt, .vtt, .txt, .md）
2. 生成结构化的 Skill 输出（包含摘要、关键点、练习题）
3. 支持 CLI 单文件处理和配置文件批量处理
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 导入本地模块
try:
    from transcript_parser import TranscriptParser, parse_transcript
    from data_types import Lesson
except ImportError:
    from skill_seekers.cli.transcript_parser import TranscriptParser, parse_transcript
    from skill_seekers.cli.data_types import Lesson

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TranscriptScraper:
    """
    Transcript 文件到 Skill 的转换器。
    
    遵循 Skill_Seekers 架构，提供与其他 scraper 一致的接口：
    - fetch(): 获取和解析源内容
    - clean(): 清理和规范化内容（在 parser 中已完成）
    - chunk(): 处理超长内容（大多数情况下不需要）
    - scrape(): 主入口，执行完整流程
    """
    
    # Skill 输出的标准 Prompt 模板
    SKILL_PROMPT_TEMPLATE = """You are processing a course transcript. 
Your output MUST include the following sections:

1. **Summary**: A concise 2-3 paragraph overview of the lesson
2. **Key Concepts**: A bulleted list of the main concepts covered
3. **Practice Exercises**: Three distinct exercises to reinforce the material

Content to analyze:
---
{content}
---"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 TranscriptScraper。
        
        Args:
            config: 配置字典，可以是：
                - 完整的 unified config（包含 sources 数组）
                - 单个 transcript 源配置
                - 简单配置（仅包含 path 和 name）
        """
        self.config = config
        
        # 解析配置
        self.name = config.get('name', 'transcript_skill')
        self.paths = self._resolve_paths(config)
        
        # 输出目录
        self.output_dir = f"output/{self.name}"
        self.data_dir = f"output/{self.name}_data"
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 存储解析后的课程
        self.lessons: List[Lesson] = []
        self.scraped_data: Dict[str, Any] = {}
        
        logger.info(f"TranscriptScraper initialized: {len(self.paths)} files to process")
    
    def _resolve_paths(self, config: Dict[str, Any]) -> List[str]:
        """从配置中解析所有 transcript 文件路径。"""
        paths = []
        
        # 单文件路径
        if 'path' in config:
            paths.append(config['path'])
        
        # 多文件路径数组
        if 'paths' in config:
            paths.extend(config['paths'])
        
        # 目录扫描
        if 'directory' in config:
            dir_path = Path(config['directory'])
            patterns = config.get('patterns', ['*.srt', '*.vtt', '*.txt'])
            for pattern in patterns:
                paths.extend(str(p) for p in dir_path.glob(pattern))
        
        # 去重并验证
        unique_paths = list(dict.fromkeys(paths))
        valid_paths = [p for p in unique_paths if Path(p).exists()]
        
        if len(valid_paths) < len(unique_paths):
            missing = set(unique_paths) - set(valid_paths)
            logger.warning(f"Some files not found: {missing}")
        
        return valid_paths
    
    def fetch(self) -> List[Lesson]:
        """
        获取并解析所有 transcript 文件。
        
        Returns:
            解析后的 Lesson 对象列表
        """
        logger.info("Fetching and parsing transcripts...")
        
        for path in self.paths:
            try:
                lesson = parse_transcript(path)
                self.lessons.append(lesson)
                logger.info(f"✅ Parsed: {lesson.title} ({lesson.word_count()} words)")
            except Exception as e:
                logger.error(f"❌ Failed to parse {path}: {e}")
        
        logger.info(f"Successfully parsed {len(self.lessons)}/{len(self.paths)} files")
        return self.lessons
    
    def clean(self) -> List[Lesson]:
        """
        清理和规范化内容。
        
        在 TranscriptParser 中已完成大部分清理工作，
        这里可以进行额外的后处理。
        
        Returns:
            清理后的 Lesson 列表
        """
        # TranscriptParser 已处理了时间戳移除和行合并
        # 这里可以添加额外的清理逻辑
        return self.lessons
    
    def chunk(self, max_chars: int = 150000) -> List[Lesson]:
        """
        分割过长的内容。
        
        Claude 200k context 通常足够处理单个课程，
        但如果内容过长，需要分割。
        
        Args:
            max_chars: 单个 lesson 的最大字符数
            
        Returns:
            可能分割后的 Lesson 列表
        """
        chunked_lessons = []
        
        for lesson in self.lessons:
            if lesson.char_count() <= max_chars:
                chunked_lessons.append(lesson)
            else:
                # 分割超长内容
                chunks = self._split_content(lesson.content, max_chars)
                for i, chunk in enumerate(chunks):
                    chunked_lesson = Lesson(
                        title=f"{lesson.title} (Part {i+1})",
                        content=chunk,
                        source_path=lesson.source_path
                    )
                    chunked_lessons.append(chunked_lesson)
                logger.info(f"Split {lesson.title} into {len(chunks)} parts")
        
        self.lessons = chunked_lessons
        return self.lessons
    
    def _split_content(self, content: str, max_chars: int) -> List[str]:
        """在段落边界处分割内容。"""
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_len = len(para) + 2  # 加上换行符
            if current_length + para_len > max_chars and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_len
            else:
                current_chunk.append(para)
                current_length += para_len
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def scrape(self) -> Dict[str, Any]:
        """
        执行完整的 scraping 流程。
        
        Returns:
            包含所有提取数据的字典
        """
        logger.info("=" * 60)
        logger.info(f"Starting transcript scraping: {self.name}")
        logger.info("=" * 60)
        
        # Step 1: 获取和解析
        self.fetch()
        
        # Step 2: 清理
        self.clean()
        
        # Step 3: 分块（如有必要）
        self.chunk()
        
        # Step 4: 构建输出数据
        self.scraped_data = self._build_data()
        
        # Step 5: 保存数据
        self._save_data()
        
        logger.info(f"✅ Scraping complete: {len(self.lessons)} lessons processed")
        return self.scraped_data
    
    def _build_data(self) -> Dict[str, Any]:
        """构建标准输出数据格式。"""
        lessons_data = []
        
        for lesson in self.lessons:
            lessons_data.append({
                'title': lesson.title,
                'content': lesson.content,
                'source_path': lesson.source_path,
                'word_count': lesson.word_count(),
                'char_count': lesson.char_count(),
                'sections': lesson.sections
            })
        
        return {
            'name': self.name,
            'type': 'transcript',
            'generated_at': datetime.now().isoformat(),
            'total_lessons': len(self.lessons),
            'total_words': sum(l.word_count() for l in self.lessons),
            'lessons': lessons_data,
            'prompt_template': self.SKILL_PROMPT_TEMPLATE
        }
    
    def _save_data(self):
        """保存提取的数据到 JSON 文件。"""
        data_file = os.path.join(self.data_dir, 'transcript_data.json')
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved: {data_file}")
        
        # 保存摘要文件（与其他 scraper 保持一致）
        summary = {
            'name': self.name,
            'type': 'transcript',
            'total_lessons': len(self.lessons),
            'total_words': sum(l.word_count() for l in self.lessons),
            'lessons': [
                {'title': l.title, 'words': l.word_count()}
                for l in self.lessons
            ]
        }
        summary_file = os.path.join(self.data_dir, 'summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def build_skill(self) -> str:
        """
        生成 Skill 文件。
        
        Returns:
            生成的 SKILL.md 文件路径
        """
        if not self.scraped_data:
            self.scrape()
        
        skill_content = self._generate_skill_md()
        
        skill_path = os.path.join(self.output_dir, 'SKILL.md')
        with open(skill_path, 'w', encoding='utf-8') as f:
            f.write(skill_content)
        
        logger.info(f"Skill generated: {skill_path}")
        return skill_path
    
    def _generate_skill_md(self) -> str:
        """生成 SKILL.md 内容，调用 Claude API 生成结构化输出。"""
        lines = [
            f"# {self.name}",
            "",
            "## Overview",
            "",
            f"This skill was generated from {len(self.lessons)} transcript(s).",
            f"Total word count: {sum(l.word_count() for l in self.lessons):,}",
            "",
        ]
        
        for lesson in self.lessons:
            lines.extend([
                f"## {lesson.title}",
                "",
                f"*Source: {lesson.source_path}*",
                "",
            ])
            
            # 尝试使用 Claude API 生成结构化内容
            enhanced_content = self._enhance_with_llm(lesson)
            
            if enhanced_content:
                lines.extend([enhanced_content, ""])
            else:
                # 如果 LLM 调用失败，使用纯内容
                lines.extend([
                    "### Content",
                    "",
                    lesson.content,
                    ""
                ])
            
            lines.extend(["---", ""])
        
        return '\n'.join(lines)
    
    def _enhance_with_llm(self, lesson: Lesson) -> Optional[str]:
        """
        使用 Claude API 生成结构化的 Skill 内容。
        
        Returns:
            增强后的 markdown 内容，如果失败返回 None
        """
        try:
            import anthropic
        except ImportError:
            logger.warning("anthropic 包未安装，跳过 LLM 增强。使用 'pip install anthropic' 安装。")
            return None
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            logger.warning("未设置 ANTHROPIC_API_KEY 环境变量，跳过 LLM 增强。")
            return None
        
        logger.info(f"🤖 使用 Claude API 增强内容: {lesson.title}")
        
        # 构建 prompt
        prompt = f"""你是一位专业的课程内容分析师。请分析以下课程 transcript，并生成结构化的学习资料。

## 课程标题
{lesson.title}

## 原始 Transcript 内容
{lesson.content[:50000]}  # 限制内容长度

---

请按以下格式输出（使用中文）：

### 📝 课程摘要
（2-3 段简洁的课程概述，帮助读者快速了解课程主题和核心价值）

### 🎯 关键要点
（用列表形式列出 5-10 个核心概念和关键知识点）

### 💡 核心概念详解
（对最重要的 3-5 个概念进行详细解释）

### 📋 实践练习
（设计 3 道练习题，帮助巩固所学知识）

### 🔗 延伸学习
（提供 2-3 个进一步学习的建议方向）

请确保输出内容：
1. 准确提取原文的核心观点，不要编造
2. 使用清晰的语言组织信息
3. 保持结构化和可读性"""

        try:
            client = anthropic.Anthropic(api_key=api_key)
            
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            enhanced_content = message.content[0].text
            logger.info(f"✅ LLM 增强完成: {len(enhanced_content)} 字符")
            return enhanced_content
            
        except Exception as e:
            logger.error(f"❌ Claude API 调用失败: {e}")
            return None


def main():
    """CLI 入口点。"""
    parser = argparse.ArgumentParser(
        description='Convert transcripts to Claude AI skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file
  skill-seekers transcript --input lecture.srt
  
  # Process multiple files
  skill-seekers transcript --input lecture1.srt --input lecture2.srt
  
  # Process directory
  skill-seekers transcript --directory ./transcripts --patterns "*.srt" "*.vtt"
  
  # Use config file
  skill-seekers transcript --config transcript_config.json
        """
    )
    
    parser.add_argument('--input', '-i', action='append', dest='inputs',
                       help='Input transcript file (can specify multiple)')
    parser.add_argument('--directory', '-d',
                       help='Directory containing transcript files')
    parser.add_argument('--patterns', nargs='+', default=['*.srt', '*.vtt', '*.txt'],
                       help='File patterns to match (default: *.srt *.vtt *.txt)')
    parser.add_argument('--config', '-c',
                       help='Path to config JSON file')
    parser.add_argument('--name', '-n', default='transcript_skill',
                       help='Name for the output skill')
    
    args = parser.parse_args()
    
    # 构建配置
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        config = {
            'name': args.name,
            'paths': args.inputs or [],
            'patterns': args.patterns
        }
        if args.directory:
            config['directory'] = args.directory
    
    if not config.get('paths') and not config.get('directory') and not config.get('path'):
        parser.error("Must specify --input, --directory, or --config")
    
    # 执行 scraping
    scraper = TranscriptScraper(config)
    scraper.scrape()
    scraper.build_skill()
    
    print(f"\n✅ Skill generated: output/{config.get('name', 'transcript_skill')}/SKILL.md")


if __name__ == '__main__':
    main()
