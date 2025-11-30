from pydantic import BaseModel, Field
from typing import Optional


class SimpleLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    otp_key: Optional[str] = Field(None, description="OTP密钥")


class UserInfo(BaseModel):
    """用户信息模型"""
    id: int
    username: str
    password: str
    base_path: str
    role: int
    disabled: bool
    permission: int
    sso_id: str
    otp: bool


class TokenPayload(BaseModel):
    """JWT Token 载荷模型"""
    exp: int
    iat: int
    nbf: int
    username: str
    pwd_ts: int

