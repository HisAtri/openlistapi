"""
RemotePath - 按 pathlib 风格
"""
from __future__ import annotations

import posixpath
from typing import TYPE_CHECKING, AsyncIterator, Iterator, Union

from ...models.file import FileInfo, UploadOptions

if TYPE_CHECKING:
    from .async_fs import AsyncFileSystem
    from .sync_fs import SyncFileSystem


class RemotePath:
    """
    远程路径对象 (类似 pathlib.Path)
    
    提供面向对象的文件操作接口。路径操作（如 parent、name）是纯本地计算，
    不涉及网络请求；文件操作（如 exists、mkdir）会触发 API 调用。
    
    支持异步和同步两种使用方式：
    - 使用 AsyncFileSystem 时，文件操作方法返回协程
    - 使用 SyncFileSystem 时，文件操作方法直接返回结果
    
    Example (异步):
        async with OpenList(...) as client:
            root = client.path("/data")
            
            # 路径操作 (不涉及网络)
            child = root / "subfolder" / "file.txt"
            print(child.name)  # "file.txt"
            print(child.parent)  # RemotePath("/data/subfolder")
            
            # 文件操作 (网络请求)
            if await child.exists():
                info = await child.stat()
                print(f"Size: {info.size}")
            
            # 遍历目录
            async for item in root.iterdir():
                print(item.name)
    
    Example (同步):
        with OpenListSync(...) as client:
            root = client.path("/data")
            
            if root.exists():
                for item in root.iterdir():
                    print(item.name)
    """
    
    __slots__ = ("_fs", "_path", "_is_async")
    
    def __init__(
        self, 
        fs: Union["AsyncFileSystem", "SyncFileSystem"],
        path: str = "/",
    ):
        """
        创建 RemotePath 对象
        
        Args:
            fs: 文件系统服务实例 (AsyncFileSystem 或 SyncFileSystem)
            path: 路径字符串
        """
        self._fs = fs
        self._path = self._normalize(path)
        # 检测是否为异步文件系统
        self._is_async = hasattr(fs, "_transport")  # AsyncFileSystem 有 _transport
    
    @staticmethod
    def _normalize(path: str) -> str:
        """规范化路径"""
        path = path.replace("\\", "/")
        path = posixpath.normpath(path)
        if not path.startswith("/"):
            path = "/" + path
        return path
    
    # =========================================================================
    # 路径属性 (纯本地计算，不涉及网络)
    # =========================================================================
    
    @property
    def path(self) -> str:
        """完整路径字符串"""
        return self._path
    
    @property
    def name(self) -> str:
        """文件或目录名称"""
        return posixpath.basename(self._path) or "/"
    
    @property
    def stem(self) -> str:
        """不含扩展名的文件名"""
        name = self.name
        if "." in name and name != ".":
            return name.rsplit(".", 1)[0]
        return name
    
    @property
    def suffix(self) -> str:
        """文件扩展名 (包含点号)"""
        name = self.name
        if "." in name and name != ".":
            return "." + name.rsplit(".", 1)[-1]
        return ""
    
    @property
    def suffixes(self) -> list[str]:
        """所有扩展名列表"""
        name = self.name
        if name.startswith("."):
            name = name[1:]
        parts = name.split(".")
        if len(parts) > 1:
            return ["." + s for s in parts[1:]]
        return []
    
    @property
    def parent(self) -> "RemotePath":
        """父目录路径"""
        parent_path = posixpath.dirname(self._path)
        if not parent_path:
            parent_path = "/"
        return RemotePath(self._fs, parent_path)
    
    @property
    def parents(self) -> tuple["RemotePath", ...]:
        """所有祖先目录路径"""
        result = []
        current = self.parent
        while current._path != "/":
            result.append(current)
            current = current.parent
        result.append(RemotePath(self._fs, "/"))
        return tuple(result)
    
    @property
    def parts(self) -> tuple[str, ...]:
        """路径各部分"""
        if self._path == "/":
            return ("/",)
        parts = self._path.split("/")
        return ("/",) + tuple(p for p in parts if p)
    
    def __truediv__(self, other: str) -> "RemotePath":
        """
        使用 / 运算符连接路径
        
        Example:
            path = RemotePath(fs, "/data") / "subfolder" / "file.txt"
            # 结果: RemotePath("/data/subfolder/file.txt")
        """
        if isinstance(other, RemotePath):
            other = other._path
        new_path = posixpath.join(self._path, other)
        return RemotePath(self._fs, new_path)
    
    def __rtruediv__(self, other: str) -> "RemotePath":
        """支持字符串在左侧"""
        new_path = posixpath.join(other, self._path)
        return RemotePath(self._fs, new_path)
    
    def joinpath(self, *parts: str) -> "RemotePath":
        """
        连接多个路径部分
        
        Example:
            path = root.joinpath("a", "b", "c.txt")
        """
        result = self._path
        for part in parts:
            result = posixpath.join(result, part)
        return RemotePath(self._fs, result)
    
    def with_name(self, name: str) -> "RemotePath":
        """返回具有不同名称的新路径"""
        if self._path == "/":
            raise ValueError("Cannot change name of root path")
        return RemotePath(self._fs, posixpath.join(posixpath.dirname(self._path), name))
    
    def with_stem(self, stem: str) -> "RemotePath":
        """返回具有不同 stem 的新路径"""
        return self.with_name(stem + self.suffix)
    
    def with_suffix(self, suffix: str) -> "RemotePath":
        """返回具有不同后缀的新路径"""
        if suffix and not suffix.startswith("."):
            raise ValueError(f"Invalid suffix: {suffix!r}")
        return self.with_name(self.stem + suffix)
    
    def is_absolute(self) -> bool:
        """是否为绝对路径 (远程路径总是绝对路径)"""
        return True
    
    def is_relative_to(self, other: Union[str, "RemotePath"]) -> bool:
        """检查是否相对于另一路径"""
        if isinstance(other, RemotePath):
            other = other._path
        other = self._normalize(other)
        return self._path.startswith(other.rstrip("/") + "/") or self._path == other
    
    def relative_to(self, other: Union[str, "RemotePath"]) -> str:
        """获取相对于另一路径的相对路径"""
        if isinstance(other, RemotePath):
            other = other._path
        other = self._normalize(other).rstrip("/")
        
        if not self.is_relative_to(other):
            raise ValueError(f"{self._path!r} is not relative to {other!r}")
        
        if self._path == other:
            return "."
        
        return self._path[len(other):].lstrip("/")
    
    # =========================================================================
    # 魔术方法
    # =========================================================================
    
    def __str__(self) -> str:
        return self._path
    
    def __repr__(self) -> str:
        return f"RemotePath({self._path!r})"
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, RemotePath):
            return self._path == other._path
        if isinstance(other, str):
            return self._path == self._normalize(other)
        return NotImplemented
    
    def __hash__(self) -> int:
        return hash(self._path)
    
    def __lt__(self, other: "RemotePath") -> bool:
        if isinstance(other, RemotePath):
            return self._path < other._path
        return NotImplemented
    
    def __le__(self, other: "RemotePath") -> bool:
        if isinstance(other, RemotePath):
            return self._path <= other._path
        return NotImplemented
    
    def __gt__(self, other: "RemotePath") -> bool:
        if isinstance(other, RemotePath):
            return self._path > other._path
        return NotImplemented
    
    def __ge__(self, other: "RemotePath") -> bool:
        if isinstance(other, RemotePath):
            return self._path >= other._path
        return NotImplemented
    
    # =========================================================================
    # 文件操作 - 异步版本
    # =========================================================================
    
    async def exists(self) -> bool:
        """检查路径是否存在"""
        return await self._fs.exists(self._path)
    
    async def is_dir(self) -> bool:
        """检查是否为目录"""
        return await self._fs.is_dir(self._path)
    
    async def is_file(self) -> bool:
        """检查是否为文件"""
        return await self._fs.is_file(self._path)
    
    async def stat(self) -> FileInfo:
        """获取文件/目录信息"""
        return await self._fs.stat(self._path)
    
    async def iterdir(self) -> AsyncIterator["RemotePath"]:
        """
        遍历目录内容
        
        Yields:
            目录中每个项目的 RemotePath 对象
        """
        items = await self._fs.listdir(self._path)
        for item in items:
            yield RemotePath(self._fs, posixpath.join(self._path, item.name))
    
    async def mkdir(self, exist_ok: bool = False) -> None:
        """
        创建目录
        
        Args:
            exist_ok: 目录已存在时不抛出异常
        """
        await self._fs.mkdir(self._path, exist_ok=exist_ok)
    
    async def rmdir(self) -> None:
        """删除目录"""
        await self._fs.rmdir(self._path)
    
    async def unlink(self) -> None:
        """删除文件"""
        await self._fs.unlink(self._path)
    
    async def remove(self) -> None:
        """删除文件或目录"""
        await self._fs.remove(self._path)
    
    async def read_bytes(self) -> bytes:
        """
        读取文件内容
        
        注意: 当前 API 不支持直接读取文件内容，此方法预留供未来扩展。
        
        Raises:
            NotImplementedError: 当前不支持此操作
        """
        raise NotImplementedError(
            "Direct file reading is not supported by the current API. "
            "Use the download URL from stat() to fetch file content."
        )
    
    async def write_bytes(
        self, 
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> None:
        """
        写入文件内容
        
        Args:
            data: 文件内容
            overwrite: 是否覆盖已存在的文件
        """
        options = UploadOptions(overwrite=overwrite)
        await self._fs.write_bytes(self._path, data, options=options)
    
    async def rename(self, target: Union[str, "RemotePath"]) -> "RemotePath":
        """
        重命名文件或目录
        
        注意: 只支持同目录下重命名，不支持移动到其他目录。
        
        Args:
            target: 新名称或新路径
            
        Returns:
            新路径的 RemotePath 对象
        """
        if isinstance(target, RemotePath):
            target = target._path
        
        await self._fs.rename(self._path, target)
        
        # 返回新路径
        new_name = posixpath.basename(target) if "/" in target else target
        new_path = posixpath.join(posixpath.dirname(self._path), new_name)
        return RemotePath(self._fs, new_path)
    
    async def copy_to(self, target: Union[str, "RemotePath"]) -> "RemotePath":
        """
        复制到目标位置
        
        Args:
            target: 目标目录路径
            
        Returns:
            目标位置的 RemotePath 对象
        """
        if isinstance(target, RemotePath):
            target = target._path
        target = self._normalize(target)
        
        await self._fs.copy(self._path, target)
        
        return RemotePath(self._fs, posixpath.join(target, self.name))
    
    async def move_to(self, target: Union[str, "RemotePath"]) -> "RemotePath":
        """
        移动到目标位置
        
        Args:
            target: 目标目录路径
            
        Returns:
            目标位置的 RemotePath 对象
        """
        if isinstance(target, RemotePath):
            target = target._path
        target = self._normalize(target)
        
        await self._fs.move(self._path, target)
        
        return RemotePath(self._fs, posixpath.join(target, self.name))


class SyncRemotePath:
    """
    同步版本的远程路径对象
    
    与 RemotePath 相同的 API，但所有文件操作都是同步的。
    
    Example:
        with OpenListSync(...) as client:
            root = client.path("/data")
            
            if root.exists():
                for item in root.iterdir():
                    print(item.name)
    """
    
    __slots__ = ("_fs", "_path")
    
    def __init__(
        self,
        fs: "SyncFileSystem",
        path: str = "/",
    ):
        self._fs = fs
        self._path = self._normalize(path)
    
    @staticmethod
    def _normalize(path: str) -> str:
        """规范化路径"""
        path = path.replace("\\", "/")
        path = posixpath.normpath(path)
        if not path.startswith("/"):
            path = "/" + path
        return path
    
    # =========================================================================
    # 路径属性 (与 RemotePath 相同)
    # =========================================================================
    
    @property
    def path(self) -> str:
        return self._path
    
    @property
    def name(self) -> str:
        return posixpath.basename(self._path) or "/"
    
    @property
    def stem(self) -> str:
        name = self.name
        if "." in name and name != ".":
            return name.rsplit(".", 1)[0]
        return name
    
    @property
    def suffix(self) -> str:
        name = self.name
        if "." in name and name != ".":
            return "." + name.rsplit(".", 1)[-1]
        return ""
    
    @property
    def suffixes(self) -> list[str]:
        name = self.name
        if name.startswith("."):
            name = name[1:]
        parts = name.split(".")
        if len(parts) > 1:
            return ["." + s for s in parts[1:]]
        return []
    
    @property
    def parent(self) -> "SyncRemotePath":
        parent_path = posixpath.dirname(self._path)
        if not parent_path:
            parent_path = "/"
        return SyncRemotePath(self._fs, parent_path)
    
    @property
    def parents(self) -> tuple["SyncRemotePath", ...]:
        result = []
        current = self.parent
        while current._path != "/":
            result.append(current)
            current = current.parent
        result.append(SyncRemotePath(self._fs, "/"))
        return tuple(result)
    
    @property
    def parts(self) -> tuple[str, ...]:
        if self._path == "/":
            return ("/",)
        parts = self._path.split("/")
        return ("/",) + tuple(p for p in parts if p)
    
    def __truediv__(self, other: str) -> "SyncRemotePath":
        if isinstance(other, SyncRemotePath):
            other = other._path
        new_path = posixpath.join(self._path, other)
        return SyncRemotePath(self._fs, new_path)
    
    def __rtruediv__(self, other: str) -> "SyncRemotePath":
        new_path = posixpath.join(other, self._path)
        return SyncRemotePath(self._fs, new_path)
    
    def joinpath(self, *parts: str) -> "SyncRemotePath":
        result = self._path
        for part in parts:
            result = posixpath.join(result, part)
        return SyncRemotePath(self._fs, result)
    
    def with_name(self, name: str) -> "SyncRemotePath":
        if self._path == "/":
            raise ValueError("Cannot change name of root path")
        return SyncRemotePath(self._fs, posixpath.join(posixpath.dirname(self._path), name))
    
    def with_stem(self, stem: str) -> "SyncRemotePath":
        return self.with_name(stem + self.suffix)
    
    def with_suffix(self, suffix: str) -> "SyncRemotePath":
        if suffix and not suffix.startswith("."):
            raise ValueError(f"Invalid suffix: {suffix!r}")
        return self.with_name(self.stem + suffix)
    
    def is_absolute(self) -> bool:
        return True
    
    def is_relative_to(self, other: Union[str, "SyncRemotePath"]) -> bool:
        if isinstance(other, SyncRemotePath):
            other = other._path
        other = self._normalize(other)
        return self._path.startswith(other.rstrip("/") + "/") or self._path == other
    
    def relative_to(self, other: Union[str, "SyncRemotePath"]) -> str:
        if isinstance(other, SyncRemotePath):
            other = other._path
        other = self._normalize(other).rstrip("/")
        
        if not self.is_relative_to(other):
            raise ValueError(f"{self._path!r} is not relative to {other!r}")
        
        if self._path == other:
            return "."
        
        return self._path[len(other):].lstrip("/")
    
    # =========================================================================
    # 魔术方法
    # =========================================================================
    
    def __str__(self) -> str:
        return self._path
    
    def __repr__(self) -> str:
        return f"SyncRemotePath({self._path!r})"
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (SyncRemotePath, RemotePath)):
            return self._path == other._path
        if isinstance(other, str):
            return self._path == self._normalize(other)
        return NotImplemented
    
    def __hash__(self) -> int:
        return hash(self._path)
    
    def __lt__(self, other: "SyncRemotePath") -> bool:
        if isinstance(other, (SyncRemotePath, RemotePath)):
            return self._path < other._path
        return NotImplemented
    
    def __le__(self, other: "SyncRemotePath") -> bool:
        if isinstance(other, (SyncRemotePath, RemotePath)):
            return self._path <= other._path
        return NotImplemented
    
    def __gt__(self, other: "SyncRemotePath") -> bool:
        if isinstance(other, (SyncRemotePath, RemotePath)):
            return self._path > other._path
        return NotImplemented
    
    def __ge__(self, other: "SyncRemotePath") -> bool:
        if isinstance(other, (SyncRemotePath, RemotePath)):
            return self._path >= other._path
        return NotImplemented
    
    # =========================================================================
    # 文件操作 - 同步版本
    # =========================================================================
    
    def exists(self) -> bool:
        """检查路径是否存在"""
        return self._fs.exists(self._path)
    
    def is_dir(self) -> bool:
        """检查是否为目录"""
        return self._fs.is_dir(self._path)
    
    def is_file(self) -> bool:
        """检查是否为文件"""
        return self._fs.is_file(self._path)
    
    def stat(self) -> FileInfo:
        """获取文件/目录信息"""
        return self._fs.stat(self._path)
    
    def iterdir(self) -> Iterator["SyncRemotePath"]:
        """遍历目录内容"""
        items = self._fs.listdir(self._path)
        for item in items:
            yield SyncRemotePath(self._fs, posixpath.join(self._path, item.name))
    
    def mkdir(self, exist_ok: bool = False) -> None:
        """创建目录"""
        self._fs.mkdir(self._path, exist_ok=exist_ok)
    
    def rmdir(self) -> None:
        """删除目录"""
        self._fs.rmdir(self._path)
    
    def unlink(self) -> None:
        """删除文件"""
        self._fs.unlink(self._path)
    
    def remove(self) -> None:
        """删除文件或目录"""
        self._fs.remove(self._path)
    
    def read_bytes(self) -> bytes:
        """读取文件内容 (当前不支持)"""
        raise NotImplementedError(
            "Direct file reading is not supported by the current API. "
            "Use the download URL from stat() to fetch file content."
        )
    
    def write_bytes(
        self,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> None:
        """写入文件内容"""
        options = UploadOptions(overwrite=overwrite)
        self._fs.write_bytes(self._path, data, options=options)
    
    def rename(self, target: Union[str, "SyncRemotePath"]) -> "SyncRemotePath":
        """重命名文件或目录"""
        if isinstance(target, SyncRemotePath):
            target = target._path
        
        self._fs.rename(self._path, target)
        
        new_name = posixpath.basename(target) if "/" in target else target
        new_path = posixpath.join(posixpath.dirname(self._path), new_name)
        return SyncRemotePath(self._fs, new_path)
    
    def copy_to(self, target: Union[str, "SyncRemotePath"]) -> "SyncRemotePath":
        """复制到目标位置"""
        if isinstance(target, SyncRemotePath):
            target = target._path
        target = self._normalize(target)
        
        self._fs.copy(self._path, target)
        
        return SyncRemotePath(self._fs, posixpath.join(target, self.name))
    
    def move_to(self, target: Union[str, "SyncRemotePath"]) -> "SyncRemotePath":
        """移动到目标位置"""
        if isinstance(target, SyncRemotePath):
            target = target._path
        target = self._normalize(target)
        
        self._fs.move(self._path, target)
        
        return SyncRemotePath(self._fs, posixpath.join(target, self.name))
