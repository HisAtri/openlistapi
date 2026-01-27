"""
文件系统操作模块

提供多种风格的文件系统操作接口:
- AsyncFileSystem: 异步文件系统服务
- SyncFileSystem: 同步文件系统服务
- RemotePath: pathlib 风格的异步路径对象
- SyncRemotePath: pathlib 风格的同步路径对象

Example (异步):
    from openlist.core.file import AsyncFileSystem, RemotePath
    
    async with OpenList(...) as client:
        # 使用 FileSystem 服务
        fs = AsyncFileSystem(client.context)
        files = await fs.listdir("/data")
        
        # 使用 RemotePath 对象
        path = RemotePath(fs, "/data/file.txt")
        if await path.exists():
            await path.unlink()

Example (同步):
    from openlist.core.file import SyncFileSystem, SyncRemotePath
    
    with OpenListSync(...) as client:
        fs = SyncFileSystem(client.context)
        files = fs.listdir("/data")
"""
from .async_fs import AsyncFileSystem
from .sync_fs import SyncFileSystem
from .path import RemotePath, SyncRemotePath
from .transport import FileTransport

__all__ = [
    # 文件系统服务
    "AsyncFileSystem",
    "SyncFileSystem",
    # 路径对象
    "RemotePath",
    "SyncRemotePath",
    # 传输层 (高级用户)
    "FileTransport",
]
