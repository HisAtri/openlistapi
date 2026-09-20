.DEFAULT_GOAL := help

DOCS_DIR := docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build
DOCS_HTML_DIR := $(DOCS_BUILD_DIR)/html

.PHONY: help sync docs-install docs-serve docs-build docs-clean

help: ## 显示可用命令
	@echo "OpenList 开发命令"
	@echo "  sync             用 uv 同步项目基础环境"
	@echo "  docs-install     同步项目环境并安装 docs 依赖组"
	@echo "  docs-serve       启动文档热重载预览服务器"
	@echo "  docs-build       构建静态 HTML 文档"
	@echo "  docs-clean       删除文档构建产物"

sync: ## 用 uv 同步项目基础环境
	uv sync

docs-install: ## 同步项目环境并安装 docs 依赖组
	uv sync --group docs

docs-serve: ## 启动文档热重载预览服务器（http://127.0.0.1:8000）
	uv run --group docs sphinx-autobuild $(DOCS_DIR) $(DOCS_HTML_DIR) --host 127.0.0.1 --port 8000

docs-build: ## 构建静态 HTML 文档（严格处理警告）
	uv run --group docs sphinx-build -W --keep-going -b html $(DOCS_DIR) $(DOCS_HTML_DIR)

docs-clean: ## 删除文档构建产物
	powershell -NoProfile -Command "if (Test-Path '$(DOCS_BUILD_DIR)') { Remove-Item -Recurse -Force '$(DOCS_BUILD_DIR)' }"
