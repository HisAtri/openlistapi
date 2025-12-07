"""
服务基类，封装 context 和通用 HTTP 请求逻辑
"""
from abc import ABC
from typing import Optional, Any
import httpx

from ..context import Context
from ..exceptions import BadResponse, AuthenticationFailed, UnexceptedResponseCode, NotFound


class BaseService(ABC):
    """
    API 服务基类，封装 context 和通用请求逻辑
    
    所有需要访问 API 的服务类都应该继承此类
    """
    
    def __init__(self, context: Context):
        self.context = context
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        require_auth: bool = True,
        expected_codes: tuple[int, ...] = (200,),
    ) -> dict:
        """
        统一的异步请求方法，处理认证和错误
        
        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE 等)
            endpoint: API 端点路径
            json: 请求体数据
            params: URL 查询参数
            require_auth: 是否需要认证头
            expected_codes: 期望的 HTTP 状态码
            
        Returns:
            响应的 JSON 数据
            
        Raises:
            AuthenticationFailed: 认证失败 (401/403)
            UnexceptedResponseCode: 非预期的状态码
            BadResponse: API 返回的 code 不是 200
        """
        headers = {}
        if require_auth and self.context.auth_token:
            headers["Authorization"] = self.context.auth_token
        
        # 构建请求参数
        request_kwargs = {"headers": headers}
        if json is not None:
            request_kwargs["json"] = json
        if params is not None:
            request_kwargs["params"] = params
        
        # 执行请求
        http_method = getattr(self.context.httpx_client, method.lower())
        response: httpx.Response = await http_method(endpoint, **request_kwargs)
        
        # 处理 HTTP 状态码错误
        if response.status_code == 401:
            raise AuthenticationFailed("Unauthorized")
        elif response.status_code == 403:
            raise AuthenticationFailed(response.json().get("message", "Forbidden"))
        elif response.status_code == 404:
            raise NotFound(response.json().get("message", "Not Found"))
        elif response.status_code not in expected_codes:
            raise UnexceptedResponseCode(
                response.status_code,
                response.json().get("message", "Unknown error")
            )
        
        # 解析响应
        try:
            data = response.json()
        except Exception:
            raise BadResponse("Invalid JSON response")
        
        # 检查业务状态码
        if data.get("code") != 200:
            raise BadResponse(data.get("message", "Unknown error"))
        
        return data
    
    async def _get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        require_auth: bool = True,
    ) -> dict:
        return await self._request("GET", endpoint, params=params, require_auth=require_auth)
    
    async def _post(
        self,
        endpoint: str,
        json: Optional[dict] = None,
        require_auth: bool = True,
    ) -> dict:
        return await self._request("POST", endpoint, json=json, require_auth=require_auth)
