#!/usr/bin/env python3
"""
Transcript E2E Integration Tests

端到端集成测试，验证 transcript 处理的完整流程。
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path

# 确保模块在导入路径中
sys.path.insert(0, str(Path(__file__).parent))

from test_transcript_helpers import (
    TranscriptTestFixture, 
    verify_transcript_output,
    verify_lesson_structure
)


class TestTranscriptParser(unittest.TestCase):
    """TranscriptParser 单元测试。"""
    
    def setUp(self):
        self.fixture = TranscriptTestFixture()
    
    def tearDown(self):
        self.fixture.cleanup()
    
    def test_parse_srt_file(self):
        """测试 SRT 文件解析。"""
        from transcript_parser import parse_transcript
        
        srt_path = self.fixture.create_srt()
        lesson = parse_transcript(srt_path)
        
        # 验证基本结构
        self.assertIsNotNone(lesson)
        self.assertIsNotNone(lesson.title)
        self.assertIsNotNone(lesson.content)
        self.assertEqual(lesson.source_path, srt_path)
        
        # 验证时间戳已被移除
        self.assertNotIn('-->', lesson.content)
        self.assertNotIn('00:00:00,000', lesson.content)
        
        # 验证内容存在
        self.assertIn('Python', lesson.content)
        self.assertIn('list', lesson.content.lower())
    
    def test_parse_vtt_file(self):
        """测试 VTT 文件解析。"""
        from transcript_parser import parse_transcript
        
        vtt_path = self.fixture.create_vtt()
        lesson = parse_transcript(vtt_path)
        
        # 验证基本结构
        self.assertIsNotNone(lesson)
        self.assertNotIn('WEBVTT', lesson.content)
        self.assertNotIn('-->', lesson.content)
        
        # 验证内容存在
        self.assertIn('JavaScript', lesson.content)
    
    def test_parse_txt_file(self):
        """测试纯文本文件解析。"""
        from transcript_parser import parse_transcript
        
        txt_path = self.fixture.create_txt()
        lesson = parse_transcript(txt_path)
        
        # 验证基本结构
        self.assertIsNotNone(lesson)
        self.assertIn('Machine Learning', lesson.content)
    
    def test_unsupported_format(self):
        """测试不支持的格式抛出异常。"""
        from transcript_parser import TranscriptParser
        
        # 创建一个假的 .xyz 文件
        fd, path = tempfile.mkstemp(suffix='.xyz')
        os.close(fd)
        self.fixture.temp_files.append(path)
        
        with self.assertRaises(ValueError) as context:
            TranscriptParser(path)
        
        self.assertIn('Unsupported format', str(context.exception))
    
    def test_file_not_found(self):
        """测试文件不存在时抛出异常。"""
        from transcript_parser import TranscriptParser
        
        with self.assertRaises(FileNotFoundError):
            TranscriptParser('/nonexistent/path/file.srt')
    
    def test_lesson_word_count(self):
        """测试 Lesson 词数统计。"""
        from transcript_parser import parse_transcript
        
        txt_path = self.fixture.create_txt()
        lesson = parse_transcript(txt_path)
        
        word_count = lesson.word_count()
        self.assertGreater(word_count, 0)
        
        # 预期大约有 30-50 个词
        self.assertGreater(word_count, 20)
        self.assertLess(word_count, 100)


class TestTranscriptScraper(unittest.TestCase):
    """TranscriptScraper 集成测试。"""
    
    def setUp(self):
        self.fixture = TranscriptTestFixture()
        self.output_dir = self.fixture.create_temp_dir()
    
    def tearDown(self):
        self.fixture.cleanup()
    
    def test_scrape_single_file(self):
        """测试单文件 scraping。"""
        from transcript_scraper import TranscriptScraper
        
        srt_path = self.fixture.create_srt()
        
        config = {
            'name': 'test_skill',
            'path': srt_path
        }
        
        # 临时更改输出目录
        original_cwd = os.getcwd()
        os.chdir(self.output_dir)
        
        try:
            scraper = TranscriptScraper(config)
            data = scraper.scrape()
            
            # 验证输出结构
            result = verify_transcript_output(data, min_lessons=1)
            self.assertTrue(result['valid'], f"Validation errors: {result['errors']}")
            
            # 验证数据内容
            self.assertEqual(data['type'], 'transcript')
            self.assertGreater(data['total_lessons'], 0)
        finally:
            os.chdir(original_cwd)
    
    def test_scrape_multiple_files(self):
        """测试多文件 scraping。"""
        from transcript_scraper import TranscriptScraper
        
        srt_path = self.fixture.create_srt()
        vtt_path = self.fixture.create_vtt()
        
        config = {
            'name': 'multi_test',
            'paths': [srt_path, vtt_path]
        }
        
        original_cwd = os.getcwd()
        os.chdir(self.output_dir)
        
        try:
            scraper = TranscriptScraper(config)
            data = scraper.scrape()
            
            result = verify_transcript_output(data, min_lessons=2)
            self.assertTrue(result['valid'], f"Validation errors: {result['errors']}")
            self.assertEqual(data['total_lessons'], 2)
        finally:
            os.chdir(original_cwd)
    
    def test_scrape_directory(self):
        """测试目录 scraping。"""
        from transcript_scraper import TranscriptScraper
        
        # 创建带样本文件的目录
        test_dir = self.fixture.create_temp_dir()
        
        # 在目录中创建文件
        srt_content = """1
00:00:00,000 --> 00:00:03,000
Test content for directory scraping.
"""
        srt_path = os.path.join(test_dir, 'lesson.srt')
        with open(srt_path, 'w') as f:
            f.write(srt_content)
        
        config = {
            'name': 'dir_test',
            'directory': test_dir,
            'patterns': ['*.srt']
        }
        
        original_cwd = os.getcwd()
        os.chdir(self.output_dir)
        
        try:
            scraper = TranscriptScraper(config)
            data = scraper.scrape()
            
            self.assertGreater(data['total_lessons'], 0)
        finally:
            os.chdir(original_cwd)
    
    def test_build_skill(self):
        """测试 Skill 文件生成。"""
        from transcript_scraper import TranscriptScraper
        
        srt_path = self.fixture.create_srt()
        
        config = {
            'name': 'skill_test',
            'path': srt_path
        }
        
        original_cwd = os.getcwd()
        os.chdir(self.output_dir)
        
        try:
            scraper = TranscriptScraper(config)
            skill_path = scraper.build_skill()
            
            self.assertTrue(os.path.exists(skill_path))
            
            with open(skill_path, 'r') as f:
                content = f.read()
            
            self.assertIn('# skill_test', content)
            self.assertIn('## Lessons', content)
        finally:
            os.chdir(original_cwd)


class TestConfigValidator(unittest.TestCase):
    """ConfigValidator transcript 类型验证测试。"""
    
    def setUp(self):
        self.fixture = TranscriptTestFixture()
    
    def tearDown(self):
        self.fixture.cleanup()
    
    def test_validate_transcript_source_with_path(self):
        """测试带 path 的 transcript 源验证。"""
        from config_validator import ConfigValidator
        
        srt_path = self.fixture.create_srt()
        
        config = {
            'name': 'test',
            'description': 'Test skill',
            'sources': [
                {
                    'type': 'transcript',
                    'path': srt_path
                }
            ]
        }
        
        validator = ConfigValidator(config)
        self.assertTrue(validator.validate())
    
    def test_validate_transcript_source_with_directory(self):
        """测试带 directory 的 transcript 源验证。"""
        from config_validator import ConfigValidator
        
        test_dir = self.fixture.create_temp_dir()
        
        config = {
            'name': 'test',
            'description': 'Test skill',
            'sources': [
                {
                    'type': 'transcript',
                    'directory': test_dir
                }
            ]
        }
        
        validator = ConfigValidator(config)
        self.assertTrue(validator.validate())
    
    def test_validate_transcript_source_missing_path(self):
        """测试缺少路径的 transcript 源验证失败。"""
        from config_validator import ConfigValidator
        
        config = {
            'name': 'test',
            'description': 'Test skill',
            'sources': [
                {
                    'type': 'transcript'
                    # 缺少 path, paths, directory
                }
            ]
        }
        
        validator = ConfigValidator(config)
        with self.assertRaises(ValueError) as context:
            validator.validate()
        
        self.assertIn('Missing required field', str(context.exception))


class TestUnifiedScraperIntegration(unittest.TestCase):
    """Unified Scraper transcript 集成测试。"""
    
    def setUp(self):
        self.fixture = TranscriptTestFixture()
        self.output_dir = self.fixture.create_temp_dir()
    
    def tearDown(self):
        self.fixture.cleanup()
    
    def test_unified_config_with_transcript(self):
        """测试包含 transcript 源的 unified 配置。"""
        from config_validator import ConfigValidator
        
        srt_path = self.fixture.create_srt()
        
        unified_config = {
            'name': 'multi_source_test',
            'description': 'Test with transcript',
            'merge_mode': 'rule-based',
            'sources': [
                {
                    'type': 'transcript',
                    'path': srt_path
                }
            ]
        }
        
        validator = ConfigValidator(unified_config)
        self.assertTrue(validator.validate())
        self.assertTrue(validator.is_unified)
        
        # 验证可以获取 transcript 类型的源
        transcript_sources = validator.get_sources_by_type('transcript')
        self.assertEqual(len(transcript_sources), 1)


def run_tests():
    """运行所有测试并输出报告。"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestTranscriptParser))
    suite.addTests(loader.loadTestsFromTestCase(TestTranscriptScraper))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestUnifiedScraperIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回是否全部通过
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
