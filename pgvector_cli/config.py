"""Linus式统一配置管理 - 消除配置地狱，单一数据源."""

import os
from pathlib import Path
from typing import Optional

from .platform import get_project_root


class Settings:
    """统一配置类，处理所有环境变量和.env文件."""
    
    _instance: Optional['Settings'] = None
    
    def __new__(cls):
        # Singleton模式，确保配置只加载一次
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置，按优先级：环境变量 > .env文件 > 默认值."""
        # 尝试加载.env文件
        env_file = get_project_root() / ".env"
        if env_file.exists():
            self._load_env_file(env_file)
        
        # 核心数据库配置
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://lihongwen@localhost:5432/postgres"
        )
        
        # 应用配置
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # DashScope配置
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.dashscope_base_url = os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 清理配置
        self.soft_delete_retention_days = int(os.getenv("SOFT_DELETE_RETENTION_DAYS", "30"))
    
    def _load_env_file(self, env_file: Path):
        """手动加载.env文件，避免依赖python-dotenv."""
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key, value = key.strip(), value.strip()
                        # 只在环境变量不存在时才设置
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception:
            # 静默处理.env文件读取错误
            pass
    
    def is_valid(self) -> bool:
        """检查配置是否有效."""
        return bool(self.database_url)
    
    def mask_sensitive_data(self) -> dict:
        """返回脱敏后的配置，用于日志和调试."""
        return {
            "database_url": self._mask_url(self.database_url),
            "debug": self.debug,
            "dashscope_api_key": "***" if self.dashscope_api_key else "",
            "dashscope_base_url": self.dashscope_base_url,
            "soft_delete_retention_days": self.soft_delete_retention_days,
        }
    
    def _mask_url(self, url: str) -> str:
        """屏蔽URL中的密码."""
        if "@" in url and ":" in url.split("@")[0]:
            parts = url.split("://")
            if len(parts) == 2:
                protocol, rest = parts
                user_pass_host = rest.split("@")[0]
                if ":" in user_pass_host:
                    user = user_pass_host.split(":")[0]
                    return url.replace(user_pass_host, f"{user}:***")
        return url


# 全局实例
_settings = None


def get_settings() -> Settings:
    """获取全局配置实例."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
