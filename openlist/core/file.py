"""
基本文件操作API
"""
import posixpath
from typing import Optional, Union
from .base import BaseService
from ..data_types import FsListResult, FsObject, RenameObject
from ..exceptions import BadResponse


class FileSystem(BaseService):
    """文件系统操作"""

    async def listdir(
        self,
        path: str = "/",
        *,
        password: Optional[str] = None,
        refresh: bool = False,
        page: int = 1,
        per_page: int = 30,
    ) -> FsListResult:
        """
        列出指定路径下的文件和目录。

        Args:
            path: 要列出的路径，默认为根目录 "/"
            password: 受保护路径的访问密码
            refresh: 是否强制刷新缓存
            page: 页码，从 1 开始
            per_page: 每页数量，范围 1-100

        Returns:
            FsListResult: 包含文件列表、总数、README、权限等信息
        """
        payload = {
            "path": path,
            "refresh": refresh,
            "page": page,
            "per_page": per_page,
        }
        if password is not None:
            payload["password"] = password

        response = await self._post("/api/fs/list", json=payload)
        data = response.get("data", {})

        content = [FsObject(**item) for item in data.get("content", [])]

        return FsListResult(
            content=content,
            total=data.get("total", 0),
            readme=data.get("readme", ""),
            header=data.get("header", ""),
            write=data.get("write", False),
            provider=data.get("provider", ""),
        )

    async def info(
        self,
        path: str,
        *,
        password: Optional[str] = None,
    ) -> FsObject:
        """
        获取指定文件或目录的详细信息。

        Args:
            path: 文件或目录路径
            password: 受保护路径的访问密码

        Returns:
            FsObject: 文件/目录的详细信息
        """
        payload = {"path": path}
        if password is not None:
            payload["password"] = password

        response = await self._post("/api/fs/get", json=payload)
        data = response.get("data", {})

        return FsObject(**data)

    async def remove(
        self,
        path: str,
        *names: str,
    ) -> None:
        """
        删除文件或目录。

        Args:
            path: 单文件模式时为完整路径；批量模式时为目录路径
            *names: 批量删除时，要删除的文件/目录名称列表

        Examples:
            await fs.remove("/folder/file.txt")           # 删除单个文件
            await fs.remove("/folder", "a.txt", "b.txt")  # 批量删除
        """
        if names:
            dir_path = path
            name_list = list(names)
        else:
            dir_path = posixpath.dirname(path)
            name_list = [posixpath.basename(path)]

        payload = {
            "dir": dir_path,
            "names": name_list,
        }
        await self._post("/api/fs/remove", json=payload)

    async def rename(
        self,
        src: str,
        dst: str,
    ) -> None:
        """
        重命名文件或目录（不能用于移动）。

        Args:
            src: 源文件/目录的完整路径
            dst: 新名称或完整路径（会自动提取 basename）

        Examples:
            await fs.rename("/data/old.txt", "new.txt")
            await fs.rename("/data/old.txt", "/data/new.txt")
        """
        new_name = posixpath.basename(dst) if "/" in dst else dst

        payload = {
            "path": src,
            "name": new_name,
        }
        await self._post("/api/fs/rename", json=payload)

    async def batch_rename(
        self,
        path: str,
        rename_pairs: list[Union[tuple[str, str], RenameObject]],
    ) -> None:
        """
        批量重命名文件。

        Args:
            path: 文件所在目录路径
            rename_pairs: 重命名映射列表，每项为 (旧名, 新名) 元组或 RenameObject

        Examples:
            await fs.batch_rename("/data", [("old1.txt", "new1.txt"), ("old2.txt", "new2.txt")])
        """
        rename_objects = []
        for item in rename_pairs:
            if isinstance(item, tuple):
                rename_objects.append({
                    "src_name": item[0],
                    "new_name": item[1],
                })
            elif isinstance(item, RenameObject):
                rename_objects.append({
                    "src_name": item.src_name,
                    "new_name": item.new_name,
                })
            else:
                rename_objects.append(item)

        payload = {
            "src_dir": path,
            "rename_objects": rename_objects,
        }
        await self._post("/api/fs/batch_rename", json=payload)

    async def makedirs(
        self,
        path: str,
        exist_ok: bool = False,
    ) -> None:
        """
        创建目录（自动创建所有父目录）。

        Args:
            path: 要创建的目录路径
            exist_ok: 为 True 时，目录已存在不抛异常

        Examples:
            await fs.makedirs("/data/new_folder")
            await fs.makedirs("/data/new_folder", exist_ok=True)
        """
        payload = {"path": path}

        try:
            await self._post("/api/fs/mkdir", json=payload)
        except BadResponse as e:
            if exist_ok and ("exist" in str(e).lower() or "already" in str(e).lower()):
                return
            raise

    mkdir = makedirs

    async def copy(
        self,
        src: str,
        dst: str,
        *names: str,
    ) -> None:
        """
        复制文件或目录。

        Args:
            src: 单文件模式时为源文件完整路径；批量模式时为源目录路径
            dst: 目标目录路径
            *names: 批量模式时，要复制的文件/目录名称列表

        Examples:
            await fs.copy("/data/file.txt", "/backup/")             # 复制单个文件
            await fs.copy("/data/", "/backup/", "a.txt", "b.txt")   # 批量复制
        """
        if names:
            src_dir = src
            dst_dir = dst
            name_list = list(names)
        else:
            src_dir = posixpath.dirname(src)
            dst_dir = dst
            name_list = [posixpath.basename(src)]

        payload = {
            "src_dir": src_dir,
            "dst_dir": dst_dir,
            "names": name_list,
        }
        await self._post("/api/fs/copy", json=payload)

    async def move(
        self,
        src: str,
        dst: str,
        *names: str,
    ) -> None:
        """
        移动文件或目录。

        Args:
            src: 单文件模式时为源文件完整路径；批量模式时为源目录路径
            dst: 目标目录路径
            *names: 批量模式时，要移动的文件/目录名称列表

        Examples:
            await fs.move("/data/file.txt", "/archive/")            # 移动单个文件
            await fs.move("/data/", "/archive/", "a.txt", "b.txt")  # 批量移动
        """
        if names:
            src_dir = src
            dst_dir = dst
            name_list = list(names)
        else:
            src_dir = posixpath.dirname(src)
            dst_dir = dst
            name_list = [posixpath.basename(src)]

        payload = {
            "src_dir": src_dir,
            "dst_dir": dst_dir,
            "names": name_list,
        }
        await self._post("/api/fs/move", json=payload)

    async def recursive_move(
        self,
        src: str,
        dst: str,
    ) -> None:
        """
        递归移动目录（保留目录结构）。

        Args:
            src: 源目录路径
            dst: 目标目录路径

        Examples:
            await fs.recursive_move("/data/folder/", "/archive/")
        """
        payload = {
            "src_dir": src,
            "dst_dir": dst,
        }
        await self._post("/api/fs/recursive_move", json=payload)
