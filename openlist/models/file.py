"""
文件系统相关的 Pydantic 模型
"""
from datetime import datetime
from enum import IntEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class FileType(IntEnum):
    """文件类型枚举"""
    UNKNOWN = 0
    FOLDER = 1
    VIDEO = 2
    AUDIO = 3
    TEXT = 4
    IMAGE = 5


class HashInfo(BaseModel):
    """文件哈希信息"""
    md5: str | None = Field(default=None, description="MD5 哈希值")
    sha1: str | None = Field(default=None, description="SHA1 哈希值")
    sha256: str | None = Field(default=None, description="SHA256 哈希值")
    
    model_config = {"extra": "allow"}


class StorageInfo(BaseModel):
    """存储详情"""
    driver_name: str = Field(..., description="存储驱动名称")
    total_space: int = Field(..., description="总存储空间 (字节)")
    free_space: int = Field(..., description="可用存储空间 (字节)")
    
    @property
    def used_space(self) -> int:
        """已使用空间 (字节)"""
        return self.total_space - self.free_space
    
    @property
    def usage_percent(self) -> float:
        """使用率百分比 (0-100)"""
        if self.total_space == 0:
            return 0.0
        return (self.used_space / self.total_space) * 100


class FileInfo(BaseModel):
    """
    文件或目录信息
    
    表示远程文件系统中的一个文件或目录对象。
    """
    name: str = Field(..., description="文件或目录名称")
    path: str = Field(default="", description="完整路径")
    size: int = Field(default=0, description="文件大小 (字节)，目录为 0")
    is_dir: bool = Field(..., description="是否为目录")
    modified: datetime = Field(..., description="最后修改时间")
    created: datetime = Field(..., description="创建时间")
    
    # 可选字段
    id: str = Field(default="", description="对象 ID")
    sign: str = Field(default="", description="下载认证签名")
    thumb: str = Field(default="", description="缩略图 URL")
    type: FileType = Field(default=FileType.UNKNOWN, description="文件类型")
    hash_info: HashInfo | None = Field(default=None, description="哈希信息")
    storage_info: StorageInfo | None = Field(default=None, description="存储详情")
    
    # 原始哈希信息字符串 (用于兼容)
    hashinfo: str | None = Field(default=None, exclude=True)
    
    # 原始挂载详情 (用于兼容)
    mount_details: dict | None = Field(default=None, exclude=True)
    
    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        """将整数转换为 FileType 枚举"""
        if isinstance(v, int):
            try:
                return FileType(v)
            except ValueError:
                return FileType.UNKNOWN
        return v
    
    def model_post_init(self, __context) -> None:
        """初始化后处理"""
        # 解析 hashinfo 字符串为 HashInfo 对象
        if self.hashinfo and not self.hash_info:
            import json
            try:
                data = json.loads(self.hashinfo)
                if isinstance(data, dict):
                    object.__setattr__(self, "hash_info", HashInfo(**data))
            except (json.JSONDecodeError, TypeError):
                pass
        
        # 解析 mount_details 为 StorageInfo 对象
        if self.mount_details and not self.storage_info:
            try:
                object.__setattr__(self, "storage_info", StorageInfo(**self.mount_details))
            except (TypeError, ValueError):
                pass
    
    @property
    def suffix(self) -> str:
        """文件扩展名 (包含点号)"""
        if "." in self.name:
            return "." + self.name.rsplit(".", 1)[-1]
        return ""
    
    @property
    def stem(self) -> str:
        """不含扩展名的文件名"""
        if "." in self.name:
            return self.name.rsplit(".", 1)[0]
        return self.name


class DirectoryListing(BaseModel):
    """
    目录列表结果
    
    包含目录下的文件列表及相关元信息。
    """
    items: list[FileInfo] = Field(default_factory=list, description="文件/目录列表")
    total: int = Field(default=0, description="总项目数")
    readme: str = Field(default="", description="README 内容")
    header: str = Field(default="", description="头部内容")
    has_write_permission: bool = Field(default=False, description="是否有写权限")
    provider: str = Field(default="", description="存储提供商名称")


class UploadOptions(BaseModel):
    """
    上传选项配置
    """
    overwrite: bool = Field(default=False, description="是否覆盖已存在的文件")
    password: str | None = Field(default=None, description="受保护目录的访问密码")
    as_task: bool = Field(default=False, description="是否作为后台任务上传")
    last_modified: int | None = Field(default=None, description="最后修改时间 (秒时间戳)")


class RenameItem(BaseModel):
    """
    批量重命名项
    """
    src_name: str = Field(..., description="源文件名")
    new_name: str = Field(..., description="新文件名")
    
    @classmethod
    def from_tuple(cls, item: tuple[str, str]) -> "RenameItem":
        """从元组创建"""
        return cls(src_name=item[0], new_name=item[1])


class ListOptions(BaseModel):
    """
    目录列表选项
    """
    password: str | None = Field(default=None, description="受保护路径的访问密码")
    refresh: bool = Field(default=False, description="是否强制刷新缓存")
    page: Annotated[int, Field(ge=1)] = Field(default=1, description="页码 (从 1 开始)")
    per_page: Annotated[int, Field(ge=1, le=100)] = Field(
        default=30, description="每页数量 (1-100)"
    )
