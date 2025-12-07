from ... import Client
from ..theme import console, logger

import asyncio
from pydantic import BaseModel
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .. import Cli

class CliContext(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    
    client: Client = None
    cli: Any = None  # 使用 Any 避免循环导入
    
    def set_banner(self, text: str):
        """设置 CLI Banner"""
        if self.cli:
            self.cli.set_banner(text)
    
    def clear_banner(self):
        """清除 CLI Banner"""
        if self.cli:
            self.cli.clear_banner()

context: CliContext = CliContext()

# 全局事件循环，整个 CLI 生命周期共享
_event_loop: asyncio.AbstractEventLoop = None

# 全局状态寄存器
registry: dict[str, Any] = {}


def get_event_loop() -> asyncio.AbstractEventLoop:
    """获取或创建全局事件循环"""
    global _event_loop
    if _event_loop is None or _event_loop.is_closed():
        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)
    return _event_loop


def run_async(coro):
    """
    安全地运行异步代码
    使用全局共享的事件循环，确保所有异步对象使用同一个循环
    """
    loop = get_event_loop()
    return loop.run_until_complete(coro)
