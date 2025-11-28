import httpx
import pyotp
from hashlib import sha256
from ..exceptions import BadResponse, AuthenticationFailed, UnexceptedResponseCode


# OpenList 默认的静态盐值
STATIC_HASH_SALT = "https://github.com/alist-org/alist"


def login(httpx_client: httpx.Client, username: str, password: str, otp_key: str = None) -> str:
    # 使用 OpenList 的 StaticHash 格式: SHA256(password + "-" + salt)
    combined = f"{password}-{STATIC_HASH_SALT}"
    hashed_password = sha256(combined.encode()).hexdigest()
    if otp_key:
        totp = pyotp.TOTP(otp_key)
        otp: str = totp.now()
    else:
        otp: str = None

    payload = {
        "username": username,
        "password": hashed_password,
        "otp_code": otp,
    }

    response: httpx.Response = httpx_client.post(
        "/api/auth/login/hash",
        json=payload,
        headers={
            "Content-Type": "application/json",
        },
    )
    if response.status_code == 403:
        raise AuthenticationFailed(response.json().get("message", "Unknown error"))
    elif response.status_code != 200:
        raise UnexceptedResponseCode(response.status_code, response.json().get("message", "Unknown error"))
    
    try:
        token: str = response.json()["data"]["token"]
    except KeyError:
        raise BadResponse(response.json().get("message", "Unknown error"))
    return token

    
