import httpx
import pyotp
import time
from hashlib import sha256
from ..exceptions import BadResponse, AuthenticationFailed, UnexceptedResponseCode
from ..context import Context
from ..utils import decode_token


class Authentication:
    def __init__(self, context: Context):
        self.context = context

    async def login(self, username: str, password: str, otp_key: str = None) -> None:
        """
        登录并将 token 存入 context
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

        response: httpx.Response = await self.context.httpx_client.post(
            "/api/auth/login/hash",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        
        if response.status_code == 403:
            raise AuthenticationFailed(response.json().get("message", "Unknown error"))
        elif response.status_code != 200:
            raise UnexceptedResponseCode(response.status_code, response.json().get("message", "Unknown error"))
        
        try:
            self.context.auth_token = response.json()["data"]["token"]
        except (KeyError, TypeError):
            raise BadResponse(response.json().get("message", "Unknown error"))

    async def logout(self) -> None:
        """
        登出，使JWT失效
        """
        if not self.context.auth_token:
            return

        token = decode_token(self.context.auth_token)
        if time.time() > token.exp:
            return
            
        response: httpx.Response = await self.context.httpx_client.get(
            "/api/auth/logout",
            headers={"Authorization": self.context.auth_token},
        )

        if response.status_code == 401:
            raise AuthenticationFailed("Unauthorized")
        elif response.status_code != 200:
            raise UnexceptedResponseCode(response.status_code, response.json().get("message", "Unknown error"))
