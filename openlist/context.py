from dataclasses import dataclass
from typing import Callable, Union
import httpx

@dataclass
class Context:
    base_url: str               # 服务器地址
    auth_token: str             # 认证令牌
    httpx_client: Union[httpx.AsyncClient, httpx.Client]  # HTTP客户端（默认异步）
    auth_method: Callable = None    # 认证方法
    auth_params: dict = None        # 认证参数
