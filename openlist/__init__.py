import httpx
from .core.authentication import Authentication
from .context import Context
from .data_types import SimpleLogin

class Server:
    """
    Client实例的入点
    
    ```
    client = Server("https://host")
    client.login("test", "test")
    # 也支持
    # client = Server("https://host").login("test", "test")
    client.user.get_totp()
    client.file.get_file_list()
    ```
    """
    def __init__(self, base_url: str):
        self.context: Context = Context(base_url=base_url,
                                        auth_token=None,
                                        httpx_client=httpx.Client(base_url=base_url, follow_redirects=True)
                                    )
        self.auth = Authentication(self.context)
        
    def login(self, username: str, password: str, otp_key: str = None) -> "Server":
        login_elements: SimpleLogin = SimpleLogin(username=username, password=password, otp_key=otp_key)
        self.auth.login(**login_elements.model_dump())
        return self

    def logout(self) -> "Server":
        self.auth.logout()
        self.context.auth_token = None
        return self

    def __del__(self) -> None:
        self.logout()
        self.context.httpx_client.close()