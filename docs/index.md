# OpenList API 文档

OpenList API 是 OpenList 服务的 Python 客户端，提供异步与同步的文件系统操作、认证和用户管理功能。

```{toctree}
:maxdepth: 2
:caption: 使用指南

getting-started
guides/filesystem
guides/authentication
```

```{toctree}
:maxdepth: 2
:caption: API 参考

api/client
api/filesystem
api/models
api/services
api/exceptions
```

## 本地构建

先用 uv 初始化项目环境，再同步文档依赖组：

```bash
make sync
make docs-install
```

生成静态 HTML：

```bash
make docs-build
```

开发时可用 `make docs-serve` 启动热重载预览服务器。生成的网站入口是 `docs/_build/html/index.html`。`docs/API_REFERENCE.md` 是迁移前的手工参考快照，当前不参与构建；新的 API 页由源码中的 docstring 自动生成。
