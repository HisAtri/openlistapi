import httpx
from .core.authentication import login



class Server:
    def __init__(self, base_url: str, auth_token: str = None):
        
        self.base_url: str = base_url
        self.httpx_client: httpx.Client = httpx.Client(base_url=base_url)
        self._auth_token: str = auth_token

    def login(self, username: str, password: str, otp_key: str = None) -> "Server":
        self._auth_token = login(self.httpx_client, username, password, otp_key)
        return self

        