"""
认证相关的 API 服务
"""
import time
from hashlib import sha256

import httpx
import pyotp

from .base import BaseService
from ..context import Context
from ..exceptions import AuthenticationFailed, UnexceptedResponseCode, BadResponse
from ..utils import decode_token


class Authentication(BaseService):
    """用户认证服务"""

    async def login(self, username: str, password: str, otp_key: str = None) -> None:
        """
        登录并将 token 存入 context
        
        Args:
            username: 用户名
            password: 密码
            otp_key: OTP 密钥（可选）
        """
        STATIC_HASH_SALT = "https://github.com/alist-org/alist"
        combined = f"{password}-{STATIC_HASH_SALT}"
        hashed_password = sha256(combined.encode()).hexdigest()
        
        otp = pyotp.TOTP(otp_key).now() if otp_key else None

        payload = {
            "username": username,
            "password": hashed_password,
            "otp_code": otp,
        }

        # login 接口特殊处理：不需要认证头，403 表示认证失败
        response: httpx.Response = await self.context.httpx_client.post(
            "/api/auth/login/hash",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        
        if response.status_code == 403:
            raise AuthenticationFailed(response.json().get("message", "Unknown error"))
        elif response.status_code != 200:
            raise UnexceptedResponseCode(
                response.status_code, 
                response.json().get("message", "Unknown error")
            )
        
        try:
            self.context.auth_token = response.json()["data"]["token"]
        except (KeyError, TypeError):
            raise BadResponse(response.json().get("message", "Unknown error"))

    async def logout(self) -> None:
        """
        登出，使 JWT 失效
        """
        if not self.context.auth_token:
            return

        token = decode_token(self.context.auth_token)
        if time.time() > token.exp:
            return
        
        await self._get("/api/auth/logout")
