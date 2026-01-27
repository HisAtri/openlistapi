# OpenList API

OpenList API 的 Python 客户端。

## 特性

- 基于 `httpx` 的异步设计，同时提供同步接口
- 类似 `pathlib.Path` 的面向对象文件操作接口
- 完整的文件系统操作方法
- 用户管理和认证
- 支持流式及分片上传
- 使用 Pydantic 定义明确的类型
- 层次化的异常体系

## 要求

- [Python 3.10](https://www.python.org/downloads/release/python-3100/) 或以上版本
- 无操作系统及架构限制

## 安装

使用 pip 安装：
```bash
pip install openlist
```

## 快速开始

### 基础用法

```python
import asyncio
from openlist import Client

async def main():
    async with Client("https://your-server.com") as client:
        await client.login("username", "password")
        
        # 获取当前用户信息
        user_info = await client.user.me()
        print(f"当前用户: {user_info.username}")

asyncio.run(main())
```

### 文件系统操作 (函数式)

```python
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
        
        # 从本地上传 (分片流式)
        await fs.upload_file("local_file.zip", "/data/remote_file.zip")
        
        # 复制、移动、删除
        await fs.copy("/data/file.txt", "/backup/")
        await fs.move("/data/old.txt", "/archive/")
        await fs.remove("/data/temp.txt")
```

### 文件系统操作 (pathlib 风格)

```python
async def main():
    async with Client("https://your-server.com") as client:
        await client.login("username", "password")
        
        # 创建路径对象
        root = client.path("/data")
        
        # 路径操作 (不涉及网络)
        config = root / "config" / "settings.json"
        print(f"路径: {config}")           # /data/config/settings.json
        print(f"名称: {config.name}")      # settings.json
        print(f"父目录: {config.parent}")  # /data/config
        print(f"扩展名: {config.suffix}")  # .json
        
        # 文件操作 (网络请求)
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
```

### 上传选项

```python
from openlist.models.file import UploadOptions

async def main():
    async with Client("https://your-server.com") as client:
        await client.login("username", "password")
        
        options = UploadOptions(
            overwrite=True,      # 覆盖已存在的文件
            as_task=False,       # 作为后台任务
        )
        
        await client.fs.write_bytes(
            "/data/file.txt",
            b"content",
            options=options
        )
```

### OTP 双因素认证

```python
async def main():
    async with Client("https://your-server.com") as client:
        await client.login("username", "password", otp_key="your-otp-secret")
```

## 异常处理

```python
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
```

## 模块结构

| 模块 | 说明 |
|------|------|
| `openlist.Client` | 异步客户端入口 |
| `openlist.core.file.AsyncFileSystem` | 异步文件系统服务 |
| `openlist.core.file.SyncFileSystem` | 同步文件系统服务 |
| `openlist.core.file.RemotePath` | pathlib 风格路径对象 |
| `openlist.models.file` | 文件系统 Pydantic 模型 |
| `openlist.exceptions` | 异常类型定义 |
