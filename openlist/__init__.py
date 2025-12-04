import httpx
from .core.authentication import Authentication
from .core.admin import UserMe, MySSHKey
from .core.file import FileSystem
from .context import Context
from .data_types import SimpleLogin, RenameObject
import asyncio

__all__ = [
    "Client",
    "RenameObject",
]

class Client:
    """
    Client实例的入点（异步版本）
    
    ```python
    import asyncio
    
    async def main():
        client = Client("https://host")
        await client.login("test", "test")
        # 也支持
        # async with Client("https://host") as client:
        #     await client.login("test", "test")
        user_info = await client.user.me()
        await client.close()
    
    asyncio.run(main())
    ```
    """
    def __init__(self, base_url: str):
        self.context: Context = Context(base_url=base_url,
                                        auth_token=None,
                                        httpx_client=httpx.AsyncClient(base_url=base_url, follow_redirects=True))
        self.auth = Authentication(self.context)
        self.user = UserMe(self.context)
        self.fs = FileSystem(self.context)

    def get_token(self) -> str:
        return self.context.auth_token
        
    async def login(self, username: str, password: str, otp_key: str = None) -> "Client":
        """
        登录
        
        Args:
            username: 用户名
            password: 密码
            otp_key: OTP 密钥
        
        Returns:
            Client: 客户端实例
        """
        login_elements: SimpleLogin = SimpleLogin(username=username, password=password, otp_key=otp_key)
        await self.auth.login(**login_elements.model_dump())
        return self

    async def logout(self) -> "Client":
        await self.auth.logout()
        self.context.auth_token = None
        return self

    async def close(self) -> None:
        """关闭 HTTP 客户端连接"""
        await self.logout()
        await self.context.httpx_client.aclose()

    async def __aenter__(self) -> "Client":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器退出"""
        await self.close()

    def __del__(self) -> None:
        """析构函数"""
        asyncio.create_task(self.close())
