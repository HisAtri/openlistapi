# 文件系统操作

`client.fs` 提供函数式文件系统接口；`client.path()` 则创建类似 `pathlib.Path` 的远程路径对象。两者都使用同一个异步客户端和认证上下文。

## 函数式接口

```python
async with Client("https://your-server.com") as client:
    await client.login("username", "password")
    await client.fs.mkdir("/data/new-folder", exist_ok=True)
    await client.fs.write_bytes("/data/new-folder/hello.txt", b"Hello!")

    for item in await client.fs.listdir("/data"):
        print(item.name)
```

## 路径接口

```python
async with Client("https://your-server.com") as client:
    await client.login("username", "password")
    file = client.path("/data") / "new-folder" / "hello.txt"

    if await file.exists():
        print((await file.stat()).size)
```

同步调用方可使用 `SyncFileSystem` 和 `SyncRemotePath`。它们具有相同的业务语义，但不能在已经运行的 asyncio 事件循环中调用。
