"""
同步文件系统
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator

from ...context import Context
from ...models.file import (
    DirectoryListing,
    FileInfo,
    ListOptions,
    RenameItem,
    UploadOptions,
)
from .async_fs import AsyncFileSystem


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """获取或创建事件循环"""
    try:
        loop = asyncio.get_running_loop()
        return loop
    except RuntimeError:
        pass
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def _run_sync(coro):
    """
    在同步上下文中运行协程
    
    如果当前没有运行中的事件循环，使用 asyncio.run()。
    如果在异步上下文中调用（有运行中的循环），使用线程池。
    """
    try:
        asyncio.get_running_loop()
        # 在异步上下文中，需要在新线程中运行
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # 没有运行中的循环，直接运行
        return asyncio.run(coro)


class SyncFileSystem:
    """
    同步文件系统操作
    
    提供与 AsyncFileSystem 相同的 API，但所有方法都是同步的。
    适用于不需要异步的场景。
    
    Example:
        with OpenListSync(...) as client:
            fs = client.fs
            
            # 列出目录
            files = fs.listdir("/data")
            
            # 检查文件
            if fs.exists("/data/file.txt"):
                info = fs.stat("/data/file.txt")
                print(f"Size: {info.size}")
            
            # 创建目录
            fs.mkdir("/data/new_folder", exist_ok=True)
            
            # 上传文件
            fs.write_bytes("/data/hello.txt", b"Hello!")
    """
    
    def __init__(self, context: Context):
        self._context = context
        self._async_fs = AsyncFileSystem(context)
    
    # =========================================================================
    # 查询操作
    # =========================================================================
    
    def listdir(
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
        return _run_sync(self._async_fs.listdir(path, password=password, refresh=refresh))
    
    def listdir_detail(
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
        return _run_sync(self._async_fs.listdir_detail(path, options=options))
    
    def stat(
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
        return _run_sync(self._async_fs.stat(path, password=password))
    
    def exists(
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
        return _run_sync(self._async_fs.exists(path, password=password))
    
    def is_dir(
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
            是目录返回 True，否则 False
        """
        return _run_sync(self._async_fs.is_dir(path, password=password))
    
    def is_file(
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
            是文件返回 True，否则 False
        """
        return _run_sync(self._async_fs.is_file(path, password=password))
    
    # =========================================================================
    # 目录操作
    # =========================================================================
    
    def mkdir(
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
        return _run_sync(self._async_fs.mkdir(path, exist_ok=exist_ok))
    
    # makedirs 是 mkdir 的别名
    makedirs = mkdir
    
    # =========================================================================
    # 删除操作
    # =========================================================================
    
    def remove(
        self,
        path: str,
    ) -> None:
        """
        删除文件或目录
        
        Args:
            path: 文件或目录路径
            
        Raises:
            FileNotFoundError: 路径不存在
        """
        return _run_sync(self._async_fs.remove(path))
    
    def unlink(
        self,
        path: str,
    ) -> None:
        """
        删除文件
        
        与 remove() 功能相同，命名与 pathlib.Path.unlink() 一致。
        
        Args:
            path: 文件路径
        """
        return _run_sync(self._async_fs.unlink(path))
    
    def rmdir(
        self,
        path: str,
    ) -> None:
        """
        删除目录
        
        与 remove() 功能相同，命名与 os.rmdir() 一致。
        
        Args:
            path: 目录路径
        """
        return _run_sync(self._async_fs.rmdir(path))
    
    def remove_many(
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
        return _run_sync(self._async_fs.remove_many(dir_path, names))
    
    # =========================================================================
    # 重命名操作
    # =========================================================================
    
    def rename(
        self,
        src: str,
        dst: str,
    ) -> None:
        """
        重命名文件或目录
        
        注意: 此操作仅支持重命名，不支持移动到其他目录。
        
        Args:
            src: 源文件/目录完整路径
            dst: 新名称或新完整路径 (只使用 basename)
            
        Raises:
            FileNotFoundError: 源路径不存在
        """
        return _run_sync(self._async_fs.rename(src, dst))
    
    def rename_many(
        self,
        dir_path: str,
        items: list[RenameItem | tuple[str, str]],
    ) -> None:
        """
        批量重命名同一目录下的多个文件
        
        Args:
            dir_path: 目录路径
            items: 重命名项列表
        """
        return _run_sync(self._async_fs.rename_many(dir_path, items))
    
    # =========================================================================
    # 复制和移动操作
    # =========================================================================
    
    def copy(
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
        return _run_sync(self._async_fs.copy(src, dst))
    
    def copy_many(
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
        return _run_sync(self._async_fs.copy_many(src_dir, dst_dir, names))
    
    def move(
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
        return _run_sync(self._async_fs.move(src, dst))
    
    def move_many(
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
        return _run_sync(self._async_fs.move_many(src_dir, dst_dir, names))
    
    def recursive_move(
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
        return _run_sync(self._async_fs.recursive_move(src, dst))
    
    # =========================================================================
    # 文件读写操作
    # =========================================================================
    
    def write_bytes(
        self,
        path: str,
        data: bytes | Iterator[bytes],
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
        return _run_sync(self._async_fs.write_bytes(path, data, options=options))
    
    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        *,
        chunk_size: int = 1024 * 1024,
        options: UploadOptions | None = None,
    ) -> None:
        """
        从本地文件上传到远程
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程目标路径
            chunk_size: 分片大小 (字节)
            options: 上传选项
        """
        return _run_sync(
            self._async_fs.upload_file(
                local_path, remote_path, 
                chunk_size=chunk_size, 
                options=options
            )
        )
