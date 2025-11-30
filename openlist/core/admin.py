import httpx
from ..exceptions import BadResponse, AuthenticationFailed, UnexceptedResponseCode
from ..context import Context
from ..data_types import UserInfo
from ..utils import decode_token


class User:
    def __init__(self, context: Context):
        self.context = context

    def me(self) -> UserInfo:
        """
        获取当前用户信息

        GET /api/me
        """
        response: httpx.Response = self.context.httpx_client.get(
            "/api/me",
            headers={"Authorization": self.context.auth_token},
        )
        if response.status_code == 401:
            raise AuthenticationFailed("Unauthorized")
        elif response.status_code != 200:
            raise UnexceptedResponseCode(response.status_code, response.json().get("message", "Unknown error"))
        
        try:
            response_data: dict = response.json()
            if response_data["code"] != 200:
                raise BadResponse(response_data.get("message", "Unknown error"))
            return UserInfo(**response_data["data"])
        except (KeyError, TypeError):
            raise BadResponse(response_data.get("message", "Unknown error"))

    def update(self, username: str=None, password: str=None, sso_id: str=None):
        """
        更新用户信息；会使JWT失效，需要重新登录
        """
        payload = {
            "username": username or decode_token(self.context.auth_token).username,
            "password": password or "",
            "sso_id": sso_id or "",
        }
        response: httpx.Response = self.context.httpx_client.post(
            "/api/me/update",
            json=payload,
            headers={"Authorization": self.context.auth_token},
        )
        if response.status_code == 401:
            raise AuthenticationFailed("Unauthorized")
        elif response.status_code != 200:
            raise UnexceptedResponseCode(response.status_code, response.json().get("message", "Unknown error"))
        elif response.json()["code"] != 200:
            raise BadResponse(response.json().get("message", "Unknown error"))

        return