class BadResponse(Exception):
    def __init__(self, message: str):
        super().__init__(f"Bad response: {message}")

class AuthenticationFailed(Exception):
    def __init__(self, message: str):
        super().__init__(f"Authentication failed: {message}")

class UnexceptedResponseCode(Exception):
    def __init__(self, response_code: int, message: str=""):
        super().__init__(f"Unexpected response code: {response_code} {message}")