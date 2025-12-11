#!/usr/bin/env python3
"""
Tests for cli/install_skill.py functionality
"""

import os
import sys
import unittest
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from skill_seekers.cli.install_skill import (
    get_claude_skills_dir,
    install_skill,
    _validate_flags,
    _safe_extract_zip,
    _create_backup,
)


class TestGetClaudeSkillsDir(unittest.TestCase):
    """Test get_claude_skills_dir() cross-platform directory resolution"""

    def test_env_override(self):
        """Test CLAUDE_SKILLS_DIR environment variable override"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CLAUDE_SKILLS_DIR": tmpdir}):
                result = get_claude_skills_dir()
                self.assertEqual(result, Path(tmpdir).resolve())

    def test_env_override_with_tilde(self):
        """Test environment variable with tilde expansion"""
        with patch.dict(os.environ, {"CLAUDE_SKILLS_DIR": "~/test-skills"}):
            result = get_claude_skills_dir()
            self.assertEqual(result, Path.home() / "test-skills")

    def test_windows_default(self):
        """Test Windows default path resolution"""
        # Preserve essential env vars for Path.home() to work
        preserved_env = {
            "USERPROFILE": os.environ.get("USERPROFILE", ""),
            "HOME": os.environ.get("HOME", ""),
            "HOMEDRIVE": os.environ.get("HOMEDRIVE", ""),
            "HOMEPATH": os.environ.get("HOMEPATH", ""),
        }
        with patch("sys.platform", "win32"):
            with patch.dict(os.environ, {**preserved_env, "APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}, clear=True):
                result = get_claude_skills_dir()
                # Should fall back to ~/.claude/skills since Claude dir doesn't exist
                self.assertTrue(str(result).endswith(".claude\\skills") or 
                               str(result).endswith(".claude/skills"))

    def test_macos_default(self):
        """Test macOS default path resolution"""
        preserved_env = {
            "USERPROFILE": os.environ.get("USERPROFILE", ""),
            "HOME": os.environ.get("HOME", ""),
        }
        with patch("sys.platform", "darwin"):
            with patch.dict(os.environ, preserved_env, clear=True):
                result = get_claude_skills_dir()
                # Should fall back to ~/.claude/skills
                expected_suffix = ".claude/skills" if "/" in str(result) else ".claude\\skills"
                self.assertTrue(str(result).endswith(expected_suffix))

    def test_linux_default(self):
        """Test Linux default path resolution"""
        preserved_env = {
            "USERPROFILE": os.environ.get("USERPROFILE", ""),
            "HOME": os.environ.get("HOME", ""),
        }
        with patch("sys.platform", "linux"):
            with patch.dict(os.environ, preserved_env, clear=True):
                result = get_claude_skills_dir()
                expected_suffix = ".claude/skills" if "/" in str(result) else ".claude\\skills"
                self.assertTrue(str(result).endswith(expected_suffix))


class TestValidateFlags(unittest.TestCase):
    """Test flag validation"""

    def test_overwrite_and_backup_mutually_exclusive(self):
        """Test that --overwrite and --backup are mutually exclusive"""
        with self.assertRaises(ValueError) as ctx:
            _validate_flags(overwrite=True, backup=True)
        self.assertIn("mutually exclusive", str(ctx.exception))

    def test_overwrite_only(self):
        """Test --overwrite alone is valid"""
        _validate_flags(overwrite=True, backup=False)  # Should not raise

    def test_backup_only(self):
        """Test --backup alone is valid"""
        _validate_flags(overwrite=False, backup=True)  # Should not raise

    def test_neither_flag(self):
        """Test no flags is valid"""
        _validate_flags(overwrite=False, backup=False)  # Should not raise


class TestInstallSkill(unittest.TestCase):
    """Test install_skill() core functionality"""

    def create_test_skill_directory(self, tmpdir, name="test-skill"):
        """Helper to create a test skill directory"""
        skill_dir = Path(tmpdir) / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: test-skill\n---\n# Test Skill")
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "index.md").write_text("# Index")
        return skill_dir

    def create_test_skill_zip(self, tmpdir, name="test-skill"):
        """Helper to create a test skill zip"""
        skill_dir = self.create_test_skill_directory(tmpdir, name)
        zip_path = Path(tmpdir) / f"{name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in skill_dir.rglob("*"):
                if file.is_file():
                    arcname = f"{name}/{file.relative_to(skill_dir)}"
                    zf.write(file, arcname)
        
        return zip_path

    def test_install_from_directory(self):
        """Test installing from a skill directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = self.create_test_skill_directory(tmpdir)
            target_dir = Path(tmpdir) / "skills"
            
            success, installed_path = install_skill(
                skill_dir, target_dir=target_dir
            )
            
            self.assertTrue(success)
            self.assertIsNotNone(installed_path)
            self.assertTrue(installed_path.exists())
            self.assertTrue((installed_path / "SKILL.md").exists())

    def test_install_from_zip(self):
        """Test installing from a .zip file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = self.create_test_skill_zip(tmpdir)
            target_dir = Path(tmpdir) / "skills"
            
            success, installed_path = install_skill(
                zip_path, target_dir=target_dir
            )
            
            self.assertTrue(success)
            self.assertIsNotNone(installed_path)
            self.assertTrue(installed_path.exists())
            self.assertTrue((installed_path / "SKILL.md").exists())

    def test_install_nonexistent_source(self):
        """Test installing from nonexistent source fails"""
        success, path = install_skill(Path("/nonexistent/path"))
        self.assertFalse(success)
        self.assertIsNone(path)

    def test_install_conflict_default_fails(self):
        """Test that installing over existing skill fails by default"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = self.create_test_skill_directory(tmpdir)
            target_dir = Path(tmpdir) / "skills"
            
            # First install
            success1, _ = install_skill(skill_dir, target_dir=target_dir)
            self.assertTrue(success1)
            
            # Second install should fail
            success2, _ = install_skill(skill_dir, target_dir=target_dir)
            self.assertFalse(success2)

    def test_install_overwrite(self):
        """Test --overwrite replaces existing skill"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = self.create_test_skill_directory(tmpdir)
            target_dir = Path(tmpdir) / "skills"
            
            # First install
            success1, path1 = install_skill(skill_dir, target_dir=target_dir)
            self.assertTrue(success1)
            
            # Modify the source
            (skill_dir / "SKILL.md").write_text("# Updated")
            
            # Install with overwrite
            success2, path2 = install_skill(
                skill_dir, target_dir=target_dir, overwrite=True
            )
            self.assertTrue(success2)
            
            # Check content was updated
            content = (path2 / "SKILL.md").read_text()
            self.assertEqual(content, "# Updated")

    def test_install_backup(self):
        """Test --backup creates backup of existing skill"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = self.create_test_skill_directory(tmpdir)
            target_dir = Path(tmpdir) / "skills"
            
            # First install
            success1, _ = install_skill(skill_dir, target_dir=target_dir)
            self.assertTrue(success1)
            
            # Install with backup
            success2, _ = install_skill(
                skill_dir, target_dir=target_dir, backup=True
            )
            self.assertTrue(success2)
            
            # Check backup was created
            backup_dirs = [d for d in target_dir.iterdir() 
                          if d.name.startswith("test-skill-backup-")]
            self.assertEqual(len(backup_dirs), 1)

    def test_dry_run(self):
        """Test --dry-run doesn't make changes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = self.create_test_skill_directory(tmpdir)
            target_dir = Path(tmpdir) / "skills"
            
            success, path = install_skill(
                skill_dir, target_dir=target_dir, dry_run=True
            )
            
            self.assertTrue(success)
            self.assertIsNotNone(path)
            # Target should not exist in dry-run
            self.assertFalse(path.exists())

    def test_invalid_skill_no_skill_md(self):
        """Test that directory without SKILL.md is rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_dir = Path(tmpdir) / "invalid-skill"
            invalid_dir.mkdir()
            (invalid_dir / "some_file.txt").write_text("test")
            
            target_dir = Path(tmpdir) / "skills"
            
            success, _ = install_skill(invalid_dir, target_dir=target_dir)
            self.assertFalse(success)


class TestZipSecurity(unittest.TestCase):
    """Test ZIP security validation"""

    def test_path_traversal_rejected(self):
        """Test that path traversal in ZIP is rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "malicious.zip"
            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()
            
            # Create ZIP with path traversal
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("../../../etc/passwd", "malicious content")
            
            with self.assertRaises(ValueError) as ctx:
                _safe_extract_zip(zip_path, target_dir)
            self.assertIn("Path traversal", str(ctx.exception))

    def test_absolute_path_rejected(self):
        """Test that absolute paths in ZIP are rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "malicious.zip"
            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()
            
            # Create ZIP with absolute path
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("/etc/passwd", "malicious content")
            
            with self.assertRaises(ValueError) as ctx:
                _safe_extract_zip(zip_path, target_dir)
            self.assertIn("Absolute path", str(ctx.exception))


class TestCreateBackup(unittest.TestCase):
    """Test backup creation"""

    def test_backup_creates_timestamped_directory(self):
        """Test backup creates directory with timestamp"""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir) / "test-skill"
            target_path.mkdir()
            (target_path / "SKILL.md").write_text("test")
            
            backup_path = _create_backup(target_path)
            
            self.assertTrue(backup_path.exists())
            self.assertFalse(target_path.exists())
            self.assertTrue(backup_path.name.startswith("test-skill-backup-"))
            self.assertTrue((backup_path / "SKILL.md").exists())


class TestInstallSkillCLI(unittest.TestCase):
    """Test install_skill CLI"""

    def test_cli_help(self):
        """Test that skill-seekers install --help works"""
        import subprocess
        
        try:
            result = subprocess.run(
                ['skill-seekers', 'install', '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.assertIn(result.returncode, [0, 2])
            output = result.stdout + result.stderr
            self.assertTrue('install' in output.lower() or 'source' in output.lower())
        except FileNotFoundError:
            self.skipTest("skill-seekers command not installed")


if __name__ == '__main__':
    unittest.main()
