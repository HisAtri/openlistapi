"""
用户管理相关的 API 服务
"""
from .base import BaseService
from ..context import Context
from ..data_types import UserInfo, SSHKey, UserListResult
from ..utils import decode_token


class UserMe(BaseService):
    """当前用户信息"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        self.sshkey = MySSHKey(self.context)

    async def me(self) -> UserInfo:
        """
        获取当前用户信息

        GET /api/me
        """
        data = await self._get("/api/me")
        return UserInfo(**data["data"])

    async def update(self, username: str = None, password: str = None, sso_id: str = None) -> None:
        """
        更新用户信息；会使 JWT 失效，需要重新登录
        
        Args:
            username: 新用户名（可选）
            password: 新密码（可选）
            sso_id: SSO ID（可选）
        """
        payload = {
            "username": username or decode_token(self.context.auth_token).username,
            "password": password or "",
            "sso_id": sso_id or "",
        }
        await self._post("/api/me/update", json=payload)


class MySSHKey(BaseService):
    """当前用户 SSH 密钥管理"""

    async def add(self, name: str, public_key: str) -> None:
        """
        添加 SSH 密钥
        
        Args:
            name: 密钥名称
            public_key: 公钥内容
        """
        payload = {
            "name": name,
            "public_key": public_key,
        }
        await self._post("/api/me/sshkey/add", json=payload)

    async def delete(self, id: int) -> None:
        """
        删除 SSH 密钥
        
        Args:
            id: 密钥 ID
        """
        payload = {"id": id}
        await self._post("/api/me/sshkey/delete", json=payload)

    async def list(self) -> list[SSHKey]:
        """
        获取 SSH 密钥列表
        
        Returns:
            SSH 密钥列表
        """
        data = await self._get("/api/me/sshkey/list")
        return [SSHKey(**item) for item in data["data"]]


class Admin(BaseService):
    """管理员"""
    def __init__(self, context: Context):
        super().__init__(context)
        self.user = User(self.context)


class User(BaseService):
    """管理员用户管理"""

    async def list(self, page: int = 1, per_page: int = 30) -> UserListResult:
        """
        获取所有用户的分页列表（需要管理员Token）
        
        Args:
            page: 页码，默认为 1
            per_page: 每页数量，默认为 30
            
        Returns:
            UserListResult: 分页结果
        """
        params = {
            "page": page,
            "per_page": per_page,
        }
        data = await self._get("/api/admin/user/list", params=params)
        return UserListResult(
            content=[UserInfo(**user) for user in data["data"]["content"]],
            total=data["data"]["total"],
        )

    async def get(self, id: int) -> UserInfo:
        """
        通过 ID 获取特定用户信息（需要管理员Token）
        
        Args:
            id: 用户 ID
            
        Returns:
            UserInfo: 用户信息
        """
        params = {"id": id}
        data = await self._get("/api/admin/user/get", params=params)
        return UserInfo(**data["data"])

    async def create(self,
                     username: str,
                     password: str,
                     base_path: str,
                     role: int,
                     permission: int,
                     disabled: bool,
                    ) -> None:
        """
        创建用户

        Args:
            username: 用户名
            password: 密码
            base_path: 基础路径
            role: 角色
            permission: 权限
            disabled: 是否禁用
        """
        payload = {
            "username": username,
            "password": password,
            "base_path": base_path,
            "role": role,
            "permission": permission,
            "disabled": disabled,
        }
        await self._post("/api/admin/user/create", json=payload)
        return