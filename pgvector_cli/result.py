"""Unified result handling for pgvector CLI - Linus式数据结构简化."""

from typing import Any, Dict, Generic, Optional, TypeVar, Union

T = TypeVar('T')
E = TypeVar('E')


class Result(Generic[T, E]):
    """统一结果类型，消除90%的try/except特殊情况.
    
    Linus原则：用简单数据结构解决复杂问题，而非用复杂代码修补问题。
    """
    
    def __init__(self, success: bool, data: Optional[T] = None, error: Optional[E] = None):
        self._success = success
        self._data = data
        self._error = error
    
    @property
    def success(self) -> bool:
        return self._success
    
    @property
    def data(self) -> Optional[T]:
        return self._data
    
    @property
    def error(self) -> Optional[E]:
        return self._error
    
    def is_ok(self) -> bool:
        """检查是否成功."""
        return self._success
    
    def is_err(self) -> bool:
        """检查是否失败."""
        return not self._success
    
    def unwrap(self) -> T:
        """获取数据，失败时抛异常."""
        if not self._success:
            raise ValueError(f"Cannot unwrap failed result: {self._error}")
        return self._data
    
    def unwrap_or(self, default: T) -> T:
        """获取数据，失败时返回默认值."""
        return self._data if self._success else default
    
    @classmethod
    def ok(cls, data: T) -> 'Result[T, Any]':
        """创建成功结果."""
        return cls(True, data=data)
    
    @classmethod
    def err(cls, error: E) -> 'Result[Any, E]':
        """创建失败结果."""
        return cls(False, error=error)
    
    def to_mcp_dict(self) -> Dict[str, Any]:
        """转换为MCP标准返回格式."""
        if self._success:
            return {"success": True, "data": self._data}
        else:
            return {"success": False, "error": str(self._error)}


def safe_call(func, *args, **kwargs) -> Result[Any, str]:
    """安全调用函数，自动包装异常为Result."""
    try:
        result = func(*args, **kwargs)
        return Result.ok(result)
    except Exception as e:
        return Result.err(str(e))


# MCP专用的结果构造函数，让代码更简洁
def mcp_success(data: Any) -> Dict[str, Any]:
    """MCP成功响应."""
    return {"success": True, **data} if isinstance(data, dict) else {"success": True, "data": data}


def mcp_error(error: Union[str, Exception]) -> Dict[str, Any]:
    """MCP错误响应."""
    return {"success": False, "error": str(error)}