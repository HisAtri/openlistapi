# OpenList API 参考文档

> **生成日期**：2026-06-21
> **库版本**：0.1.1-beta2
> **覆盖范围**：`openlist` 库的全部公开 API（**已排除 CLI 模块** `openlist/cli/*`）
> **Python 要求**：>= 3.10

本文档按项目结构目录顺序，逐一罗列 openlist 库当前所有的类、方法、属性、函数、数据模型、异常、枚举，并提供完整签名、说明与关键示例。所有签名严格依据源代码。

---

## 目录

- [文档约定](#文档约定)
- [项目结构概览](#项目结构概览)
- [1. `openlist/__init__.py` — 客户端入口](#1-openlist__init__py--客户端入口)
- [2. `openlist/context.py` — 会话上下文](#2-openlistcontextpy--会话上下文)
- [3. `openlist/data_types.py` — 用户/认证模型](#3-openlistdata_typespy--用户认证模型)
- [4. `openlist/exceptions.py` — 异常体系](#4-openlistexceptionspy--异常体系)
- [5. `openlist/utils.py` — 工具函数](#5-openlistutilspy--工具函数)
- [6. `openlist/models/file.py` — 文件系统模型](#6-openlistmodelsfilepy--文件系统模型)
- [7. `openlist/models/__init__.py` — 模型包导出](#7-openlistmodels__init__py--模型包导出)
- [8. `openlist/core/base.py` — 服务基类](#8-openlistcorebasepy--服务基类)
- [9. `openlist/core/authentication.py` — 认证服务](#9-openlistcoreauthenticationpy--认证服务)
- [10. `openlist/core/admin.py` — 用户/管理员服务](#10-openlistcoreadminpy--用户管理员服务)
- [11. `openlist/core/file/async_fs.py` — 异步文件系统](#11-openlistcorefileasync_fspy--异步文件系统)
- [12. `openlist/core/file/sync_fs.py` — 同步文件系统](#12-openlistcorefilesync_fspy--同步文件系统)
- [13. `openlist/core/file/path.py` — 路径对象](#13-openlistcorefilepathpy--路径对象)
- [14. `openlist/core/file/transport.py` — 传输层](#14-openlistcorefiletransportpy--传输层)
- [包导出速查](#包导出速查)
- [使用示例合集](#使用示例合集)
- [异常层级速查图](#异常层级速查图)

---

## 文档约定

| 标记 | 含义 |
|------|------|
| `async` | 异步方法/协程，需 `await` 调用 |
| `@property` | 只读属性（property 装饰器） |
| `classmethod` | 类方法 |
| `staticmethod` | 静态方法 |
| `abc.abstractmethod` | 抽象方法，子类必须实现 |
| `_前缀` | 私有/受保护成员（仅在需说明时列出） |
| `*` | 关键字参数分隔符之后的参数为仅关键字参数 |

**类型注解符号**：
- `X | Y` → 联合类型（`X` 或 `Y`）
- `X | None` → 可选类型，等价于 `Optional[X]`
- `list[X]` / `dict[K, V]` / `tuple[X, ...]` → 泛型容器

**说明文字来源**：优先采用源码 docstring（中文）。无 docstring 处给出简短中文说明，会以 *斜体* 标注为推断说明。

---

## 项目结构概览

以下是 `openlist/` 包的完整文件树（**已排除 CLI 模块**）：

```
openlist/
├── __init__.py                  # 客户端入口：Client 类（异步）
├── context.py                   # Context 数据类：会话/连接共享状态
├── data_types.py                # 用户/认证相关 Pydantic 模型
├── exceptions.py                # 层次化异常体系（11 个类）
├── utils.py                     # 工具函数 + TimeLike 类型别名
├── models/
│   ├── __init__.py              # 模型包导出
│   └── file.py                  # 文件系统相关 Pydantic 模型 + FileType 枚举
└── core/
    ├── __init__.py              # 核心模块导出
    ├── base.py                  # BaseService：API 服务抽象基类
    ├── authentication.py        # Authentication：登录/登出/OTP
    ├── admin.py                 # UserMe / MySSHKey / Admin / User
    └── file/
        ├── __init__.py          # 文件系统模块导出
        ├── async_fs.py          # AsyncFileSystem：异步高层文件系统
        ├── sync_fs.py           # SyncFileSystem：同步高层文件系统
        ├── path.py              # RemotePath / SyncRemotePath：pathlib 风格路径对象
        └── transport.py         # FileTransport：底层 HTTP 传输层（高级用户）
```

> **注意**：`openlist/cli/` 子包（`app.py`、`theme.py`、`commands/file.py`、`commands/server.py` 及其 `__init__.py`）以及根目录的 `cli_temp_test.py` 不在本文档覆盖范围内。

---

## 1. `openlist/__init__.py` — 客户端入口

库的统一入口模块，导出顶层公开 API。

**模块公开常量**：

```python
__all__ = [
    "Client",
    # 文件系统
    "AsyncFileSystem",
    "SyncFileSystem",
    "RemotePath",
    "SyncRemotePath",
    # 模型
    "RenameItem",
    "FileInfo",
    "DirectoryListing",
    "UploadOptions",
]
```

---

### 类 `Client`

> Client 实例的入口（异步版本）。集成认证（`auth`）、用户管理（`user`）、文件系统（`fs`）三大服务，并持有共享上下文（`context`）。支持 JWT 自动刷新和异步上下文管理器（`async with`）。

#### 构造方法

```python
Client(base_url: str, auto_refresh: bool = True)
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `base_url` | `str` | 是 | — | OpenList 服务器地址 |
| `auto_refresh` | `bool` | 否 | `True` | 是否在 token 过期前自动刷新 |

#### 实例属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `context` | `Context` | 客户端运行时共享上下文（持有 base_url、auth_token、httpx_client 等） |
| `auth` | `Authentication` | 认证服务实例（登录/登出） |
| `user` | `UserMe` | 当前用户管理服务（附带 `.sshkey` 子服务） |
| `fs` | `AsyncFileSystem` | 异步文件系统服务实例 |
| `_auto_refresh` | `bool` | 是否启用自动刷新（私有） |
| `_refresh_task` | `asyncio.Task \| None` | 自动刷新后台任务（私有） |
| `_stop_refresh` | `asyncio.Event` | 停止自动刷新的事件信号（私有） |

#### 方法

##### `path(self, path: str = "/") -> RemotePath`

创建远程路径对象。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 否 | `"/"` | 路径字符串 |

**返回**：`RemotePath` 对象，用于 pathlib 风格的文件操作。

##### `get_token(self) -> str`

*返回当前 context 中保存的认证 token。*

**返回**：`str` — 当前 JWT 认证令牌。

##### `async login(self, username: str, password: str, otp_key: str = None) -> "Client"`

登录到服务器，将 token 存入 context，并根据 `auto_refresh` 配置启动后台自动刷新任务。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `username` | `str` | 是 | — | 用户名 |
| `password` | `str` | 是 | — | 密码（明文，内部会加盐哈希） |
| `otp_key` | `str \| None` | 否 | `None` | OTP 双因素认证密钥 |

**返回**：`Client`（自身，支持链式调用）。

##### `async logout(self) -> "Client"`

登出并使 JWT 失效，停止自动刷新任务。

**返回**：`Client`（自身）。

##### `async close(self) -> None`

关闭 HTTP 客户端连接。会先执行登出。

#### 异步上下文管理器

| 方法 | 签名 | 说明 |
|------|------|------|
| `__aenter__` | `async __aenter__(self) -> "Client"` | 进入异步上下文，返回自身 |
| `__aexit__` | `async __aexit__(self, exc_type, exc_val, exc_tb) -> None` | 退出上下文时自动调用 `close()` |

#### 示例

```python
import asyncio
from openlist import Client

async def main():
    # 方式 1：手动管理
    client = Client("https://your-server.com")
    await client.login("username", "password")
    user_info = await client.user.me()
    await client.close()

    # 方式 2：异步上下文管理器（推荐）
    async with Client("https://your-server.com") as client:
        await client.login("username", "password")
        print(await client.get_token())

asyncio.run(main())
```

---

## 2. `openlist/context.py` — 会话上下文

---

### 类 `Context`（`@dataclass`）

> 客户端共享上下文数据类，承载所有服务实例共用的运行时状态（服务器地址、认证 token、HTTP 客户端等）。

#### 字段（实例属性）

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `base_url` | `str` | — | 服务器地址（必填） |
| `auth_token` | `str` | — | 认证令牌（必填，未登录时为 `None`） |
| `httpx_client` | `httpx.AsyncClient` | — | HTTP 异步客户端（必填） |
| `auth_method` | `Callable \| None` | `None` | 认证方法（用于自动刷新时回调） |
| `auth_params` | `dict \| None` | `None` | 认证参数（用于自动刷新时回调） |

#### 说明

该类为纯数据类，无自定义方法。由 `Client.__init__` 创建，并传递给所有服务实例共享。

---

## 3. `openlist/data_types.py` — 用户/认证模型

> 包含用户、认证相关的 Pydantic 模型。文件系统相关模型请使用 `models.file` 模块。

所有类均继承 `pydantic.BaseModel`，无自定义方法（仅字段定义）。

---

### 类 `SimpleLogin(BaseModel)`

> 登录凭据。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `username` | `str` | —（必填） | 用户名 |
| `password` | `str` | —（必填） | 密码 |
| `otp_key` | `str \| None` | `None` | OTP 密钥 |

---

### 类 `UserInfo(BaseModel)`

> 用户信息模型。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `id` | `int` | —（必填） | 用户 ID |
| `username` | `str` | —（必填） | 用户名 |
| `password` | `str` | —（必填） | 密码 |
| `base_path` | `str` | —（必填） | 基础路径 |
| `role` | `int` | —（必填） | 角色 |
| `disabled` | `bool` | —（必填） | 是否禁用 |
| `permission` | `int` | —（必填） | 权限 |
| `sso_id` | `str` | —（必填） | SSO ID |
| `otp` | `bool` | —（必填） | 是否启用 OTP |

---

### 类 `TokenPayload(BaseModel)`

> JWT Token 载荷模型。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `exp` | `int` | —（必填） | 过期时间戳 |
| `iat` | `int` | —（必填） | 签发时间戳 |
| `nbf` | `int` | —（必填） | 生效时间戳 |
| `username` | `str` | —（必填） | 用户名 |
| `pwd_ts` | `int` | —（必填） | 密码时间戳 |

---

### 类 `SSHKey(BaseModel)`

> SSH 密钥对象。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `id` | `int` | —（必填） | 密钥 ID |
| `name` | `str` | —（必填） | 密钥名称 |
| `public_key` | `str` | —（必填） | 公钥内容 |
| `created_at` | `str` | —（必填） | 创建时间 |

---

### 类 `UserListResult(BaseModel)`

> 用户列表分页响应。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `content` | `list[UserInfo]` | —（必填） | 用户列表 |
| `total` | `int` | —（必填） | 总用户数 |

---

## 4. `openlist/exceptions.py` — 异常体系

> OpenList 异常定义。所有异常均继承自 `OpenListError`（后者继承自 `Exception`），构成层次化异常体系。

> **注意**：本模块的 `FileNotFoundError` 与 `FileExistsError` 会覆盖 Python 内置的同名异常，并在整个库中导入使用。

完整层级见 [异常层级速查图](#异常层级速查图)。

---

### 类 `OpenListError(Exception)`

> OpenList 所有异常的基类。

```python
OpenListError(message: str, details: dict[str, Any] | None = None)
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `message` | `str` | 是 | — | 错误消息 |
| `details` | `dict[str, Any] \| None` | 否 | `None` | 额外错误详情 |

**实例属性**：`message: str`、`details: dict[str, Any]`

**重写方法**：`__str__(self) -> str`（返回 `message`）。

---

### 类 `NetworkError(OpenListError)`

> 网络通信错误。

```python
NetworkError(
    message: str = "Network communication failed",
    status_code: int | None = None,
    details: dict[str, Any] | None = None,
)
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `message` | `str` | 否 | `"Network communication failed"` | 错误消息 |
| `status_code` | `int \| None` | 否 | `None` | HTTP 状态码 |
| `details` | `dict[str, Any] \| None` | 否 | `None` | 额外错误详情 |

**新增实例属性**：`status_code: int | None`

---

### 类 `AuthenticationError(OpenListError)`

> 认证失败。

```python
AuthenticationError(
    message: str = "Authentication failed",
    details: dict[str, Any] | None = None,
)
```

---

### 类 `UnexpectedResponseError(NetworkError)`

> 非预期的响应状态码。

```python
UnexpectedResponseError(
    status_code: int,
    message: str = "",
    details: dict[str, Any] | None = None,
)
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `status_code` | `int` | 是 | — | HTTP 状态码 |
| `message` | `str` | 否 | `""` | 错误消息（会追加到状态码描述后） |
| `details` | `dict[str, Any] \| None` | 否 | `None` | 额外错误详情 |

> 内部会自动构造形如 `"Unexpected response code: {status_code} - {message}"` 的消息。

---

### 类 `FileSystemError(OpenListError)`

> 文件系统操作错误基类。

```python
FileSystemError(
    message: str,
    path: str | None = None,
    details: dict[str, Any] | None = None,
)
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `message` | `str` | 是 | — | 错误消息 |
| `path` | `str \| None` | 否 | `None` | 相关路径 |
| `details` | `dict[str, Any] \| None` | 否 | `None` | 额外错误详情 |

**新增实例属性**：`path: str | None`

**重写方法**：`__str__(self) -> str`（若有 path 则返回 `"{message}: '{path}'"`）。

---

### 类 `FileNotFoundError(FileSystemError)`

> 文件或目录不存在。

```python
FileNotFoundError(
    path: str,
    message: str = "File or directory not found",
    details: dict[str, Any] | None = None,
)
```

---

### 类 `FileExistsError(FileSystemError)`

> 文件或目录已存在。

```python
FileExistsError(
    path: str,
    message: str = "File or directory already exists",
    details: dict[str, Any] | None = None,
)
```

---

### 类 `PermissionDeniedError(FileSystemError)`

> 权限不足。

```python
PermissionDeniedError(
    path: str | None = None,
    message: str = "Permission denied",
    details: dict[str, Any] | None = None,
)
```

> `path` 可选（认证类权限错误可能无具体路径）。

---

### 类 `NotADirectoryError(FileSystemError)`

> 期望目录但不是目录。

```python
NotADirectoryError(
    path: str,
    message: str = "Not a directory",
    details: dict[str, Any] | None = None,
)
```

---

### 类 `IsADirectoryError(FileSystemError)`

> 期望文件但是目录。

```python
IsADirectoryError(
    path: str,
    message: str = "Is a directory",
    details: dict[str, Any] | None = None,
)
```

---

### 类 `InvalidPathError(FileSystemError)`

> 无效的路径格式。

```python
InvalidPathError(
    path: str,
    message: str = "Invalid path format",
    details: dict[str, Any] | None = None,
)
```

---

### 类 `OperationError(FileSystemError)`

> 文件操作执行失败。

```python
OperationError(
    operation: str,
    path: str | None = None,
    message: str = "Operation failed",
    details: dict[str, Any] | None = None,
)
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `operation` | `str` | 是 | — | 操作名称 |
| `path` | `str \| None` | 否 | `None` | 相关路径 |
| `message` | `str` | 否 | `"Operation failed"` | 错误消息 |
| `details` | `dict[str, Any] \| None` | 否 | `None` | 额外错误详情 |

**新增实例属性**：`operation: str`

> 内部会构造形如 `"{operation}: {message}"` 的完整消息。

---

## 5. `openlist/utils.py` — 工具函数

> OpenList 工具函数模块。提供时间转换和签名生成等实用工具函数。

### 类型别名

#### `TimeLike: TypeAlias = Union[datetime, date, str, Real]`

> 时间类型别名，支持 `datetime`、`date`、ISO 格式字符串或数值时间戳。

定义：`TimeLike = Union[datetime, date, str, Real]`

---

### 函数 `to_utc_timestamp(t: TimeLike) -> int`

> 将多种时间表示形式转换为 UTC Unix 时间戳。

**支持以下输入类型**：
- 数值类型（`int`/`float`）：直接作为时间戳返回
- ISO 8601 格式字符串：解析后转换
- `datetime` 对象：转换为 UTC 时间戳
- `date` 对象：转换为当天 00:00:00 UTC 的时间戳

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `t` | `TimeLike` | 是 | — | 时间表示 |

**返回**：`int` — UTC Unix 时间戳（秒）。

**异常**：
- `ValueError`：字符串格式无法解析为有效时间时抛出。
- `TypeError`：输入类型不受支持时抛出。

**示例**：

```python
>>> to_utc_timestamp(1700000000)
1700000000
>>> to_utc_timestamp("2023-11-14T22:13:20+00:00")
1700000000
>>> from datetime import datetime, timezone
>>> to_utc_timestamp(datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc))
1700000000
```

---

### 函数 `sign(path: str, token: str, expire: TimeLike = 0) -> str`

> 生成 OpenList 资源访问签名。使用 HMAC-SHA256 算法生成 URL 安全的 Base64 编码签名。签名使用原始路径而非 URL 编码路径。

参考算法（NodeJS）：<https://doc.oplist.org/guide/drivers/common#_3-developing-on-your-own>

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 是 | — | 需要签名的资源路径，如 `"/path/to/file.txt"` |
| `token` | `str` | 是 | — | 签名令牌（OpenList 后台「设置 → 其他 → 令牌」获取） |
| `expire` | `TimeLike` | 否 | `0` | 签名过期时间（`0` 表示永不过期） |

**返回**：`str` — 格式为 `"{base64_signature}:{expire_timestamp}"` 的签名字符串。

---

### 函数 `decode_token(token: str) -> TokenPayload`

> *解码 JWT token 并返回 `TokenPayload` 对象（不验证签名）。*

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `token` | `str` | 是 | — | JWT token 字符串 |

**返回**：`TokenPayload` — 解码后的 token 载荷。

---

## 6. `openlist/models/file.py` — 文件系统模型

> 文件系统相关的 Pydantic 模型与 `FileType` 枚举。

---

### 类 `FileType(IntEnum)`

> 文件类型枚举。

| 成员 | 值 | 说明 |
|------|----|------|
| `UNKNOWN` | `0` | 未知类型 |
| `FOLDER` | `1` | 文件夹 |
| `VIDEO` | `2` | 视频 |
| `AUDIO` | `3` | 音频 |
| `TEXT` | `4` | 文本 |
| `IMAGE` | `5` | 图片 |

---

### 类 `HashInfo(BaseModel)`

> 文件哈希信息。配置 `model_config = {"extra": "allow"}`（允许额外字段）。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `md5` | `str \| None` | `None` | MD5 哈希值 |
| `sha1` | `str \| None` | `None` | SHA1 哈希值 |
| `sha256` | `str \| None` | `None` | SHA256 哈希值 |

---

### 类 `StorageInfo(BaseModel)`

> 存储详情。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `driver_name` | `str` | —（必填） | 存储驱动名称 |
| `total_space` | `int` | —（必填） | 总存储空间（字节） |
| `free_space` | `int` | —（必填） | 可用存储空间（字节） |

#### 属性（`@property`）

| 属性 | 签名 | 说明 |
|------|------|------|
| `used_space` | `used_space(self) -> int` | 已使用空间（字节）= `total_space - free_space` |
| `usage_percent` | `usage_percent(self) -> float` | 使用率百分比（0–100）；`total_space` 为 0 时返回 `0.0` |

---

### 类 `FileInfo(BaseModel)`

> 文件或目录信息。表示远程文件系统中的一个文件或目录对象。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `name` | `str` | —（必填） | 文件或目录名称 |
| `path` | `str` | `""` | 完整路径 |
| `size` | `int` | `0` | 文件大小（字节），目录为 0 |
| `is_dir` | `bool` | —（必填） | 是否为目录 |
| `modified` | `datetime` | —（必填） | 最后修改时间 |
| `created` | `datetime` | —（必填） | 创建时间 |
| `id` | `str` | `""` | 对象 ID |
| `sign` | `str` | `""` | 下载认证签名 |
| `thumb` | `str` | `""` | 缩略图 URL |
| `type` | `FileType` | `FileType.UNKNOWN` | 文件类型 |
| `hash_info` | `HashInfo \| None` | `None` | 哈希信息 |
| `storage_info` | `StorageInfo \| None` | `None` | 存储详情 |
| `hashinfo` | `str \| None` | `None` | 原始哈希信息字符串（用于兼容，`exclude=True`） |
| `mount_details` | `dict \| None` | `None` | 原始挂载详情（用于兼容，`exclude=True`） |

#### 属性（`@property`）

| 属性 | 签名 | 说明 |
|------|------|------|
| `suffix` | `suffix(self) -> str` | 文件扩展名（包含点号），如 `".txt"` |
| `stem` | `stem(self) -> str` | 不含扩展名的文件名，如 `"file"` |

#### 字段验证器

| 方法 | 装饰器 | 说明 |
|------|--------|------|
| `validate_type(cls, v)` | `@field_validator("type", mode="before")` + `@classmethod` | 将整数转换为 `FileType` 枚举，无效值降级为 `FileType.UNKNOWN` |

#### 初始化后处理

| 方法 | 说明 |
|------|------|
| `model_post_init(self, __context) -> None` | 解析 `hashinfo` 字符串为 `HashInfo` 对象；解析 `mount_details` 为 `StorageInfo` 对象 |

---

### 类 `DirectoryListing(BaseModel)`

> 目录列表结果。包含目录下的文件列表及相关元信息。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `items` | `list[FileInfo]` | `[]` | 文件/目录列表 |
| `total` | `int` | `0` | 总项目数 |
| `readme` | `str` | `""` | README 内容 |
| `header` | `str` | `""` | 头部内容 |
| `has_write_permission` | `bool` | `False` | 是否有写权限 |
| `provider` | `str` | `""` | 存储提供商名称 |

---

### 类 `UploadOptions(BaseModel)`

> 上传选项配置。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `overwrite` | `bool` | `False` | 是否覆盖已存在的文件 |
| `password` | `str \| None` | `None` | 受保护目录的访问密码 |
| `as_task` | `bool` | `False` | 是否作为后台任务上传 |
| `last_modified` | `int \| None` | `None` | 最后修改时间（秒时间戳） |

---

### 类 `RenameItem(BaseModel)`

> 批量重命名项。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `src_name` | `str` | —（必填） | 源文件名 |
| `new_name` | `str` | —（必填） | 新文件名 |

#### 类方法

##### `from_tuple(cls, item: tuple[str, str]) -> "RenameItem"`（`classmethod`）

> 从元组创建 `RenameItem`。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `item` | `tuple[str, str]` | 是 | — | `(源名, 新名)` 元组 |

**返回**：`RenameItem`。

**示例**：

```python
from openlist import RenameItem

item = RenameItem.from_tuple(("old.txt", "new.txt"))
# 等价于 RenameItem(src_name="old.txt", new_name="new.txt")
```

---

### 类 `ListOptions(BaseModel)`

> 目录列表选项。

| 字段 | 类型 | 默认 | 约束 | 说明 |
|------|------|------|------|------|
| `password` | `str \| None` | `None` | — | 受保护路径的访问密码 |
| `refresh` | `bool` | `False` | — | 是否强制刷新缓存 |
| `page` | `int` | `1` | `ge=1` | 页码（从 1 开始） |
| `per_page` | `int` | `30` | `ge=1, le=100` | 每页数量（1–100） |

---

## 7. `openlist/models/__init__.py` — 模型包导出

> OpenList 数据模型。本模块包含所有 Pydantic 模型定义。

**模块公开常量**：

```python
__all__ = [
    "FileType",
    "FileInfo",
    "DirectoryListing",
    "HashInfo",
    "StorageInfo",
    "UploadOptions",
    "RenameItem",
    "ListOptions",
]
```

---

## 8. `openlist/core/base.py` — 服务基类

---

### 类 `BaseService(ABC)`

> API 服务基类，封装 context 和通用请求逻辑。所有需要访问 API 的服务类都应该继承此类。

> 注意：`AsyncFileSystem`、`SyncFileSystem`、`FileTransport` **不继承** `BaseService`，它们持有 `Context` 并使用各自的传输层。

#### 构造方法

```python
BaseService(context: Context)
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `context` | `Context` | 是 | — | 共享上下文 |

#### 实例属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `context` | `Context` | 共享上下文 |

#### 受保护方法（`_` 前缀，供子类调用）

##### `async _request(self, method: str, endpoint: str, json: dict | None = None, params: dict | None = None, require_auth: bool = True, expected_codes: tuple[int, ...] = (200,)) -> dict`

> 统一的异步请求方法，处理认证和错误。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `method` | `str` | 是 | — | HTTP 方法（GET、POST、PUT、DELETE 等） |
| `endpoint` | `str` | 是 | — | API 端点路径 |
| `json` | `dict \| None` | 否 | `None` | 请求体数据 |
| `params` | `dict \| None` | 否 | `None` | URL 查询参数 |
| `require_auth` | `bool` | 否 | `True` | 是否需要认证头 |
| `expected_codes` | `tuple[int, ...]` | 否 | `(200,)` | 期望的 HTTP 状态码 |

**返回**：`dict` — 响应的 JSON 数据。

**异常**：
- `AuthenticationError`：认证失败（401/403）
- `FileNotFoundError`：资源不存在（404）
- `UnexpectedResponseError`：非预期的状态码
- `NetworkError`：API 返回的业务 `code` 不是 200，或响应不是有效 JSON

##### `async _get(self, endpoint: str, params: dict | None = None, require_auth: bool = True) -> dict`

> *GET 请求的快捷方法，内部调用 `_request("GET", ...)`。*

##### `async _post(self, endpoint: str, json: dict | None = None, require_auth: bool = True) -> dict`

> *POST 请求的快捷方法，内部调用 `_request("POST", ...)`。*

---

## 9. `openlist/core/authentication.py` — 认证服务

---

### 类 `Authentication(BaseService)`

> 用户认证服务。继承 `BaseService`（构造方法 `__init__(self, context: Context)` 由基类提供）。

#### 方法

##### `async login(self, username: str, password: str, otp_key: str = None) -> None`

> 登录并将 token 存入 context。密码会经过加盐 SHA-256 哈希后提交，支持可选 OTP 双因素认证。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `username` | `str` | 是 | — | 用户名 |
| `password` | `str` | 是 | — | 密码（明文） |
| `otp_key` | `str \| None` | 否 | `None` | OTP 密钥 |

**异常**：
- `AuthenticationError`：认证失败（403）
- `UnexpectedResponseError`：其他非 200 状态码
- `NetworkError`：响应中缺少 token 字段

##### `async logout(self) -> None`

> 登出，使 JWT 失效。若无 token 或 token 已过期，则直接返回不发起请求。

---

## 10. `openlist/core/admin.py` — 用户/管理员服务

> 用户管理相关的 API 服务。

---

### 类 `UserMe(BaseService)`

> 当前用户信息。

#### 构造方法

```python
UserMe(context: Context)
```

调用基类 `__init__`，并额外初始化子服务属性。

#### 实例属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `context` | `Context` | 继承自 `BaseService` |
| `sshkey` | `MySSHKey` | 当前用户 SSH 密钥管理子服务 |

#### 方法

##### `async me(self) -> UserInfo`

> 获取当前用户信息（`GET /api/me`）。

**返回**：`UserInfo`。

##### `async update(self, username: str = None, password: str = None, sso_id: str = None) -> None`

> 更新用户信息；会使 JWT 失效，需要重新登录。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `username` | `str \| None` | 否 | `None` | 新用户名（不填则使用当前 token 中的用户名） |
| `password` | `str \| None` | 否 | `None` | 新密码 |
| `sso_id` | `str \| None` | 否 | `None` | SSO ID |

---

### 类 `MySSHKey(BaseService)`

> 当前用户 SSH 密钥管理。继承 `BaseService`。

#### 方法

##### `async add(self, name: str, public_key: str) -> None`

> 添加 SSH 密钥（`POST /api/me/sshkey/add`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `name` | `str` | 是 | — | 密钥名称 |
| `public_key` | `str` | 是 | — | 公钥内容 |

##### `async delete(self, id: int) -> None`

> 删除 SSH 密钥（`POST /api/me/sshkey/delete`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `id` | `int` | 是 | — | 密钥 ID |

##### `async list(self) -> list[SSHKey]`

> 获取 SSH 密钥列表（`GET /api/me/sshkey/list`）。

**返回**：`list[SSHKey]`。

---

### 类 `Admin(BaseService)`

> 管理员。

#### 构造方法

```python
Admin(context: Context)
```

调用基类 `__init__`，并额外初始化子服务属性。

#### 实例属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `context` | `Context` | 继承自 `BaseService` |
| `user` | `User` | 管理员用户管理子服务 |

> `Admin` 类本身无自定义公开方法，仅通过 `user` 属性暴露 `User` 子服务。

---

### 类 `User(BaseService)`

> 管理员用户管理。继承 `BaseService`。**需要管理员 Token**。

#### 方法

##### `async list(self, page: int = 1, per_page: int = 30) -> UserListResult`

> 获取所有用户的分页列表（`GET /api/admin/user/list`，需要管理员 Token）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `page` | `int` | 否 | `1` | 页码 |
| `per_page` | `int` | 否 | `30` | 每页数量 |

**返回**：`UserListResult`。

##### `async get(self, id: int) -> UserInfo`

> 通过 ID 获取特定用户信息（`GET /api/admin/user/get`，需要管理员 Token）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `id` | `int` | 是 | — | 用户 ID |

**返回**：`UserInfo`。

##### `async create(self, username: str, password: str, base_path: str, role: int, permission: int, disabled: bool) -> None`

> 创建用户（`POST /api/admin/user/create`，需要管理员 Token）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `username` | `str` | 是 | — | 用户名 |
| `password` | `str` | 是 | — | 密码 |
| `base_path` | `str` | 是 | — | 基础路径 |
| `role` | `int` | 是 | — | 角色 |
| `permission` | `int` | 是 | — | 权限 |
| `disabled` | `bool` | 是 | — | 是否禁用 |

---

## 11. `openlist/core/file/async_fs.py` — 异步文件系统

---

### 类 `AsyncFileSystem`

> 异步文件系统操作。提供类似标准库 `os`/`shutil` 的语义清晰的文件操作接口。所有方法都是异步的（`async`/`await`）。

#### 构造方法

```python
AsyncFileSystem(context: Context)
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `context` | `Context` | 是 | — | 共享上下文 |

#### 实例属性（私有）

| 属性 | 类型 | 说明 |
|------|------|------|
| `_context` | `Context` | 共享上下文 |
| `_transport` | `FileTransport` | 底层传输层实例 |

#### 类级别别名

| 别名 | 指向 | 说明 |
|------|------|------|
| `makedirs` | `mkdir` | `makedirs` 是 `mkdir` 的别名 |

#### 静态/私有方法

##### `_normalize_path(path: str) -> str`（`staticmethod`，私有）

> 规范化路径为 POSIX 格式（替换反斜杠、规范化、确保以 `/` 开头）。

---

#### 查询操作

##### `async listdir(self, path: str = "/", *, password: str | None = None, refresh: bool = False) -> list[FileInfo]`

> 列出目录下的所有文件和子目录（内部以 `page=1, per_page=100` 拉取）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 否 | `"/"` | 目录路径 |
| `password` | `str \| None` | 否（关键字） | `None` | 受保护目录的密码 |
| `refresh` | `bool` | 否（关键字） | `False` | 是否强制刷新缓存 |

**返回**：`list[FileInfo]`。

##### `async listdir_detail(self, path: str = "/", *, options: ListOptions | None = None) -> DirectoryListing`

> 列出目录内容（包含完整元信息）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 否 | `"/"` | 目录路径 |
| `options` | `ListOptions \| None` | 否（关键字） | `None` | 列表选项 |

**返回**：`DirectoryListing`。

##### `async stat(self, path: str, *, password: str | None = None) -> FileInfo`

> 获取文件或目录的详细信息。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 是 | — | 文件或目录路径 |
| `password` | `str \| None` | 否（关键字） | `None` | 受保护路径的密码 |

**返回**：`FileInfo`。

**异常**：`FileNotFoundError` — 路径不存在。

##### `async exists(self, path: str, *, password: str | None = None) -> bool`

> 检查路径是否存在。

**返回**：`bool` — 存在返回 `True`，否则 `False`。

##### `async is_dir(self, path: str, *, password: str | None = None) -> bool`

> 检查路径是否为目录。

**返回**：`bool` — 是目录返回 `True`；不存在或不是目录返回 `False`。

##### `async is_file(self, path: str, *, password: str | None = None) -> bool`

> 检查路径是否为文件。

**返回**：`bool` — 是文件返回 `True`；不存在或不是文件返回 `False`。

---

#### 目录操作

##### `async mkdir(self, path: str, exist_ok: bool = False) -> None`

> 创建目录（自动创建所有父目录）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 是 | — | 目录路径 |
| `exist_ok` | `bool` | 否 | `False` | 为 `True` 时，目录已存在不抛出异常 |

**异常**：`FileExistsError` — 目录已存在且 `exist_ok=False`。

---

#### 删除操作

##### `async remove(self, path: str) -> None`

> 删除文件或目录。删除文件或空目录；若是非空目录也会被删除。

**异常**：`FileNotFoundError` — 路径不存在。

##### `async unlink(self, path: str) -> None`

> 删除文件。与 `remove()` 功能相同，命名与 `pathlib.Path.unlink()` 一致。

##### `async rmdir(self, path: str) -> None`

> 删除目录。与 `remove()` 功能相同，命名与 `os.rmdir()` 一致。

##### `async remove_many(self, dir_path: str, names: list[str]) -> None`

> 批量删除同一目录下的多个文件/目录。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `dir_path` | `str` | 是 | — | 父目录路径 |
| `names` | `list[str]` | 是 | — | 要删除的文件/目录名列表 |

---

#### 重命名操作

##### `async rename(self, src: str, dst: str) -> None`

> 重命名文件或目录。**注意**：此操作仅支持重命名，不支持移动到其他目录；如果 `dst` 包含路径，将只取其 basename 作为新名称。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `src` | `str` | 是 | — | 源文件/目录完整路径 |
| `dst` | `str` | 是 | — | 新名称或新完整路径（只使用 basename） |

**异常**：`FileNotFoundError` — 源路径不存在。

##### `async rename_many(self, dir_path: str, items: list[RenameItem | tuple[str, str]]) -> None`

> 批量重命名同一目录下的多个文件。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `dir_path` | `str` | 是 | — | 目录路径 |
| `items` | `list[RenameItem \| tuple[str, str]]` | 是 | — | 重命名项列表，每项为 `RenameItem` 或 `(旧名, 新名)` 元组 |

---

#### 复制和移动操作

##### `async copy(self, src: str, dst: str) -> None`

> 复制文件或目录到目标位置。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `src` | `str` | 是 | — | 源文件/目录完整路径 |
| `dst` | `str` | 是 | — | 目标目录路径 |

**异常**：`FileNotFoundError` — 源路径不存在。

##### `async copy_many(self, src_dir: str, dst_dir: str, names: list[str]) -> None`

> 批量复制同一目录下的多个文件/目录。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `src_dir` | `str` | 是 | — | 源目录路径 |
| `dst_dir` | `str` | 是 | — | 目标目录路径 |
| `names` | `list[str]` | 是 | — | 要复制的文件/目录名列表 |

##### `async move(self, src: str, dst: str) -> None`

> 移动文件或目录到目标位置。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `src` | `str` | 是 | — | 源文件/目录完整路径 |
| `dst` | `str` | 是 | — | 目标目录路径 |

**异常**：`FileNotFoundError` — 源路径不存在。

##### `async move_many(self, src_dir: str, dst_dir: str, names: list[str]) -> None`

> 批量移动同一目录下的多个文件/目录。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `src_dir` | `str` | 是 | — | 源目录路径 |
| `dst_dir` | `str` | 是 | — | 目标目录路径 |
| `names` | `list[str]` | 是 | — | 要移动的文件/目录名列表 |

##### `async recursive_move(self, src: str, dst: str) -> None`

> 递归移动目录（保留目录结构）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `src` | `str` | 是 | — | 源目录路径 |
| `dst` | `str` | 是 | — | 目标目录路径 |

---

#### 文件读写操作

##### `async write_bytes(self, path: str, data: bytes | Iterator[bytes] | AsyncIterator[bytes], *, options: UploadOptions | None = None) -> None`

> 写入字节数据到文件。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 是 | — | 目标文件路径 |
| `data` | `bytes \| Iterator[bytes] \| AsyncIterator[bytes]` | 是 | — | 文件内容（bytes 或迭代器） |
| `options` | `UploadOptions \| None` | 否（关键字） | `None` | 上传选项 |

**异常**：`FileExistsError` — 文件已存在且 `overwrite=False`。

##### `async upload_file(self, local_path: str, remote_path: str, *, chunk_size: int = 1024 * 1024, options: UploadOptions | None = None) -> None`

> 从本地文件上传到远程。使用分片流式上传，适合大文件。未指定 `last_modified` 时使用本地文件修改时间。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `local_path` | `str` | 是 | — | 本地文件路径 |
| `remote_path` | `str` | 是 | — | 远程目标路径 |
| `chunk_size` | `int` | 否（关键字） | `1048576`（1MB） | 分片大小（字节） |
| `options` | `UploadOptions \| None` | 否（关键字） | `None` | 上传选项 |

---

## 12. `openlist/core/file/sync_fs.py` — 同步文件系统

> 同步文件系统模块。提供与 `AsyncFileSystem` 完全相同的 API，但所有方法均为同步阻塞调用。

### 模块级私有函数

| 函数 | 签名 | 说明 |
|------|------|------|
| `_get_or_create_event_loop` | `_get_or_create_event_loop() -> asyncio.AbstractEventLoop` | 获取或创建事件循环 |
| `_run_sync` | `_run_sync(coro)` | 在同步上下文中运行协程；无运行循环时用 `asyncio.run()`，在异步上下文中则用线程池 |

---

### 类 `SyncFileSystem`

> 同步文件系统操作。提供与 `AsyncFileSystem` 相同的 API，但所有方法都是同步的。适用于不需要异步的场景。

> **实现说明**：内部持有 `_async_fs: AsyncFileSystem` 实例，每个同步方法通过 `_run_sync()` 桥接到对应的异步实现。因此方法签名与 `AsyncFileSystem` 一一对应，仅去掉 `async` 关键字，且 `write_bytes` 的 `data` 仅支持 `bytes | Iterator[bytes]`（不支持异步迭代器）。

#### 构造方法

```python
SyncFileSystem(context: Context)
```

#### 实例属性（私有）

| 属性 | 类型 | 说明 |
|------|------|------|
| `_context` | `Context` | 共享上下文 |
| `_async_fs` | `AsyncFileSystem` | 内部委托的异步文件系统实例 |

#### 类级别别名

| 别名 | 指向 |
|------|------|
| `makedirs` | `mkdir` |

#### 公开方法

> 以下方法的签名、参数、返回值、异常与 `AsyncFileSystem` 中同名方法**完全一致**（去掉 `async`），此处不再赘述，请参见 [§11 AsyncFileSystem](#11-openlistcorefileasync_fspy--异步文件系统) 对应章节：

- `listdir(self, path: str = "/", *, password: str | None = None, refresh: bool = False) -> list[FileInfo]`
- `listdir_detail(self, path: str = "/", *, options: ListOptions | None = None) -> DirectoryListing`
- `stat(self, path: str, *, password: str | None = None) -> FileInfo`
- `exists(self, path: str, *, password: str | None = None) -> bool`
- `is_dir(self, path: str, *, password: str | None = None) -> bool`
- `is_file(self, path: str, *, password: str | None = None) -> bool`
- `mkdir(self, path: str, exist_ok: bool = False) -> None`
- `remove(self, path: str) -> None`
- `unlink(self, path: str) -> None`
- `rmdir(self, path: str) -> None`
- `remove_many(self, dir_path: str, names: list[str]) -> None`
- `rename(self, src: str, dst: str) -> None`
- `rename_many(self, dir_path: str, items: list[RenameItem | tuple[str, str]]) -> None`
- `copy(self, src: str, dst: str) -> None`
- `copy_many(self, src_dir: str, dst_dir: str, names: list[str]) -> None`
- `move(self, src: str, dst: str) -> None`
- `move_many(self, src_dir: str, dst_dir: str, names: list[str]) -> None`
- `recursive_move(self, src: str, dst: str) -> None`
- `write_bytes(self, path: str, data: bytes | Iterator[bytes], *, options: UploadOptions | None = None) -> None`
- `upload_file(self, local_path: str, remote_path: str, *, chunk_size: int = 1024 * 1024, options: UploadOptions | None = None) -> None`

---

## 13. `openlist/core/file/path.py` — 路径对象

> `RemotePath` 和 `SyncRemotePath`：按 `pathlib.Path` 风格设计的远程路径对象。路径属性（如 `parent`、`name`）是纯本地计算，不涉及网络请求；文件操作（如 `exists`、`mkdir`）会触发 API 调用。

---

### 类 `RemotePath`

> 远程路径对象（类似 `pathlib.Path`）。

**`__slots__ = ("_fs", "_path", "_is_async")`**

#### 构造方法

```python
RemotePath(fs: Union["AsyncFileSystem", "SyncFileSystem"], path: str = "/")
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `fs` | `AsyncFileSystem \| SyncFileSystem` | 是 | — | 文件系统服务实例 |
| `path` | `str` | 否 | `"/"` | 路径字符串 |

#### 实例属性（私有，通过 `__slots__` 约束）

| 属性 | 类型 | 说明 |
|------|------|------|
| `_fs` | `AsyncFileSystem \| SyncFileSystem` | 关联的文件系统服务 |
| `_path` | `str` | 规范化后的路径字符串 |
| `_is_async` | `bool` | 是否为异步文件系统（通过 `hasattr(fs, "_transport")` 判定） |

#### 静态/私有方法

##### `_normalize(path: str) -> str`（`staticmethod`，私有）

> 规范化路径（替换反斜杠、规范化、确保以 `/` 开头）。

---

#### 路径属性（`@property`，纯本地计算，不涉及网络）

| 属性 | 签名 | 说明 |
|------|------|------|
| `path` | `path(self) -> str` | 完整路径字符串 |
| `name` | `name(self) -> str` | 文件或目录名称（根路径返回 `"/"`） |
| `stem` | `stem(self) -> str` | 不含扩展名的文件名 |
| `suffix` | `suffix(self) -> str` | 文件扩展名（包含点号） |
| `suffixes` | `suffixes(self) -> list[str]` | 所有扩展名列表，如 `[".tar", ".gz"]` |
| `parent` | `parent(self) -> "RemotePath"` | 父目录路径 |
| `parents` | `parents(self) -> tuple["RemotePath", ...]` | 所有祖先目录路径（含根） |
| `parts` | `parts(self) -> tuple[str, ...]` | 路径各部分，如 `("/", "data", "file.txt")` |

---

#### 路径操作方法（纯本地计算，不涉及网络）

##### `joinpath(self, *parts: str) -> "RemotePath"`

> 连接多个路径部分。

**示例**：`root.joinpath("a", "b", "c.txt")`

##### `with_name(self, name: str) -> "RemotePath"`

> 返回具有不同名称的新路径。根路径会抛出 `ValueError`。

##### `with_stem(self, stem: str) -> "RemotePath"`

> 返回具有不同 stem 的新路径（保留原扩展名）。

##### `with_suffix(self, suffix: str) -> "RemotePath"`

> 返回具有不同后缀的新路径。`suffix` 必须以 `.` 开头或为空，否则抛出 `ValueError`。

##### `is_absolute(self) -> bool`

> 是否为绝对路径（远程路径总是绝对路径，恒返回 `True`）。

##### `is_relative_to(self, other: Union[str, "RemotePath"]) -> bool`

> 检查是否相对于另一路径。

##### `relative_to(self, other: Union[str, "RemotePath"]) -> str`

> 获取相对于另一路径的相对路径。不构成相对关系时抛出 `ValueError`；相同时返回 `"."`。

---

#### 文件操作方法（异步，触发网络请求）

##### `async exists(self) -> bool`

> 检查路径是否存在。

##### `async is_dir(self) -> bool`

> 检查是否为目录。

##### `async is_file(self) -> bool`

> 检查是否为文件。

##### `async stat(self) -> FileInfo`

> 获取文件/目录信息。

**返回**：`FileInfo`。

##### `async iterdir(self) -> AsyncIterator["RemotePath"]`

> 遍历目录内容。**异步生成器**，使用 `async for` 迭代。

**Yields**：目录中每个项目的 `RemotePath` 对象。

##### `async mkdir(self, exist_ok: bool = False) -> None`

> 创建目录。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `exist_ok` | `bool` | 否 | `False` | 目录已存在时不抛出异常 |

##### `async rmdir(self) -> None`

> 删除目录。

##### `async unlink(self) -> None`

> 删除文件。

##### `async remove(self) -> None`

> 删除文件或目录。

##### `async read_bytes(self) -> bytes`

> 读取文件内容。**当前 API 不支持直接读取**，始终抛出 `NotImplementedError`。建议使用 `stat()` 返回的下载 URL 获取文件内容。

**异常**：`NotImplementedError`。

##### `async write_bytes(self, data: bytes, *, overwrite: bool = False) -> None`

> 写入文件内容。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `data` | `bytes` | 是 | — | 文件内容 |
| `overwrite` | `bool` | 否（关键字） | `False` | 是否覆盖已存在的文件 |

##### `async rename(self, target: Union[str, "RemotePath"]) -> "RemotePath"`

> 重命名文件或目录。**注意**：只支持同目录下重命名，不支持移动到其他目录。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `target` | `str \| RemotePath` | 是 | — | 新名称或新路径 |

**返回**：`RemotePath` — 新路径对象。

##### `async copy_to(self, target: Union[str, "RemotePath"]) -> "RemotePath"`

> 复制到目标位置。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `target` | `str \| RemotePath` | 是 | — | 目标目录路径 |

**返回**：`RemotePath` — 目标位置的对象。

##### `async move_to(self, target: Union[str, "RemotePath"]) -> "RemotePath"`

> 移动到目标位置。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `target` | `str \| RemotePath` | 是 | — | 目标目录路径 |

**返回**：`RemotePath` — 目标位置的对象。

---

#### 魔术方法

| 方法 | 说明 |
|------|------|
| `__truediv__(self, other: str) -> "RemotePath"` | `/` 运算符连接路径：`path / "sub" / "file.txt"` |
| `__rtruediv__(self, other: str) -> "RemotePath"` | 支持字符串在左侧 |
| `__str__(self) -> str` | 返回路径字符串 |
| `__repr__(self) -> str` | 返回 `RemotePath('/path')` 形式 |
| `__eq__(self, other: object) -> bool` | 相等比较（支持 `RemotePath` 与 `str`） |
| `__hash__(self) -> int` | 哈希值（基于路径字符串） |
| `__lt__(self, other: "RemotePath") -> bool` | 小于比较 |
| `__le__(self, other: "RemotePath") -> bool` | 小于等于比较 |
| `__gt__(self, other: "RemotePath") -> bool` | 大于比较 |
| `__ge__(self, other: "RemotePath") -> bool` | 大于等于比较 |

---

### 类 `SyncRemotePath`

> 同步版本的远程路径对象。与 `RemotePath` 相同的 API，但所有文件操作都是同步的。

**`__slots__ = ("_fs", "_path")`**

#### 构造方法

```python
SyncRemotePath(fs: "SyncFileSystem", path: str = "/")
```

#### 实例属性（私有）

| 属性 | 类型 | 说明 |
|------|------|------|
| `_fs` | `SyncFileSystem` | 关联的同步文件系统服务 |
| `_path` | `str` | 规范化后的路径字符串 |

#### 静态/私有方法

##### `_normalize(path: str) -> str`（`staticmethod`，私有）

> 规范化路径。逻辑与 `RemotePath._normalize` 相同。

#### 路径属性（`@property`）

> 与 `RemotePath` 同名属性一一对应，返回类型为 `SyncRemotePath`：

- `path(self) -> str`
- `name(self) -> str`
- `stem(self) -> str`
- `suffix(self) -> str`
- `suffixes(self) -> list[str]`
- `parent(self) -> "SyncRemotePath"`
- `parents(self) -> tuple["SyncRemotePath", ...]`
- `parts(self) -> tuple[str, ...]`

#### 路径操作方法

> 与 `RemotePath` 对应方法逻辑一致，返回 `SyncRemotePath`：

- `joinpath(self, *parts: str) -> "SyncRemotePath"`
- `with_name(self, name: str) -> "SyncRemotePath"`
- `with_stem(self, stem: str) -> "SyncRemotePath"`
- `with_suffix(self, suffix: str) -> "SyncRemotePath"`
- `is_absolute(self) -> bool`
- `is_relative_to(self, other: Union[str, "SyncRemotePath"]) -> bool`
- `relative_to(self, other: Union[str, "SyncRemotePath"]) -> str`

#### 文件操作方法（同步）

> 与 `RemotePath` 对应方法语义一致，区别在于返回值不再是协程（直接返回结果），`iterdir` 返回普通迭代器而非异步生成器：

| 方法 | 签名 | 说明 |
|------|------|------|
| `exists` | `exists(self) -> bool` | 检查路径是否存在 |
| `is_dir` | `is_dir(self) -> bool` | 检查是否为目录 |
| `is_file` | `is_file(self) -> bool` | 检查是否为文件 |
| `stat` | `stat(self) -> FileInfo` | 获取文件/目录信息 |
| `iterdir` | `iterdir(self) -> Iterator["SyncRemotePath"]` | 遍历目录内容（同步生成器） |
| `mkdir` | `mkdir(self, exist_ok: bool = False) -> None` | 创建目录 |
| `rmdir` | `rmdir(self) -> None` | 删除目录 |
| `unlink` | `unlink(self) -> None` | 删除文件 |
| `remove` | `remove(self) -> None` | 删除文件或目录 |
| `read_bytes` | `read_bytes(self) -> bytes` | 读取文件内容（当前不支持，抛出 `NotImplementedError`） |
| `write_bytes` | `write_bytes(self, data: bytes, *, overwrite: bool = False) -> None` | 写入文件内容 |
| `rename` | `rename(self, target: Union[str, "SyncRemotePath"]) -> "SyncRemotePath"` | 重命名文件或目录 |
| `copy_to` | `copy_to(self, target: Union[str, "SyncRemotePath"]) -> "SyncRemotePath"` | 复制到目标位置 |
| `move_to` | `move_to(self, target: Union[str, "SyncRemotePath"]) -> "SyncRemotePath"` | 移动到目标位置 |

#### 魔术方法

> 与 `RemotePath` 相同，**额外支持**与 `RemotePath` 实例跨类型比较：

`__truediv__`、`__rtruediv__`、`__str__`、`__repr__`、`__eq__`、`__hash__`、`__lt__`、`__le__`、`__gt__`、`__ge__`。

> 其中 `__eq__`/`__lt__`/`__le__`/`__gt__`/`__ge__` 的 `other` 参数既接受 `SyncRemotePath` 也接受 `RemotePath`。

---

## 14. `openlist/core/file/transport.py` — 传输层

> 文件系统 API 传输层。负责纯粹的 HTTP 通信。

> **定位说明**：`FileTransport` 是面向高级用户的底层接口，普通用户应使用 `AsyncFileSystem`/`SyncFileSystem`。其内部方法虽以非下划线开头，但属于传输层实现细节。

### 模块级私有函数

| 函数 | 签名 | 说明 |
|------|------|------|
| `_map_error_to_exception` | `_map_error_to_exception(code: int, message: str, path: str \| None = None) -> Exception` | 将 API 错误码/消息映射为对应的异常类型 |
| `_async_iter_from_sync` | `async _async_iter_from_sync(sync_iter: Iterator[bytes]) -> AsyncIterator[bytes]` | 将同步迭代器转换为异步迭代器 |

---

### 类 `FileTransport`

> 文件系统 API 传输层。

**职责**：
- 执行 HTTP 请求
- 处理响应状态码
- 将错误映射为异常
- 返回原始响应数据（`dict`）

#### 构造方法

```python
FileTransport(context: Context)
```

#### 实例属性（私有）

| 属性 | 类型 | 说明 |
|------|------|------|
| `_context` | `Context` | 共享上下文 |

#### 私有属性（`@property`）

| 属性 | 签名 | 说明 |
|------|------|------|
| `_client` | `_client(self) -> httpx.AsyncClient` | 底层 HTTP 客户端 |
| `_auth_token` | `_auth_token(self) -> str` | 当前认证 token |

#### 私有方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `_get_headers` | `_get_headers(self) -> dict[str, str]` | 获取带认证的请求头 |
| `_request` | `async _request(self, method: str, endpoint: str, *, json_data: dict \| None = None, params: dict \| None = None, path_hint: str \| None = None) -> dict[str, Any]` | 执行请求并处理响应，返回响应 `data` 字段 |
| `_post` | `async _post(self, endpoint: str, json_data: dict \| None = None, path_hint: str \| None = None) -> dict[str, Any]` | POST 请求快捷方法 |
| `_get` | `async _get(self, endpoint: str, params: dict \| None = None, path_hint: str \| None = None) -> dict[str, Any]` | GET 请求快捷方法 |

#### 公开异步方法

##### `async list_directory(self, path: str, *, password: str | None = None, refresh: bool = False, page: int = 1, per_page: int = 30) -> dict[str, Any]`

> 列出目录内容（`POST /api/fs/list`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 是 | — | 目录路径 |
| `password` | `str \| None` | 否（关键字） | `None` | 受保护目录密码 |
| `refresh` | `bool` | 否（关键字） | `False` | 是否强制刷新缓存 |
| `page` | `int` | 否（关键字） | `1` | 页码 |
| `per_page` | `int` | 否（关键字） | `30` | 每页数量 |

**返回**：`dict[str, Any]` — 原始响应 `data` 字段。

##### `async get_info(self, path: str, *, password: str | None = None) -> dict[str, Any]`

> 获取文件/目录信息（`POST /api/fs/get`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 是 | — | 路径 |
| `password` | `str \| None` | 否（关键字） | `None` | 受保护路径密码 |

**返回**：`dict[str, Any]`。

##### `async remove(self, dir_path: str, names: list[str]) -> None`

> 删除文件或目录（`POST /api/fs/remove`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `dir_path` | `str` | 是 | — | 父目录路径 |
| `names` | `list[str]` | 是 | — | 要删除的名称列表 |

##### `async rename(self, path: str, new_name: str) -> None`

> 重命名文件或目录（`POST /api/fs/rename`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 是 | — | 源路径 |
| `new_name` | `str` | 是 | — | 新名称 |

##### `async batch_rename(self, dir_path: str, rename_objects: list[dict[str, str]]) -> None`

> 批量重命名（`POST /api/fs/batch_rename`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `dir_path` | `str` | 是 | — | 目录路径 |
| `rename_objects` | `list[dict[str, str]]` | 是 | — | 重命名对象列表，每项含 `src_name` 和 `new_name` 键 |

##### `async mkdir(self, path: str) -> None`

> 创建目录（`POST /api/fs/mkdir`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 是 | — | 目录路径 |

##### `async copy(self, src_dir: str, dst_dir: str, names: list[str]) -> None`

> 复制文件或目录（`POST /api/fs/copy`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `src_dir` | `str` | 是 | — | 源目录路径 |
| `dst_dir` | `str` | 是 | — | 目标目录路径 |
| `names` | `list[str]` | 是 | — | 文件/目录名列表 |

##### `async move(self, src_dir: str, dst_dir: str, names: list[str]) -> None`

> 移动文件或目录（`POST /api/fs/move`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `src_dir` | `str` | 是 | — | 源目录路径 |
| `dst_dir` | `str` | 是 | — | 目标目录路径 |
| `names` | `list[str]` | 是 | — | 文件/目录名列表 |

##### `async recursive_move(self, src_dir: str, dst_dir: str) -> None`

> 递归移动目录（`POST /api/fs/recursive_move`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `src_dir` | `str` | 是 | — | 源目录路径 |
| `dst_dir` | `str` | 是 | — | 目标目录路径 |

##### `async upload(self, path: str, content: bytes | AsyncIterator[bytes] | Iterator[bytes], *, last_modified: int | None = None, overwrite: bool = False, password: str | None = None, as_task: bool = False) -> None`

> 上传文件（`PUT /api/fs/put`）。同步迭代器会自动转换为异步迭代器。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `path` | `str` | 是 | — | 目标路径（包含文件名） |
| `content` | `bytes \| AsyncIterator[bytes] \| Iterator[bytes]` | 是 | — | 文件内容（bytes 或迭代器） |
| `last_modified` | `int \| None` | 否（关键字） | `None` | 最后修改时间戳（秒） |
| `overwrite` | `bool` | 否（关键字） | `False` | 是否覆盖已存在的文件 |
| `password` | `str \| None` | 否（关键字） | `None` | 受保护目录的密码 |
| `as_task` | `bool` | 否（关键字） | `False` | 是否作为后台任务 |

---

## 包导出速查

### `openlist/__init__.py`

```python
__all__ = [
    "Client", "AsyncFileSystem", "SyncFileSystem",
    "RemotePath", "SyncRemotePath",
    "RenameItem", "FileInfo", "DirectoryListing", "UploadOptions",
]
```

### `openlist/models/__init__.py`

```python
__all__ = [
    "FileType", "FileInfo", "DirectoryListing", "HashInfo",
    "StorageInfo", "UploadOptions", "RenameItem", "ListOptions",
]
```

### `openlist/core/__init__.py`

```python
__all__ = [
    "BaseService",
    "AsyncFileSystem", "SyncFileSystem",
    "RemotePath", "SyncRemotePath",
    "FileTransport",
]
```

### `openlist/core/file/__init__.py`

```python
__all__ = [
    "AsyncFileSystem", "SyncFileSystem",
    "RemotePath", "SyncRemotePath",
    "FileTransport",
]
```

---

## 使用示例合集

> 以下示例基于库的真实可用 API（与 README 一致），均采用 `async with Client(...) as client:` 模式。

### 示例 1：函数式文件系统操作（os/shutil 风格）

```python
import asyncio
from openlist import Client

async def main():
    async with Client("https://your-server.com") as client:
        await client.login("username", "password")
        fs = client.fs

        # 列出目录
        files = await fs.listdir("/data")
        for f in files:
            print(f"{f.name} - {'目录' if f.is_dir else '文件'}")

        # 获取文件信息
        info = await fs.stat("/data/file.txt")
        print(f"大小: {info.size}, 修改时间: {info.modified}")

        # 检查路径
        if await fs.exists("/data/file.txt"):
            print("文件存在")

        # 创建目录
        await fs.mkdir("/data/new_folder", exist_ok=True)

        # 上传文件
        await fs.write_bytes("/data/hello.txt", b"Hello, World!")

        # 从本地上传（分片流式）
        await fs.upload_file("local_file.zip", "/data/remote_file.zip")

        # 复制、移动、删除
        await fs.copy("/data/file.txt", "/backup/")
        await fs.move("/data/old.txt", "/archive/")
        await fs.remove("/data/temp.txt")

asyncio.run(main())
```

### 示例 2：pathlib 风格文件操作

```python
import asyncio
from openlist import Client

async def main():
    async with Client("https://your-server.com") as client:
        await client.login("username", "password")

        # 创建路径对象
        root = client.path("/data")

        # 路径操作（不涉及网络）
        config = root / "config" / "settings.json"
        print(f"路径: {config}")           # /data/config/settings.json
        print(f"名称: {config.name}")      # settings.json
        print(f"父目录: {config.parent}")  # /data/config
        print(f"扩展名: {config.suffix}")  # .json

        # 文件操作（网络请求）
        if await config.exists():
            info = await config.stat()
            print(f"大小: {info.size} bytes")

        # 遍历目录
        async for item in root.iterdir():
            is_dir = await item.is_dir()
            print(f"  {item.name} {'[DIR]' if is_dir else ''}")

        # 创建目录
        new_dir = root / "new_folder"
        await new_dir.mkdir(exist_ok=True)

        # 写入文件
        file = new_dir / "hello.txt"
        await file.write_bytes(b"Hello!")

        # 重命名
        renamed = await file.rename("greeting.txt")

        # 移动文件
        await renamed.move_to(root / "archive")

        # 删除
        await (root / "archive" / "greeting.txt").unlink()

asyncio.run(main())
```

### 示例 3：上传选项 `UploadOptions`

```python
import asyncio
from openlist import Client, UploadOptions

async def main():
    async with Client("https://your-server.com") as client:
        await client.login("username", "password")

        options = UploadOptions(
            overwrite=True,      # 覆盖已存在的文件
            as_task=False,       # 不作为后台任务
        )

        await client.fs.write_bytes(
            "/data/file.txt",
            b"content",
            options=options
        )

asyncio.run(main())
```

### 示例 4：OTP 双因素认证

```python
import asyncio
from openlist import Client

async def main():
    async with Client("https://your-server.com") as client:
        await client.login("username", "password", otp_key="your-otp-secret")

asyncio.run(main())
```

### 示例 5：SSH 密钥管理

```python
import asyncio
from openlist import Client

async def main():
    async with Client("https://your-server.com") as client:
        await client.login("username", "password")

        # 添加 SSH 密钥
        await client.user.sshkey.add("my-key", "ssh-rsa AAAAB3Nza...")

        # 列出密钥
        keys = await client.user.sshkey.list()
        for k in keys:
            print(f"{k.id}: {k.name}")

        # 删除密钥
        await client.user.sshkey.delete(keys[0].id)

asyncio.run(main())
```

### 示例 6：异常处理

```python
import asyncio
from openlist import Client
from openlist.exceptions import (
    FileNotFoundError,
    FileExistsError,
    PermissionDeniedError,
    AuthenticationError,
)

async def main():
    async with Client("https://your-server.com") as client:
        await client.login("username", "password")

        try:
            await client.fs.stat("/not_exist")
        except FileNotFoundError as e:
            print(f"文件不存在: {e.path}")

        try:
            await client.fs.mkdir("/existing_dir")
        except FileExistsError as e:
            print(f"目录已存在: {e.path}")

asyncio.run(main())
```

### 示例 7：生成资源访问签名

```python
from openlist.utils import sign, to_utc_timestamp
from datetime import datetime, timedelta, timezone

# 永不过期的签名
s1 = sign("/data/file.txt", token="your-secret-token")
print(s1)  # 形如 "abc123-def456:0"

# 一周后过期的签名
expire_at = datetime.now(timezone.utc) + timedelta(weeks=1)
s2 = sign("/data/file.txt", token="your-secret-token", expire=expire_at)
print(s2)
```

---

## 异常层级速查图

```
Exception
└── OpenListError                              # 所有异常的基类
    ├── NetworkError                           # 网络通信错误（含 status_code）
    │   └── UnexpectedResponseError            # 非预期的响应状态码
    ├── AuthenticationError                    # 认证失败
    └── FileSystemError                        # 文件系统错误基类（含 path）
        ├── FileNotFoundError                  # 文件或目录不存在
        ├── FileExistsError                    # 文件或目录已存在
        ├── PermissionDeniedError              # 权限不足（path 可选）
        ├── NotADirectoryError                 # 期望目录但不是目录
        ├── IsADirectoryError                  # 期望文件但是目录
        ├── InvalidPathError                   # 无效的路径格式
        └── OperationError                     # 文件操作执行失败（含 operation）
```

**实例属性速查**：

| 异常类 | 特有属性 |
|--------|----------|
| `OpenListError` | `message`, `details` |
| `NetworkError` | + `status_code` |
| `FileSystemError` | + `path` |
| `OperationError` | + `operation`（`FileSystemError` 的 `path` 也继承） |

> 其余异常类（`AuthenticationError`、`UnexpectedResponseError`、`FileNotFoundError`、`FileExistsError`、`PermissionDeniedError`、`NotADirectoryError`、`IsADirectoryError`、`InvalidPathError`）的实例属性继承自其父类，无新增。
