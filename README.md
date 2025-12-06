# OpenList API

OpenList API 的 Python 异步客户端，提供完整的文件管理、用户管理和认证功能。

## 特性

- 基于`httpx`的异步设计
- 完整的文件系统操作方法
- 用户管理和认证
- 支持流式及分片上传

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
    # 创建客户端实例
    client = Client("https://your-openlist-server.com")
    # 登录
    await client.login("username", "password")
    # 获取当前用户信息
    user_info = await client.user.me()
    print(f"当前用户: {user_info.username}")
    # 关闭连接
    await client.close()

asyncio.run(main())
```

### 使用上下文管理器

```python
async def main():
    async with Client("https://your-openlist-server.com") as client:
        await client.login("username", "password")
        user_info = await client.user.me()
        print(user_info)
```

### OTP 双因素认证

```python
async def main():
    client = Client("https://your-openlist-server.com")
    await client.login("username", "password", otp_key="your-otp-secret")
```