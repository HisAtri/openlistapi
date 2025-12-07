import typer
import shlex
import shutil
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from rich.panel import Panel

from .theme import (
    ThemeConfig,
    BUILTIN_THEMES,
    theme_manager,
)


def build_completer_dict(typer_app: typer.Typer) -> dict:
    """从 Typer 应用的命令树自动构建 NestedCompleter 所需的字典"""
    result = {}
    
    # 遍历子命令组 (如 user_app)
    for group in typer_app.registered_groups:
        # 尝试多种方式获取组名
        group_name = None
        if hasattr(group, 'name') and group.name:
            group_name = group.name
        elif hasattr(group, 'typer_instance') and group.typer_instance:
            if hasattr(group.typer_instance, 'info') and hasattr(group.typer_instance.info, 'name'):
                group_name = group.typer_instance.info.name
        
        if group.typer_instance:
            if group_name:
                # 如果组有名称，创建嵌套字典
                result[group_name] = build_completer_dict(group.typer_instance)
            else:
                # 如果组没有名称，将该组下的命令直接合并到当前层级
                nested_dict = build_completer_dict(group.typer_instance)
                result.update(nested_dict)
    
    # 遍历直接注册的命令
    for command in typer_app.registered_commands:
        # 命令名称：优先使用装饰器指定的 name，否则用函数名
        cmd_name = command.name or (command.callback.__name__ if command.callback else None)
        if cmd_name:
            result[cmd_name] = None  # 叶子节点
    
    return result


class Cli:
    """
    CLI 交互界面
    
    布局：
    [日志/输出区域] ← 终端原生滚动
    ─────────────── ← 分隔线
    [Banner 区域]   ← 显示状态信息
    ─────────────── ← 分隔线
    [输入行]        ← Tab 补全，补全菜单在下方
    """
    
    def __init__(
        self, 
        app: typer.Typer, 
        prompt: str = "cli> ",
        theme: ThemeConfig | str | None = None,
    ):
        self.app = app
        self.prompt = prompt
        self._running = False
        
        # 设置主题
        if theme is not None:
            theme_manager.set_theme(theme)
        
        # Banner 内容
        self._banner_text = ""
        
        # 构建补全器
        completion_dict = build_completer_dict(app)
        completion_dict['exit'] = None
        completion_dict['clear'] = None
        completion_dict['help'] = None
        completion_dict['theme'] = None
        self._completer = NestedCompleter.from_nested_dict(completion_dict)
        
        # 使用主题管理器的样式
        self._style = theme_manager.theme.to_prompt_style()
        
        # 创建 PromptSession
        self._session = PromptSession(
            completer=self._completer,
            style=self._style,
            complete_while_typing=True,
            reserve_space_for_menu=0,     # 不预留补全菜单空间
        )
    
    def _get_terminal_width(self) -> int:
        """获取终端宽度"""
        try:
            return shutil.get_terminal_size().columns
        except Exception:
            return 80
    
    def _print_banner_area(self):
        """
        使用 Rich console 打印 banner 区域，支持 Rich 标记语法
        """
        con = theme_manager.console
        width = self._get_terminal_width()
        separator = '─' * width
        
        banner = self._banner_text or '[text_dim]Tab 补全 | Ctrl+D 退出[/text_dim]'
        
        # 使用 Rich console 打印，支持标记语法
        con.print(f"[border]{separator}[/border]")
        con.print(f" {banner}")
        con.print(f"[border]{separator}[/border]")
        
        # 记录 prompt 行数，用于清除（3行 banner 区域 + 1行输入）
        self._prompt_lines = 4
    
    def _build_prompt_message(self):
        """
        构建 prompt message（仅输入行）
        """
        return [
            ('class:prompt', self.prompt),
        ]
    
    def _clear_prompt_area(self, input_text: str = ""):
        """清除 prompt 区域，保留用户输入的命令"""
        # ANSI 转义序列：
        # \033[nA - 向上移动 n 行
        # \033[K  - 清除当前行
        # \033[J  - 清除光标以下所有内容
        
        # 需要清除的行数：3行 banner 区域 + 1行输入行
        lines_to_clear = getattr(self, '_prompt_lines', 4)
        
        # 向上移动并清除
        print(f'\033[{lines_to_clear}A', end='')  # 向上移动
        print('\033[J', end='')  # 清除到屏幕底部
        
        # 打印用户输入的命令（简洁格式）
        if input_text:
            theme_manager.console.print(f"[prompt]{self.prompt}[/prompt]{input_text}")
    
    def _execute_command(self, text: str):
        """执行命令"""
        con = theme_manager.console
        
        if text == 'exit':
            self._running = False
            return
        
        if text == 'clear':
            con.clear()
            return
        
        if text == 'help':
            con.print("可用命令：")
            con.print("  exit   - 退出程序")
            con.print("  clear  - 清空屏幕")
            con.print("  help   - 显示帮助")
            con.print("  theme  - 切换主题 (default/claude-code/monokai/nord)")
            self._print_command_tree(self.app, prefix="  ")
            return
        
        if text.startswith('theme'):
            parts = text.split(maxsplit=1)
            if len(parts) == 1:
                # 显示当前主题和可用主题
                con.print(f"当前主题: [prompt]{theme_manager.theme.name}[/prompt]")
                con.print(f"可用主题: {', '.join(BUILTIN_THEMES.keys())}")
            else:
                theme_name = parts[1].strip()
                try:
                    theme_manager.set_theme(theme_name)
                    self._style = theme_manager.theme.to_prompt_style()
                    con.print(f"[success]✓ 已切换到主题: {theme_name}[/success]")
                except ValueError as e:
                    con.print(f"[error]{e}[/error]")
            return
        
        # 执行 Typer 命令
        try:
            args = shlex.split(text)
            self.app(args, standalone_mode=False)
        except SystemExit:
            pass
        except Exception as e:
            con.print(f"[error]Error: {e}[/error]")
    
    def _print_command_tree(self, typer_app: typer.Typer, prefix: str = ""):
        """递归输出命令树"""
        con = theme_manager.console
        for group in typer_app.registered_groups:
            # 尝试多种方式获取组名
            name = None
            if hasattr(group, 'name') and group.name:
                name = group.name
            elif hasattr(group, 'typer_instance') and group.typer_instance:
                if hasattr(group.typer_instance, 'info') and hasattr(group.typer_instance.info, 'name'):
                    name = group.typer_instance.info.name
            
            # 如果组有名称，显示组名并递归显示子命令
            if name:
                con.print(f"{prefix}{name}/")
                if group.typer_instance:
                    self._print_command_tree(group.typer_instance, prefix + "  ")
            else:
                # 如果组没有名称，直接递归显示该组下的命令（作为顶级命令）
                if group.typer_instance:
                    self._print_command_tree(group.typer_instance, prefix)
        
        for cmd in typer_app.registered_commands:
            name = cmd.name or (cmd.callback.__name__ if cmd.callback else "unknown")
            con.print(f"{prefix}{name}")
    
    def log(self, message: str, level: str = "info"):
        """输出日志（使用 Rich console）"""
        style_map = {
            "info": "info",
            "warning": "warning", 
            "error": "error",
            "success": "success",
            "debug": "dim",
        }
        style = style_map.get(level, "info")
        theme_manager.console.print(f"[{style}]{message}[/{style}]")
    
    def set_banner(self, text: str):
        """设置 Banner 内容（下次 prompt 时显示）"""
        self._banner_text = text

    def set_prompt(self, prompt: str):
        """设置 Prompt"""
        self.prompt = prompt
    
    def clear_banner(self):
        """清空 Banner"""
        self._banner_text = ""
    
    def start(self, *, clear: bool=True):
        """启动 CLI 交互循环"""
        self._running = True
        con = theme_manager.console
        
        # 将 Cli 实例注册到 context 中，使命令可以访问
        from .commands import context as cli_context
        cli_context.cli = self
        # 清空屏幕
        con.clear() if clear else ""
        # 欢迎信息（使用 Rich Panel）
        con.print(Panel(
            """[prompt]   ___                   _     _     _      ____ _     ___ 
  / _ \ _ __   ___ _ __ | |   (_)___| |_   / ___| |   |_ _|
 | | | | '_ \ / _ \ '_ \| |   | / __| __| | |   | |    | | 
 | |_| | |_) |  __/ | | | |___| \__ \ |_  | |___| |___ | | 
  \___/| .__/ \___|_| |_|_____|_|___/\__|  \____|_____|___|
       |_|                                                 [/prompt]\n\n"""
            "[info]欢迎使用 OpenList CLI！[/info]\n"
            "[dim]输入 [info]help[/info] 查看帮助，[info]exit[/info] 或 [info]Ctrl+D[/info] 退出[/dim]",
            border_style=theme_manager.colors.border,
            padding=(0, 2),
        ))
        
        while self._running:
            try:
                # 先打印 banner 区域（支持 Rich 标记）
                self._print_banner_area()
                
                # 然后显示输入提示符
                text = self._session.prompt(self._build_prompt_message)
                
                text = text.strip()
                if not text:
                    # 空输入也要清除 prompt 区域
                    self._clear_prompt_area()
                    continue
                
                # 清除 prompt 区域，只保留用户命令
                self._clear_prompt_area(text)
                self._execute_command(text)
                
            except KeyboardInterrupt:
                self._clear_prompt_area()
                con.print("[warning]^C[/warning]")
                continue
            except EOFError:
                self._clear_prompt_area()
                con.print("[dim]See you next time...[/dim]")
                break
        
        # 清理资源：关闭 Client 连接
        self._cleanup()
        self._running = False
    
    def _cleanup(self):
        """清理资源，关闭 Client 连接和异步任务"""
        from .commands import context, run_async, get_event_loop
        if context.client:
            try:
                # 关闭 Client，这会停止自动刷新任务并关闭 HTTP 连接
                run_async(context.client.close())
            except Exception:
                # 忽略清理时的错误，避免影响退出
                pass
            finally:
                # 清理所有pending的任务（排除当前任务）
                loop = get_event_loop()
                current_task = asyncio.current_task(loop)
                pending = [task for task in asyncio.all_tasks(loop) 
                          if task is not current_task and not task.done()]
                for task in pending:
                    task.cancel()
                # 等待所有任务完成（最多等待1秒）
                if pending:
                    try:
                        run_async(asyncio.wait_for(
                            asyncio.gather(*pending, return_exceptions=True),
                            timeout=1.0
                        ))
                    except Exception:
                        pass
