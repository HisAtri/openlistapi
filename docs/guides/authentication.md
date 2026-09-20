# 认证

使用用户名和密码登录后，访问令牌会保存在客户端上下文中，并自动附加到后续请求。

```python
async with Client("https://your-server.com", auto_refresh=True) as client:
    await client.login("username", "password")
```

如果账户启用了 TOTP，可传入 OTP 密钥：

```python
await client.login("username", "password", otp_key="your-otp-secret")
```

`auto_refresh=True` 是默认值。客户端将在令牌临近到期时尝试重新登录；退出上下文或调用 `close()` 时会停止该任务并关闭连接。
