#!/usr/bin/env python3
"""
Local Skill Installer

Install a skill directory or .zip file into Claude's local skills directory.
Supports cross-platform directory detection, conflict handling, and atomic installs.

Usage:
    skill-seekers install <skill_dir_or_zip> [--target <dir>] [--overwrite] [--backup] [--dry-run]

Examples:
    skill-seekers install output/react/
    skill-seekers install output/react.zip --overwrite
    skill-seekers install output/react/ --backup --target ~/.claude/skills
"""

import os
import sys
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


def get_claude_skills_dir() -> Path:
    """
    获取 Claude skills 目录，支持跨平台。
    
    优先级：
    1. 环境变量 CLAUDE_SKILLS_DIR
    2. 平台默认路径
    
    Returns:
        Path: Claude skills 目录路径
    """
    # 1. 环境变量优先
    if env_dir := os.environ.get("CLAUDE_SKILLS_DIR"):
        return Path(env_dir).expanduser().resolve()
    
    # 2. 平台默认
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            claude_dir = Path(appdata) / "Claude" / "skills"
            if claude_dir.exists():
                return claude_dir
        return (Path.home() / ".claude" / "skills").resolve()
    
    elif sys.platform == "darwin":
        app_support = Path.home() / "Library" / "Application Support" / "Claude" / "skills"
        if app_support.exists():
            return app_support.resolve()
        return (Path.home() / ".claude" / "skills").resolve()
    
    else:  # Linux
        xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        xdg_dir = Path(xdg) / "Claude" / "skills"
        if xdg_dir.exists():
            return xdg_dir.resolve()
        return (Path.home() / ".claude" / "skills").resolve()


def _validate_flags(overwrite: bool, backup: bool) -> None:
    """验证冲突处理标志的互斥性"""
    if overwrite and backup:
        raise ValueError("--overwrite and --backup are mutually exclusive")


def _validate_skill_structure(skill_path: Path) -> None:
    """
    验证技能目录结构完整性。
    
    Args:
        skill_path: 技能目录路径
        
    Raises:
        ValueError: 如果技能结构无效
    """
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        raise ValueError(f"Invalid skill: SKILL.md not found in {skill_path}")


def _safe_extract_zip(zip_path: Path, target_dir: Path) -> Path:
    """
    安全解压 ZIP，防止路径穿越和危险条目。
    
    Args:
        zip_path: ZIP 文件路径
        target_dir: 解压目标目录
        
    Returns:
        Path: 解压后的技能目录路径
        
    Raises:
        ValueError: 如果检测到安全问题
    """
    target_dir = target_dir.resolve()
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # 检测 ZIP 结构：是否有顶层目录
        names = zf.namelist()
        if not names:
            raise ValueError("Empty ZIP file")
        
        # 检查是否所有文件都在同一个顶层目录下
        top_dirs = set()
        for name in names:
            parts = name.split('/')
            if parts[0]:
                top_dirs.add(parts[0])
        
        has_single_top_dir = len(top_dirs) == 1 and not any(
            name == list(top_dirs)[0] for name in names
        )
        
        for member in zf.infolist():
            # 拒绝绝对路径
            if member.filename.startswith('/') or member.filename.startswith('\\'):
                raise ValueError(f"Absolute path not allowed: {member.filename}")
            
            # 拒绝路径穿越
            resolved = (target_dir / member.filename).resolve()
            if not str(resolved).startswith(str(target_dir)):
                raise ValueError(f"Path traversal detected: {member.filename}")
            
            # 跳过符号链接（external_attr 高位字节 0xa 表示符号链接）
            if member.external_attr >> 28 == 0xa:
                print(f"⚠️  Skipping symlink: {member.filename}")
                continue
            
            zf.extract(member, target_dir)
    
    # 返回实际的技能目录路径
    if has_single_top_dir:
        return target_dir / list(top_dirs)[0]
    else:
        return target_dir


def _create_backup(target_path: Path) -> Path:
    """
    创建目标目录的备份。
    
    Args:
        target_path: 要备份的目录路径
        
    Returns:
        Path: 备份目录路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{target_path.name}-backup-{timestamp}"
    backup_path = target_path.parent / backup_name
    
    shutil.move(str(target_path), str(backup_path))
    print(f"📦 Backed up existing skill to: {backup_path}")
    
    return backup_path


def _remove_path(path: Path) -> None:
    """安全删除路径（文件或目录）"""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def install_skill(
    source: Path,
    target_dir: Optional[Path] = None,
    overwrite: bool = False,
    backup: bool = False,
    dry_run: bool = False,
) -> Tuple[bool, Optional[Path]]:
    """
    安装技能到 Claude skills 目录。
    
    Args:
        source: 技能目录或 .zip 文件路径
        target_dir: 目标目录（默认自动检测）
        overwrite: 覆盖已存在的同名技能
        backup: 备份已存在的同名技能
        dry_run: 预览模式，不实际执行
    
    Returns:
        (success, installed_path): 成功标志和安装路径
    """
    # 验证互斥标志
    _validate_flags(overwrite, backup)
    
    source = Path(source).resolve()
    if not source.exists():
        print(f"❌ Error: Source not found: {source}")
        return False, None
    
    # 确定目标目录
    if target_dir is None:
        target_dir = get_claude_skills_dir()
    else:
        target_dir = Path(target_dir).expanduser().resolve()
    
    # 确定技能名称
    if source.suffix == '.zip':
        skill_name = source.stem
    else:
        skill_name = source.name
    
    final_path = target_dir / skill_name
    
    # Dry run 模式
    if dry_run:
        print(f"🔍 Dry run mode - no changes will be made")
        print(f"   Source: {source}")
        print(f"   Target: {final_path}")
        
        if final_path.exists():
            if overwrite:
                print(f"   Action: Would overwrite existing skill")
            elif backup:
                print(f"   Action: Would backup existing skill")
            else:
                print(f"   ⚠️  Conflict: Target already exists")
                return False, final_path
        else:
            print(f"   Action: Would install new skill")
        
        return True, final_path
    
    # 确保目标目录存在
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查目标是否已存在
    backup_path: Optional[Path] = None
    if final_path.exists():
        if overwrite:
            print(f"🔄 Overwriting existing skill: {skill_name}")
            _remove_path(final_path)
        elif backup:
            backup_path = _create_backup(final_path)
        else:
            print(f"❌ Error: Skill already exists: {final_path}")
            print(f"   Use --overwrite to replace or --backup to keep a copy")
            return False, None
    
    # 原子性安装：先复制到临时目录，再移动到目标
    try:
        with tempfile.TemporaryDirectory(dir=target_dir) as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            if source.suffix == '.zip':
                # 解压 ZIP
                print(f"📦 Extracting: {source.name}")
                extracted_path = _safe_extract_zip(source, tmp_path)
                skill_tmp_path = extracted_path
            else:
                # 复制目录
                print(f"📁 Copying: {source.name}")
                skill_tmp_path = tmp_path / source.name
                shutil.copytree(source, skill_tmp_path)
            
            # 验证技能结构
            _validate_skill_structure(skill_tmp_path)
            
            # 原子移动到最终位置
            shutil.move(str(skill_tmp_path), str(final_path))
        
        print(f"✅ Skill installed: {final_path}")
        return True, final_path
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        
        # 回滚：恢复备份
        if backup_path and backup_path.exists():
            print(f"🔄 Restoring backup...")
            if final_path.exists():
                _remove_path(final_path)
            shutil.move(str(backup_path), str(final_path))
            print(f"✅ Backup restored")
        
        return False, None


def main() -> int:
    """CLI entry point for install_skill."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Install a skill into Claude's local skills directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install from directory
  skill-seekers install output/react/

  # Install from ZIP
  skill-seekers install output/react.zip

  # Overwrite existing
  skill-seekers install output/react/ --overwrite

  # Backup existing and install
  skill-seekers install output/react/ --backup

  # Preview without making changes
  skill-seekers install output/react/ --dry-run

  # Install to custom location
  skill-seekers install output/react/ --target ~/.claude/skills
        """
    )
    
    parser.add_argument(
        'source',
        help='Skill directory or .zip file to install'
    )
    
    parser.add_argument(
        '--target',
        help='Override Claude skills directory (default: auto-detect)'
    )
    
    conflict_group = parser.add_mutually_exclusive_group()
    conflict_group.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing skill with same name'
    )
    conflict_group.add_argument(
        '--backup',
        action='store_true',
        help='Backup existing skill before installing'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview installation without making changes'
    )
    
    args = parser.parse_args()
    
    target_dir = Path(args.target).expanduser() if args.target else None
    
    success, installed_path = install_skill(
        Path(args.source),
        target_dir=target_dir,
        overwrite=args.overwrite,
        backup=args.backup,
        dry_run=args.dry_run,
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
