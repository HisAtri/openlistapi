# 快速开始

## 安装

```bash
python -m pip install openlist
```

## 登录并读取当前用户

```python
import asyncio

from openlist import Client


async def main() -> None:
    async with Client("https://your-server.com") as client:
        await client.login("username", "password")
        user = await client.user.me()
        print(user.username)


asyncio.run(main())
```

`Client` 是异步客户端入口。使用 `async with` 可在退出时关闭 HTTP 连接。

```{seealso}
更多初始化和认证方式请参阅 {doc}`guides/authentication`。
```
