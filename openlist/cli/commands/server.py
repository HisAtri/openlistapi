import typer
from typing import Optional
from typing_extensions import Annotated
from . import Client, logger, context, run_async, get_event_loop

server_app: typer.Typer = typer.Typer(help="服务器连接管理")

@server_app.command("connect")
def connect(
    base_url: Annotated[str, typer.Argument(help="服务器地址，例如: https://alist.example.com")],
    username: Annotated[Optional[str], typer.Argument(help="登录用户名")] = None,
    password: Annotated[Optional[str], typer.Argument(help="登录密码")] = None,
    otp_key: Annotated[Optional[str], typer.Option(
        "--otp", "-o",
        help="两步验证密钥 (可选)"
    )] = None,
):
    """连接到服务器并登录"""
    # 先设置全局事件循环，确保 Client 中的 asyncio 对象绑定到正确的循环
    get_event_loop()
    context.client = Client(base_url=base_url)

    if username and not password:
        password = typer.prompt("密码", hide_input=True, type=str)
        otp_key = typer.prompt("OTP Key", default="", show_default=False) or None
    elif not username:
        username = typer.prompt("用户名", type=str)
        password = typer.prompt("密码", hide_input=True, type=str)
        otp_key = typer.prompt("OTP Key", default="", show_default=False) or None
    
    run_async(context.client.login(username=username, password=password, otp_key=otp_key))
    logger.info(f"Connected to {base_url}")
    
    # 修改 CLI Banner 显示连接状态
    context.set_banner(f"[success]✓ 已连接到:[/success] [info]{base_url}[/info] | [dim]用户: {username}[/dim]")
    context.cli.set_prompt(f"{username}@{base_url}> ")

@server_app.command("logout")
def logout():
    """断开与服务器的连接"""
    run_async(context.client.logout())
    logger.info("已断开连接")
    context.set_banner(f"[warning]已断开连接[/warning]")
    context.cli.set_prompt(f"cli> ")
