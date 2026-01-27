"""
OpenList 异常
"""
from typing import Any


class OpenListError(Exception):
    """OpenList 所有异常的基类"""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        return self.message


# =============================================================================
# 网络和认证相关异常
# =============================================================================

class NetworkError(OpenListError):
    """网络通信错误"""
    
    def __init__(
        self, 
        message: str = "Network communication failed",
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        super().__init__(message, details)


class AuthenticationError(OpenListError):
    """认证失败"""
    
    def __init__(
        self, 
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details)


class UnexpectedResponseError(NetworkError):
    """非预期的响应状态码"""
    
    def __init__(
        self, 
        status_code: int,
        message: str = "",
        details: dict[str, Any] | None = None,
    ):
        msg = f"Unexpected response code: {status_code}"
        if message:
            msg = f"{msg} - {message}"
        super().__init__(msg, status_code, details)


# =============================================================================
# 文件系统相关异常
# =============================================================================

class FileSystemError(OpenListError):
    """文件系统操作错误基类"""
    
    def __init__(
        self, 
        message: str,
        path: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.path = path
        super().__init__(message, details)
    
    def __str__(self) -> str:
        if self.path:
            return f"{self.message}: '{self.path}'"
        return self.message


class FileNotFoundError(FileSystemError):
    """文件或目录不存在"""
    
    def __init__(
        self, 
        path: str,
        message: str = "File or directory not found",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, path, details)


class FileExistsError(FileSystemError):
    """文件或目录已存在"""
    
    def __init__(
        self, 
        path: str,
        message: str = "File or directory already exists",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, path, details)


class PermissionDeniedError(FileSystemError):
    """权限不足"""
    
    def __init__(
        self, 
        path: str | None = None,
        message: str = "Permission denied",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, path, details)


class NotADirectoryError(FileSystemError):
    """期望目录但不是目录"""
    
    def __init__(
        self, 
        path: str,
        message: str = "Not a directory",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, path, details)


class IsADirectoryError(FileSystemError):
    """期望文件但是目录"""
    
    def __init__(
        self, 
        path: str,
        message: str = "Is a directory",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, path, details)


class InvalidPathError(FileSystemError):
    """无效的路径格式"""
    
    def __init__(
        self, 
        path: str,
        message: str = "Invalid path format",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, path, details)


class OperationError(FileSystemError):
    """文件操作执行失败"""
    
    def __init__(
        self,
        operation: str,
        path: str | None = None,
        message: str = "Operation failed",
        details: dict[str, Any] | None = None,
    ):
        self.operation = operation
        full_message = f"{operation}: {message}"
        super().__init__(full_message, path, details)
