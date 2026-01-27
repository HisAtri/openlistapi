"""
文件系统 API 传输层

负责纯粹的 HTTP 通信
"""
import json
from typing import Any, AsyncIterator, Iterator
from urllib.parse import quote

import httpx

from ...context import Context
from ...exceptions import (
    AuthenticationError,
    FileExistsError,
    FileNotFoundError,
    FileSystemError,
    NetworkError,
    PermissionDeniedError,
    UnexpectedResponseError,
)


def _map_error_to_exception(
    code: int,
    message: str,
    path: str | None = None,
) -> Exception:
    """
    将 API 错误码/消息映射为对应的异常类型
    """
    msg_lower = message.lower()
    
    # 文件不存在
    if code == 404 or "not found" in msg_lower or "not exist" in msg_lower:
        return FileNotFoundError(path or "", message)
    
    # 文件已存在
    if "exist" in msg_lower or "already" in msg_lower:
        return FileExistsError(path or "", message)
    
    # 权限不足
    if code in (401, 403) or "permission" in msg_lower or "denied" in msg_lower:
        return PermissionDeniedError(path, message)
    
    # 认证失败
    if "auth" in msg_lower or "unauthorized" in msg_lower:
        return AuthenticationError(message)
    
    # 通用文件系统错误
    return FileSystemError(message, path)


async def _async_iter_from_sync(sync_iter: Iterator[bytes]) -> AsyncIterator[bytes]:
    """将同步迭代器转换为异步迭代器"""
    for chunk in sync_iter:
        yield chunk


class FileTransport:
    """
    文件系统 API 传输层
    
    职责:
    - 执行 HTTP 请求
    - 处理响应状态码
    - 将错误映射为异常
    - 返回原始响应数据 (dict)
    """
    
    def __init__(self, context: Context):
        self._context = context
    
    @property
    def _client(self) -> httpx.AsyncClient:
        return self._context.httpx_client
    
    @property
    def _auth_token(self) -> str:
        return self._context.auth_token
    
    def _get_headers(self) -> dict[str, str]:
        """获取带认证的请求头"""
        headers = {}
        if self._auth_token:
            headers["Authorization"] = self._auth_token
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_data: dict | None = None,
        params: dict | None = None,
        path_hint: str | None = None,
    ) -> dict[str, Any]:
        """
        执行请求并处理响应
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            json_data: JSON 请求体
            params: URL 查询参数
            path_hint: 用于错误消息的路径提示
            
        Returns:
            响应的 data 字段内容
            
        Raises:
            对应的异常类型
        """
        headers = self._get_headers()
        
        request_kwargs: dict[str, Any] = {"headers": headers}
        if json_data is not None:
            request_kwargs["json"] = json_data
        if params is not None:
            request_kwargs["params"] = params
        
        try:
            http_method = getattr(self._client, method.lower())
            response: httpx.Response = await http_method(endpoint, **request_kwargs)
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {e}")
        
        # 处理 HTTP 错误状态码
        if response.status_code == 401:
            raise AuthenticationError("Unauthorized")
        elif response.status_code == 403:
            try:
                msg = response.json().get("message", "Forbidden")
            except json.JSONDecodeError:
                msg = "Forbidden"
            raise PermissionDeniedError(path_hint, msg)
        elif response.status_code == 404:
            try:
                msg = response.json().get("message", "Not Found")
            except json.JSONDecodeError:
                msg = "Not Found"
            raise FileNotFoundError(path_hint or "", msg)
        elif response.status_code not in (200, 201):
            try:
                msg = response.json().get("message", "Unknown error")
            except json.JSONDecodeError:
                msg = response.text
            raise UnexpectedResponseError(response.status_code, msg)
        
        # 解析响应
        try:
            result = response.json()
        except json.JSONDecodeError:
            raise NetworkError("Invalid JSON response")
        
        # 检查业务状态码
        code = result.get("code", 0)
        if code != 200:
            message = result.get("message", "Unknown error")
            raise _map_error_to_exception(code, message, path_hint)
        
        return result.get("data", {})
    
    async def _post(
        self,
        endpoint: str,
        json_data: dict | None = None,
        path_hint: str | None = None,
    ) -> dict[str, Any]:
        """POST 请求"""
        return await self._request("POST", endpoint, json_data=json_data, path_hint=path_hint)
    
    async def _get(
        self,
        endpoint: str,
        params: dict | None = None,
        path_hint: str | None = None,
    ) -> dict[str, Any]:
        """GET 请求"""
        return await self._request("GET", endpoint, params=params, path_hint=path_hint)
    
    # =========================================================================
    # 文件系统 API 端点
    # =========================================================================
    
    async def list_directory(
        self,
        path: str,
        *,
        password: str | None = None,
        refresh: bool = False,
        page: int = 1,
        per_page: int = 30,
    ) -> dict[str, Any]:
        """列出目录内容"""
        payload = {
            "path": path,
            "refresh": refresh,
            "page": page,
            "per_page": per_page,
        }
        if password is not None:
            payload["password"] = password
        
        return await self._post("/api/fs/list", payload, path_hint=path)
    
    async def get_info(
        self,
        path: str,
        *,
        password: str | None = None,
    ) -> dict[str, Any]:
        """获取文件/目录信息"""
        payload = {"path": path}
        if password is not None:
            payload["password"] = password
        
        return await self._post("/api/fs/get", payload, path_hint=path)
    
    async def remove(
        self,
        dir_path: str,
        names: list[str],
    ) -> None:
        """删除文件或目录"""
        payload = {
            "dir": dir_path,
            "names": names,
        }
        await self._post("/api/fs/remove", payload, path_hint=dir_path)
    
    async def rename(
        self,
        path: str,
        new_name: str,
    ) -> None:
        """重命名文件或目录"""
        payload = {
            "path": path,
            "name": new_name,
        }
        await self._post("/api/fs/rename", payload, path_hint=path)
    
    async def batch_rename(
        self,
        dir_path: str,
        rename_objects: list[dict[str, str]],
    ) -> None:
        """批量重命名"""
        payload = {
            "src_dir": dir_path,
            "rename_objects": rename_objects,
        }
        await self._post("/api/fs/batch_rename", payload, path_hint=dir_path)
    
    async def mkdir(
        self,
        path: str,
    ) -> None:
        """创建目录"""
        payload = {"path": path}
        await self._post("/api/fs/mkdir", payload, path_hint=path)
    
    async def copy(
        self,
        src_dir: str,
        dst_dir: str,
        names: list[str],
    ) -> None:
        """复制文件或目录"""
        payload = {
            "src_dir": src_dir,
            "dst_dir": dst_dir,
            "names": names,
        }
        await self._post("/api/fs/copy", payload, path_hint=src_dir)
    
    async def move(
        self,
        src_dir: str,
        dst_dir: str,
        names: list[str],
    ) -> None:
        """移动文件或目录"""
        payload = {
            "src_dir": src_dir,
            "dst_dir": dst_dir,
            "names": names,
        }
        await self._post("/api/fs/move", payload, path_hint=src_dir)
    
    async def recursive_move(
        self,
        src_dir: str,
        dst_dir: str,
    ) -> None:
        """递归移动目录"""
        payload = {
            "src_dir": src_dir,
            "dst_dir": dst_dir,
        }
        await self._post("/api/fs/recursive_move", payload, path_hint=src_dir)
    
    async def upload(
        self,
        path: str,
        content: bytes | AsyncIterator[bytes] | Iterator[bytes],
        *,
        last_modified: int | None = None,
        overwrite: bool = False,
        password: str | None = None,
        as_task: bool = False,
    ) -> None:
        """
        上传文件
        
        Args:
            path: 目标路径 (包含文件名)
            content: 文件内容 (bytes 或迭代器)
            last_modified: 最后修改时间戳 (秒)
            overwrite: 是否覆盖已存在的文件
            password: 受保护目录的密码
            as_task: 是否作为后台任务
        """
        headers = {
            "Content-Type": "application/octet-stream",
            "File-Path": quote(path, safe=""),
            "Authorization": self._auth_token,
        }
        
        if last_modified is not None:
            headers["Last-Modified"] = str(int(last_modified))
        if overwrite:
            headers["Overwrite"] = "true"
        if password is not None:
            headers["Password"] = password
        if as_task:
            headers["As-Task"] = "true"
        
        # 转换同步迭代器为异步
        upload_content: bytes | AsyncIterator[bytes]
        if isinstance(content, bytes):
            upload_content = content
        elif hasattr(content, "__anext__"):
            upload_content = content  # type: ignore
        elif hasattr(content, "__next__"):
            upload_content = _async_iter_from_sync(content)  # type: ignore
        elif hasattr(content, "__aiter__"):
            upload_content = content.__aiter__()  # type: ignore
        elif hasattr(content, "__iter__"):
            upload_content = _async_iter_from_sync(iter(content))  # type: ignore
        else:
            upload_content = content  # type: ignore
        
        try:
            response = await self._client.put(
                "/api/fs/put",
                content=upload_content,
                headers=headers,
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Upload failed: {e}")
        
        if response.status_code != 200:
            try:
                result = response.json()
                message = result.get("message", "Upload failed")
            except json.JSONDecodeError:
                message = response.text
            raise _map_error_to_exception(response.status_code, message, path)
        
        result = response.json()
        if result.get("code") != 200:
            message = result.get("message", "Upload failed")
            raise _map_error_to_exception(result.get("code", 0), message, path)
