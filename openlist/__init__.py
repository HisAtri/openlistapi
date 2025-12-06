import time
import httpx
import asyncio
import jwt
from .core.authentication import Authentication
from .core.admin import UserMe, MySSHKey
from .core.file import FileSystem
from .context import Context
from .data_types import SimpleLogin, RenameObject

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
    def __init__(self, base_url: str, auto_refresh: bool = True):
        self.context: Context = Context(base_url=base_url,
                                        auth_token=None,
                                        httpx_client=httpx.AsyncClient(base_url=base_url, follow_redirects=True))
        self.auth = Authentication(self.context)
        self.user = UserMe(self.context)
        self.fs = FileSystem(self.context)
        self._auto_refresh = auto_refresh
        self._refresh_task: asyncio.Task = None
        self._stop_refresh = asyncio.Event()

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
        # 存储 auth_method
        self.context.auth_method = self.auth.login
        self.context.auth_params = login_elements.model_dump()
        
        # 启动自动刷新任务
        if self._auto_refresh:
            self._start_auto_refresh()
        
        return self

    async def logout(self) -> "Client":
        # 停止自动刷新任务
        self._stop_auto_refresh()
        await self.auth.logout()
        self.context.auth_token = None
        return self

    async def close(self) -> None:
        """关闭 HTTP 客户端连接"""
        self._stop_auto_refresh()
        await self.logout()
        await self.context.httpx_client.aclose()

    def _start_auto_refresh(self) -> None:
        """启动自动刷新任务"""
        if self._refresh_task is None or self._refresh_task.done():
            self._stop_refresh.clear()
            self._refresh_task = asyncio.create_task(self._auto_refresh_loop())
    
    def _stop_auto_refresh(self) -> None:
        """停止自动刷新任务"""
        if self._refresh_task and not self._refresh_task.done():
            self._stop_refresh.set()
            self._refresh_task.cancel()
    
    async def _auto_refresh_loop(self,
                                 *,
                                 refresh_buffer: int=300,
                                 retry_interval: int=60,
                                ) -> None:
        """
        后台循环：自动刷新 token
        在 token 过期前提前刷新（默认提前 5 分钟）
        """
        while not self._stop_refresh.is_set():
            try:
                if not self.context.auth_token:
                    await asyncio.sleep(10)
                    continue
                
                # 解码 JWT 获取过期时间
                token_data = jwt.decode(
                    self.context.auth_token, 
                    options={"verify_signature": False}
                )
                jwt_expire = int(token_data.get("exp"))
                
                if not jwt_expire:
                    await asyncio.sleep(60)
                    continue

                current_time = int(time.time())
                time_until_expire: int = jwt_expire - current_time
                
                if time_until_expire <= refresh_buffer:
                    # Token 即将过期，重新登录刷新
                    if self.context.auth_method and self.context.auth_params:
                        await self.context.auth_method(**self.context.auth_params)
                    await asyncio.sleep(60)
                else:
                    sleep_time = time_until_expire - refresh_buffer
                    try:
                        await asyncio.wait_for(
                            self._stop_refresh.wait(), 
                            timeout=sleep_time
                        )
                    except asyncio.TimeoutError:
                        pass
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"自动刷新 token 时出错: {e}")
                await asyncio.sleep(60)


    async def __aenter__(self) -> "Client":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器退出"""
        await self.close()
