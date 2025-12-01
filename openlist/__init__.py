import httpx
from .core.authentication import Authentication
from .core.admin import User, MySSHKey, UserMe
from .context import Context
from .data_types import SimpleLogin

class Client:
    """
    Client实例的入点
    
    ```
    client = Client("https://host")
    client.login("test", "test")
    # 也支持
    # client = Client("https://host").login("test", "test")
    client.user.get_totp()
    client.file.get_file_list()
    ```
    """
    def __init__(self, base_url: str):
        self.context: Context = Context(base_url=base_url,
                                        auth_token=None,
                                        httpx_client=httpx.Client(base_url=base_url, follow_redirects=True))
        self.auth = Authentication(self.context)
        self.user = UserMe(self.context)

    def get_token(self) -> str:
        return self.context.auth_token
        
    def login(self, username: str, password: str, otp_key: str = None) -> "Client":
        login_elements: SimpleLogin = SimpleLogin(username=username, password=password, otp_key=otp_key)
        self.auth.login(**login_elements.model_dump())
        return self

    def logout(self) -> "Client":
        self.auth.logout()
        self.context.auth_token = None
        return self

    def __del__(self) -> None:
        self.logout()
        self.context.httpx_client.close()