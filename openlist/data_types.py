"""
数据类型定义

包含用户、认证相关的模型。
文件系统相关模型请使用 models.file 模块。
"""
from pydantic import BaseModel, Field


class SimpleLogin(BaseModel):
    """登录凭据"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    otp_key: str | None = Field(default=None, description="OTP密钥")


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


class SSHKey(BaseModel):
    """SSH密钥对象"""
    id: int
    name: str
    public_key: str
    created_at: str


class UserListResult(BaseModel):
    """用户列表分页响应"""
    content: list[UserInfo]
    total: int