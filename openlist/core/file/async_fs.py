"""
异步文件系统
"""
import os
import posixpath
from typing import AsyncIterator, Iterator

from ...context import Context
from ...exceptions import FileExistsError, FileNotFoundError, IsADirectoryError
from ...models.file import (
    DirectoryListing,
    FileInfo,
    ListOptions,
    RenameItem,
    UploadOptions,
)
from .transport import FileTransport


class AsyncFileSystem:
    """
    异步文件系统操作
    
    提供类似标准库 os/shutil 的语义清晰的文件操作接口。
    所有方法都是异步的 (async/await)。
    
    Example:
        async with OpenList(...) as client:
            fs = client.fs
            
            # 列出目录
            files = await fs.listdir("/data")
            
            # 检查文件
            if await fs.exists("/data/file.txt"):
                info = await fs.stat("/data/file.txt")
                print(f"Size: {info.size}")
            
            # 创建目录
            await fs.mkdir("/data/new_folder", exist_ok=True)
            
            # 上传文件
            await fs.write_bytes("/data/hello.txt", b"Hello!")
    """
    
    def __init__(self, context: Context):
        self._context = context
        self._transport = FileTransport(context)
    
    @staticmethod
    def _normalize_path(path: str) -> str:
        """规范化路径为 POSIX 格式"""
        # 替换反斜杠
        path = path.replace("\\", "/")
        # 规范化路径
        path = posixpath.normpath(path)
        # 确保以 / 开头
        if not path.startswith("/"):
            path = "/" + path
        return path
    
    # =========================================================================
    # 查询操作
    # =========================================================================
    
    async def listdir(
        self,
        path: str = "/",
        *,
        password: str | None = None,
        refresh: bool = False,
    ) -> list[FileInfo]:
        """
        列出目录下的所有文件和子目录
        
        Args:
            path: 目录路径
            password: 受保护目录的密码
            refresh: 是否强制刷新缓存
            
        Returns:
            FileInfo 对象列表
        """
        path = self._normalize_path(path)
        data = await self._transport.list_directory(
            path, 
            password=password, 
            refresh=refresh,
            page=1,
            per_page=100,  # 获取较多结果
        )
        
        content = data.get("content") or []
        return [FileInfo(**item) for item in content]
    
    async def listdir_detail(
        self,
        path: str = "/",
        *,
        options: ListOptions | None = None,
    ) -> DirectoryListing:
        """
        列出目录内容 (包含完整元信息)
        
        Args:
            path: 目录路径
            options: 列表选项
            
        Returns:
            DirectoryListing 包含文件列表和元信息
        """
        path = self._normalize_path(path)
        opts = options or ListOptions()
        
        data = await self._transport.list_directory(
            path,
            password=opts.password,
            refresh=opts.refresh,
            page=opts.page,
            per_page=opts.per_page,
        )
        
        content = data.get("content") or []
        items = [FileInfo(**item) for item in content]
        
        return DirectoryListing(
            items=items,
            total=data.get("total", len(items)),
            readme=data.get("readme", ""),
            header=data.get("header", ""),
            has_write_permission=data.get("write", False),
            provider=data.get("provider", ""),
        )
    
    async def stat(
        self,
        path: str,
        *,
        password: str | None = None,
    ) -> FileInfo:
        """
        获取文件或目录的详细信息
        
        Args:
            path: 文件或目录路径
            password: 受保护路径的密码
            
        Returns:
            FileInfo 对象
            
        Raises:
            FileNotFoundError: 路径不存在
        """
        path = self._normalize_path(path)
        data = await self._transport.get_info(path, password=password)
        return FileInfo(**data)
    
    async def exists(
        self,
        path: str,
        *,
        password: str | None = None,
    ) -> bool:
        """
        检查路径是否存在
        
        Args:
            path: 文件或目录路径
            password: 受保护路径的密码
            
        Returns:
            存在返回 True，否则 False
        """
        try:
            await self.stat(path, password=password)
            return True
        except FileNotFoundError:
            return False
    
    async def is_dir(
        self,
        path: str,
        *,
        password: str | None = None,
    ) -> bool:
        """
        检查路径是否为目录
        
        Args:
            path: 路径
            password: 受保护路径的密码
            
        Returns:
            是目录返回 True，否则 False (包括不存在的情况)
        """
        try:
            info = await self.stat(path, password=password)
            return info.is_dir
        except FileNotFoundError:
            return False
    
    async def is_file(
        self,
        path: str,
        *,
        password: str | None = None,
    ) -> bool:
        """
        检查路径是否为文件
        
        Args:
            path: 路径
            password: 受保护路径的密码
            
        Returns:
            是文件返回 True，否则 False (包括不存在的情况)
        """
        try:
            info = await self.stat(path, password=password)
            return not info.is_dir
        except FileNotFoundError:
            return False
    
    # =========================================================================
    # 目录操作
    # =========================================================================
    
    async def mkdir(
        self,
        path: str,
        exist_ok: bool = False,
    ) -> None:
        """
        创建目录 (自动创建所有父目录)
        
        Args:
            path: 目录路径
            exist_ok: 为 True 时，目录已存在不抛出异常
            
        Raises:
            FileExistsError: 目录已存在且 exist_ok=False
        """
        path = self._normalize_path(path)
        try:
            await self._transport.mkdir(path)
        except FileExistsError:
            if not exist_ok:
                raise
    
    # makedirs 是 mkdir 的别名
    makedirs = mkdir
    
    # =========================================================================
    # 删除操作
    # =========================================================================
    
    async def remove(
        self,
        path: str,
    ) -> None:
        """
        删除文件或目录
        
        删除文件或空目录。如果是非空目录，也会被删除。
        
        Args:
            path: 文件或目录路径
            
        Raises:
            FileNotFoundError: 路径不存在
        """
        path = self._normalize_path(path)
        dir_path = posixpath.dirname(path)
        name = posixpath.basename(path)
        await self._transport.remove(dir_path, [name])
    
    async def unlink(
        self,
        path: str,
    ) -> None:
        """
        删除文件
        
        与 remove() 功能相同，命名与 pathlib.Path.unlink() 一致。
        
        Args:
            path: 文件路径
        """
        await self.remove(path)
    
    async def rmdir(
        self,
        path: str,
    ) -> None:
        """
        删除目录
        
        与 remove() 功能相同，命名与 os.rmdir() 一致。
        
        Args:
            path: 目录路径
        """
        await self.remove(path)
    
    async def remove_many(
        self,
        dir_path: str,
        names: list[str],
    ) -> None:
        """
        批量删除同一目录下的多个文件/目录
        
        Args:
            dir_path: 父目录路径
            names: 要删除的文件/目录名列表
        """
        dir_path = self._normalize_path(dir_path)
        await self._transport.remove(dir_path, names)
    
    # =========================================================================
    # 重命名操作
    # =========================================================================
    
    async def rename(
        self,
        src: str,
        dst: str,
    ) -> None:
        """
        重命名文件或目录
        
        注意: 此操作仅支持重命名，不支持移动到其他目录。
        如果 dst 包含路径，将只取其 basename 作为新名称。
        
        Args:
            src: 源文件/目录完整路径
            dst: 新名称或新完整路径 (只使用 basename)
            
        Raises:
            FileNotFoundError: 源路径不存在
        """
        src = self._normalize_path(src)
        new_name = posixpath.basename(dst) if "/" in dst else dst
        await self._transport.rename(src, new_name)
    
    async def rename_many(
        self,
        dir_path: str,
        items: list[RenameItem | tuple[str, str]],
    ) -> None:
        """
        批量重命名同一目录下的多个文件
        
        Args:
            dir_path: 目录路径
            items: 重命名项列表，每项为 RenameItem 或 (旧名, 新名) 元组
        """
        dir_path = self._normalize_path(dir_path)
        
        rename_objects = []
        for item in items:
            if isinstance(item, tuple):
                rename_objects.append({
                    "src_name": item[0],
                    "new_name": item[1],
                })
            else:
                rename_objects.append({
                    "src_name": item.src_name,
                    "new_name": item.new_name,
                })
        
        await self._transport.batch_rename(dir_path, rename_objects)
    
    # =========================================================================
    # 复制和移动操作
    # =========================================================================
    
    async def copy(
        self,
        src: str,
        dst: str,
    ) -> None:
        """
        复制文件或目录到目标位置
        
        Args:
            src: 源文件/目录完整路径
            dst: 目标目录路径
            
        Raises:
            FileNotFoundError: 源路径不存在
        """
        src = self._normalize_path(src)
        dst = self._normalize_path(dst)
        
        src_dir = posixpath.dirname(src)
        name = posixpath.basename(src)
        
        await self._transport.copy(src_dir, dst, [name])
    
    async def copy_many(
        self,
        src_dir: str,
        dst_dir: str,
        names: list[str],
    ) -> None:
        """
        批量复制同一目录下的多个文件/目录
        
        Args:
            src_dir: 源目录路径
            dst_dir: 目标目录路径
            names: 要复制的文件/目录名列表
        """
        src_dir = self._normalize_path(src_dir)
        dst_dir = self._normalize_path(dst_dir)
        await self._transport.copy(src_dir, dst_dir, names)
    
    async def move(
        self,
        src: str,
        dst: str,
    ) -> None:
        """
        移动文件或目录到目标位置
        
        Args:
            src: 源文件/目录完整路径
            dst: 目标目录路径
            
        Raises:
            FileNotFoundError: 源路径不存在
        """
        src = self._normalize_path(src)
        dst = self._normalize_path(dst)
        
        src_dir = posixpath.dirname(src)
        name = posixpath.basename(src)
        
        await self._transport.move(src_dir, dst, [name])
    
    async def move_many(
        self,
        src_dir: str,
        dst_dir: str,
        names: list[str],
    ) -> None:
        """
        批量移动同一目录下的多个文件/目录
        
        Args:
            src_dir: 源目录路径
            dst_dir: 目标目录路径
            names: 要移动的文件/目录名列表
        """
        src_dir = self._normalize_path(src_dir)
        dst_dir = self._normalize_path(dst_dir)
        await self._transport.move(src_dir, dst_dir, names)
    
    async def recursive_move(
        self,
        src: str,
        dst: str,
    ) -> None:
        """
        递归移动目录 (保留目录结构)
        
        Args:
            src: 源目录路径
            dst: 目标目录路径
        """
        src = self._normalize_path(src)
        dst = self._normalize_path(dst)
        await self._transport.recursive_move(src, dst)
    
    # =========================================================================
    # 文件读写操作
    # =========================================================================
    
    async def write_bytes(
        self,
        path: str,
        data: bytes | Iterator[bytes] | AsyncIterator[bytes],
        *,
        options: UploadOptions | None = None,
    ) -> None:
        """
        写入字节数据到文件
        
        Args:
            path: 目标文件路径
            data: 文件内容 (bytes 或迭代器)
            options: 上传选项
            
        Raises:
            FileExistsError: 文件已存在且 overwrite=False
        """
        path = self._normalize_path(path)
        opts = options or UploadOptions()
        
        await self._transport.upload(
            path,
            data,
            last_modified=opts.last_modified,
            overwrite=opts.overwrite,
            password=opts.password,
            as_task=opts.as_task,
        )
    
    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        *,
        chunk_size: int = 1024 * 1024,  # 1MB
        options: UploadOptions | None = None,
    ) -> None:
        """
        从本地文件上传到远程
        
        使用分片流式上传，适合大文件。
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程目标路径
            chunk_size: 分片大小 (字节)，默认 1MB
            options: 上传选项
        """
        remote_path = self._normalize_path(remote_path)
        opts = options or UploadOptions()
        
        # 如果未指定修改时间，使用本地文件的修改时间
        last_modified = opts.last_modified
        if last_modified is None:
            last_modified = int(os.path.getmtime(local_path))
        
        def file_chunk_generator() -> Iterator[bytes]:
            """分片读取本地文件"""
            with open(local_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    yield chunk
        
        await self._transport.upload(
            remote_path,
            file_chunk_generator(),
            last_modified=last_modified,
            overwrite=opts.overwrite,
            password=opts.password,
            as_task=opts.as_task,
        )
