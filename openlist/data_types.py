from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


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

class SSHKey(BaseModel):
    """列出的SSH密钥对象"""
    id: int
    name: str
    public_key: str
    created_at: str


class UserListResult(BaseModel):
    """用户列表分页响应"""
    content: list["UserInfo"]
    total: int


class StorageDetails(BaseModel):
    """存储详情"""
    driver_name: str = Field(..., description="存储驱动名称")
    total_space: int = Field(..., description="总存储空间（字节）")
    free_space: int = Field(..., description="可用存储空间（字节）")


class FsObject(BaseModel):
    """文件系统对象（文件或目录）"""
    id: str = Field(default="", description="对象 ID（本地存储可能为空）")
    path: str = Field(..., description="完整系统路径")
    name: str = Field(..., description="文件或目录名称")
    size: int = Field(default=0, description="文件大小（字节），目录为 0")
    is_dir: bool = Field(..., description="是否为目录")
    modified: datetime = Field(..., description="最后修改时间")
    created: datetime = Field(..., description="创建时间")
    sign: str = Field(default="", description="下载认证签名")
    thumb: str = Field(default="", description="缩略图 URL（如果有）")
    type: int = Field(
        default=0, 
        description="文件类型：0=未知, 1=文件夹, 2=视频, 3=音频, 4=文本, 5=图片"
    )
    hashinfo: Optional[str] = Field(default=None, description="哈希信息（JSON 字符串或 null）")
    hash_info: Optional[dict[str, str]] = Field(default=None, description="解析后的哈希信息")
    mount_details: Optional[StorageDetails] = Field(default=None, description="挂载存储详情")


class FsListResult(BaseModel):
    """文件列表响应"""
    content: list[FsObject] = Field(..., description="文件/目录列表")
    total: int = Field(..., description="总项目数")
    readme: str = Field(default="", description="README 内容（如果存在）")
    header: str = Field(default="", description="头部内容")
    write: bool = Field(default=False, description="当前用户是否有写权限")
    provider: str = Field(default="", description="存储提供商名称")


class RenameObject(BaseModel):
    """批量重命名对象"""
    src_name: str = Field(..., description="源文件名")
    new_name: str = Field(..., description="新文件名")