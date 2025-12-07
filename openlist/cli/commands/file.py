import typer
import posixpath
from typing import Optional
from typing_extensions import Annotated
from . import Client, logger, context, run_async, get_event_loop, registry, console
from ...exceptions import NotFound

from pathlib import Path

fs_general_app: typer.Typer = typer.Typer(help="文件系统通用操作")


def normalize_path(current_path: str, relative_path: str) -> str:
    """
    规范化路径，解析相对路径组件（.. 和 .）并确保返回绝对路径
    
    Args:
        current_path: 当前工作目录路径
        relative_path: 相对路径
        
    Returns:
        规范化后的绝对路径（始终以 / 开头）
    """
    # 拼接新的路径并规范化（解析 .. 和 . 组件）
    new_path = posixpath.join(current_path, relative_path)
    new_path = posixpath.normpath(new_path)
    # 确保路径始终以 / 开头（绝对路径）
    if not new_path.startswith("/"):
        new_path = "/" + new_path
    return new_path

@fs_general_app.command("cd")
def cd(path: Annotated[str, typer.Argument(help="要切换的目录路径")]):
    """切换当前工作目录"""
    # 获取用户当前所在目录
    current_path = registry.get("fs_current_path", "/")

    # 规范化路径
    new_path = normalize_path(current_path, path)
    path_info = run_async(context.client.fs.info(new_path))
    if not path_info.is_dir:
        logger.error(f"路径不是目录: {new_path}")
        return
    registry["fs_current_path"] = new_path
    context.cli.set_prompt(f"{new_path}> ")

@fs_general_app.command("ls")
def ls(path: Annotated[str, typer.Argument(help="要列出的目录路径")] = None):
    """列出当前目录或指定路径下的文件和目录"""
    current_path = registry.get("fs_current_path", "/")
    if path:
        # 规范化路径
        work_path = normalize_path(current_path, path)
    else:
        work_path = current_path
    files = run_async(context.client.fs.listdir(work_path))
    if not files.content:
        console.print("[cyan]-[/cyan]")
        return
    for file in files.content:
        name = file.name
        size = file.size
        proper = "d" if file.is_dir else "-"
        size_str = f"{size/1024:.1f}K" if not file.is_dir else "-"
        console.print(f"[bold]{name:<20}[/bold]   [cyan]{proper}[/cyan]   [magenta]{size_str:>8}[/magenta]")

@fs_general_app.command("rm")
def rm(path: Annotated[str, typer.Argument(help="要删除的文件或目录路径")]):
    """删除文件或目录"""
    current_path = registry.get("fs_current_path", "/")
    path = normalize_path(current_path, path)
    try:
        run_async(context.client.fs.remove(path))
    except NotFound as e:
        logger.error(f"文件或目录不存在: {path}")
        return
    console.print(f"[green]已删除文件或目录: {path}[/green]")
        