"""跨平台路径和环境处理 - Linus式简化，消除Windows/Unix特殊情况."""

import os
import sys
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """获取项目根目录，跨平台统一处理."""
    # 从当前文件向上查找包含pyproject.toml的目录
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    
    # 如果找不到，返回当前工作目录
    return Path.cwd()


def normalize_path(path_str: str) -> Path:
    """标准化路径，自动处理Windows/Unix差异."""
    return Path(path_str).resolve()


def is_windows() -> bool:
    """检查是否为Windows平台."""
    return sys.platform.startswith('win')


def get_python_executable() -> str:
    """获取Python可执行文件路径."""
    return sys.executable


def setup_cross_platform():
    """设置跨平台兼容性，在导入时执行."""
    if is_windows():
        # Windows特殊处理：确保Path类正确处理
        import pathlib
        # 只在必要时才做这个hack，避免在Unix系统上破坏东西
        if not hasattr(pathlib, '_original_posix_path'):
            pathlib._original_posix_path = pathlib.PosixPath
            try:
                pathlib.PosixPath = pathlib.WindowsPath
            except AttributeError:
                # 如果已经是Windows系统，这个赋值可能会失败，忽略即可
                pass


# 自动执行跨平台设置
setup_cross_platform()