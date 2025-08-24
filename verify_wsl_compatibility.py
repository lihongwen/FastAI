#!/usr/bin/env python3
"""
WSL部署兼容性验证脚本
用于验证WSL环境与macOS环境的版本一致性
"""

import sys
import subprocess
from typing import Dict, Tuple, List

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Python < 3.8 兼容性
    from importlib_metadata import version, PackageNotFoundError

# 预期版本配置 (基于macOS环境)
EXPECTED_VERSIONS = {
    # 核心数据库和向量依赖
    'sqlalchemy': '2.0.43',
    'psycopg2-binary': '2.9.10', 
    'pgvector': '0.4.1',
    'python-dotenv': '1.1.1',
    
    # 数据模型和验证
    'pydantic': '2.11.7',
    'pydantic-settings': '2.10.1',
    
    # CLI和UI依赖
    'click': '8.2.1',
    'rich': '14.1.0',
    'tabulate': '0.9.0',
    
    # AI和嵌入服务
    'dashscope': '1.24.2',
    'openai': '1.101.0',
    'numpy': '2.3.2',
    
    # HTTP和网络
    'httpx': '0.28.1',
    'socksio': '1.0.0',
    
    # 文档处理依赖
    'pymupdf4llm': '0.0.27',
    'python-docx': '1.2.0',
    'openpyxl': '3.1.5',
    'python-pptx': '1.0.2',
    'pandas': '2.3.2',
    'chardet': '5.2.0',
    'langchain-text-splitters': '0.3.9',
    
    # 开发和测试依赖
    'pytest': '8.4.1',
    'pytest-cov': '6.2.1',
    'pytest-mock': '3.14.1',
    'ruff': '0.12.10',
    'mypy': '1.17.1',
}

EXPECTED_SYSTEM_VERSIONS = {
    'python': '3.13.4',
    'postgresql': '14.18',
    'pgvector_extension': '0.8.0',
}

def check_python_version() -> Tuple[bool, str]:
    """检查Python版本"""
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    expected = EXPECTED_SYSTEM_VERSIONS['python']
    return current_version == expected, f"Python {current_version} (expected {expected})"

def check_postgresql_version() -> Tuple[bool, str]:
    """检查PostgreSQL版本"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.strip()
            # 解析版本号，例如: "psql (PostgreSQL) 14.18"
            version_parts = version_line.split()
            if len(version_parts) >= 3:
                version = version_parts[2]
                expected = EXPECTED_SYSTEM_VERSIONS['postgresql']
                return version == expected, f"PostgreSQL {version} (expected {expected})"
        return False, "PostgreSQL version check failed"
    except Exception as e:
        return False, f"PostgreSQL check error: {e}"

def check_pgvector_extension() -> Tuple[bool, str]:
    """检查pgvector扩展版本"""
    try:
        # 使用默认的数据库连接
        cmd = ['psql', '-d', 'postgres', '-c', 
               "SELECT extversion FROM pg_extension WHERE extname = 'vector';", '-t']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            expected = EXPECTED_SYSTEM_VERSIONS['pgvector_extension']
            return version == expected, f"pgvector {version} (expected {expected})"
        return False, "pgvector extension check failed"
    except Exception as e:
        return False, f"pgvector check error: {e}"

def check_python_packages() -> List[Tuple[str, bool, str]]:
    """检查Python包版本"""
    results = []
    
    for package, expected_version in EXPECTED_VERSIONS.items():
        try:
            installed_version = version(package)
            is_match = installed_version == expected_version
            status = f"{package} {installed_version} (expected {expected_version})"
            results.append((package, is_match, status))
        except PackageNotFoundError:
            results.append((package, False, f"{package} NOT INSTALLED (expected {expected_version})"))
        except Exception as e:
            results.append((package, False, f"{package} check error: {e}"))
    
    return results

def main():
    """主验证函数"""
    print("=" * 70)
    print("WSL 部署兼容性验证")
    print("=" * 70)
    
    # 检查系统版本
    print("\n🔍 系统版本检查:")
    print("-" * 30)
    
    python_ok, python_msg = check_python_version()
    print(f"{'✅' if python_ok else '❌'} {python_msg}")
    
    pg_ok, pg_msg = check_postgresql_version()
    print(f"{'✅' if pg_ok else '❌'} {pg_msg}")
    
    pgvector_ok, pgvector_msg = check_pgvector_extension()
    print(f"{'✅' if pgvector_ok else '❌'} {pgvector_msg}")
    
    # 检查Python包版本
    print("\n📦 Python包版本检查:")
    print("-" * 30)
    
    package_results = check_python_packages()
    all_packages_ok = True
    
    for package, is_match, status in package_results:
        print(f"{'✅' if is_match else '❌'} {status}")
        if not is_match:
            all_packages_ok = False
    
    # 总结
    print("\n" + "=" * 70)
    print("验证总结:")
    print("=" * 70)
    
    system_ok = python_ok and pg_ok and pgvector_ok
    overall_ok = system_ok and all_packages_ok
    
    print(f"系统版本: {'✅ 全部匹配' if system_ok else '❌ 存在不匹配'}")
    print(f"Python包: {'✅ 全部匹配' if all_packages_ok else '❌ 存在不匹配'}")
    print(f"总体状态: {'✅ 环境完全兼容' if overall_ok else '❌ 需要修复版本问题'}")
    
    if not overall_ok:
        print("\n❗ 注意事项:")
        if not system_ok:
            print("- 请确保PostgreSQL和pgvector版本与macOS环境一致")
        if not all_packages_ok:
            print("- 请使用 'pip install -r requirements.txt' 安装正确版本的Python包")
        print("- 参考 WSL_DEPLOYMENT.md 获取详细部署指南")
    
    return 0 if overall_ok else 1

if __name__ == "__main__":
    sys.exit(main())