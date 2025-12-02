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
            refresh: 是否强制刷新缓存，默认 False
            page: 页码，从 1 开始，默认 1
            per_page: 每页数量，范围 1-100，默认 30

        Returns:
            FsListResult: 包含文件列表、总数、README、权限等信息

        Raises:
            AuthenticationFailed: 认证失败或权限不足
            BadResponse: API 返回错误
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

        # 解析文件列表
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
            FsObject: 包含文件/目录的详细信息，包括：
                - id: 对象 ID（本地存储可能为空）
                - path: 完整系统路径
                - name: 文件或目录名称
                - size: 文件大小（字节），目录为 0
                - is_dir: 是否为目录
                - modified: 最后修改时间
                - created: 创建时间
                - sign: 下载认证签名
                - thumb: 缩略图 URL（如果有）
                - type: 文件类型（0=未知, 1=文件夹, 2=视频, 3=音频, 4=文本, 5=图片）
                - hashinfo: 哈希信息（JSON 字符串）
                - hash_info: 解析后的哈希信息
                - mount_details: 挂载存储详情

        Raises:
            AuthenticationFailed: 认证失败或权限不足
            BadResponse: API 返回错误（如文件不存在）
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

        支持两种调用方式（类似 os.remove 的简洁性，同时支持批量操作）：

        用法1 - 单路径删除（类似 os.remove）:
            await fs.remove("/folder/file.txt")  # 删除指定文件
            await fs.remove("/folder/subdir")    # 删除指定目录

        用法2 - 批量删除（指定目录 + 文件名列表）:
            await fs.remove("/folder", "file1.txt", "file2.txt")

        Args:
            path: 单路径模式时为完整文件/目录路径；
                  批量模式时为包含要删除文件的目录路径
            *names: 可选，要删除的文件/目录名称列表

        Raises:
            AuthenticationFailed: 认证失败或权限不足
            BadResponse: API 返回错误

        Examples:
            # 删除单个文件
            await fs.remove("/data/old_file.txt")

            # 删除多个文件
            await fs.remove("/data", "file1.txt", "file2.txt", "file3.txt")
        """
        if names:
            # 批量模式：path 是目录，names 是文件名列表
            dir_path = path
            name_list = list(names)
        else:
            # 单路径模式：从 path 中分离目录和文件名
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
        重命名文件或目录（类似 os.rename）。

        Args:
            src: 源文件/目录的完整路径
            dst: 新名称。可以是：
                 - 仅文件名（如 "new_name.txt"）
                 - 完整路径（如 "/folder/new_name.txt"，会自动提取文件名部分）

        Raises:
            AuthenticationFailed: 认证失败或权限不足
            BadResponse: API 返回错误

        Examples:
            # 使用新名称
            await fs.rename("/data/old.txt", "new.txt")

            # 使用完整路径（会自动提取 basename）
            await fs.rename("/data/old.txt", "/data/new.txt")
        """
        # 如果 dst 是完整路径，提取文件名部分
        new_name = posixpath.basename(dst) if "/" in dst else dst

        payload = {
            "path": src,
            "name": new_name,
        }
        await self._post("/api/fs/rename", json=payload)

    async def batch_rename(
        self,
        dir_path: str,
        rename_pairs: list[Union[tuple[str, str], RenameObject]],
    ) -> None:
        """
        批量重命名文件。

        Args:
            dir_path: 源目录路径
            rename_pairs: 重命名映射列表，每项可以是：
                - (src_name, new_name) 元组
                - RenameObject 对象

        Raises:
            AuthenticationFailed: 认证失败或权限不足
            BadResponse: API 返回错误

        Examples:
            # 使用元组列表
            await fs.batch_rename("/data", [
                ("old1.txt", "new1.txt"),
                ("old2.txt", "new2.txt"),
            ])

            # 使用 RenameObject
            from openlist.data_types import RenameObject
            await fs.batch_rename("/data", [
                RenameObject(src_name="old1.txt", new_name="new1.txt"),
                RenameObject(src_name="old2.txt", new_name="new2.txt"),
            ])
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
            "src_dir": dir_path,
            "rename_objects": rename_objects,
        }
        await self._post("/api/fs/batch_rename", json=payload)

    async def makedirs(
        self,
        path: str,
        exist_ok: bool = False,
    ) -> None:
        """
        创建目录（类似 os.makedirs）。

        注意：OpenList API 会自动递归创建所有必需的父目录。

        Args:
            path: 要创建的目录路径
            exist_ok: 如果为 True，当目录已存在时不抛出异常；
                      如果为 False（默认），目录已存在时抛出 BadResponse

        Raises:
            AuthenticationFailed: 认证失败或权限不足
            BadResponse: 目录已存在（当 exist_ok=False）或其他 API 错误

        Examples:
            # 创建目录，如果已存在则报错
            await fs.makedirs("/data/new_folder")

            # 创建目录，如果已存在则忽略
            await fs.makedirs("/data/new_folder", exist_ok=True)
        """
        payload = {"path": path}

        try:
            await self._post("/api/fs/mkdir", json=payload)
        except BadResponse as e:
            if exist_ok and ("exist" in str(e).lower() or "already" in str(e).lower()):
                return
            raise

    # 别名
    mkdir = makedirs
