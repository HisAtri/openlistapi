"""
主题配置模块

提供 CLI 的配色方案、主题配置和主题管理功能。
"""

import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from prompt_toolkit.styles import Style

from rich.console import Console
from rich.theme import Theme
from rich.logging import RichHandler


class ColorScheme(BaseModel):
    """配色方案模型
    """

    bg_dark: str = Field(default="#0d1117", description="深色背景")
    bg_lighter: str = Field(default="#161b22", description="稍亮背景")

    text: str = Field(default="#e6edf3", description="主文字颜色")
    text_dim: str = Field(default="#7d8590", description="次要文字")
    text_muted: str = Field(default="#484f58", description="更暗的文字")

    primary: str = Field(default="#00BCFF", description="主强调色")
    success: str = Field(default="#2D8C2A", description="成功色")
    warning: str = Field(default="#F2A20C", description="警告色")
    error: str = Field(default="#A60321", description="错误色")
    info: str = Field(default="#0054C2", description="信息色")
    accent: str = Field(default="#96f7e4", description="辅助强调色")
    
    # 边框
    border: str = Field(default="#30363d", description="边框/分隔线颜色")
    
    @field_validator('*', mode='before')
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """验证十六进制颜色格式"""
        if isinstance(v, str):
            v = v.strip()
            if not v.startswith('#'):
                v = f'#{v}'
            # 验证格式
            if len(v) not in (4, 7):  # #RGB 或 #RRGGBB
                raise ValueError(f"无效的颜色格式: {v}")
            try:
                int(v[1:], 16)
            except ValueError:
                raise ValueError(f"无效的十六进制颜色: {v}")
        return v


class ThemeConfig(BaseModel):
    """主题配置模型"""
    
    name: str = Field(default="claude-code", description="主题名称")
    description: str = Field(default="Claude Code 风格配色", description="主题描述")
    colors: ColorScheme = Field(default_factory=ColorScheme, description="配色方案")
    
    # prompt_toolkit 样式映射
    prompt_bold: bool = Field(default=True, description="提示符是否加粗")
    
    def to_rich_theme(self) -> Theme:
        """转换为 Rich Theme
        
        将配色方案中的所有颜色导出为样式名（颜色别名），
        用户可以在任何地方使用 [primary]...[/primary] 等标记。
        """
        c = self.colors
        return Theme({
            # ═══════════════════════════════════════════════════════════
            # 颜色别名 - 可在任何 Rich 标记中使用
            # 例如: [primary]文字[/primary], [warning]警告[/warning]
            # ═══════════════════════════════════════════════════════════
            "bg_dark": c.bg_dark,
            "bg_lighter": c.bg_lighter,
            "text": c.text,
            "text_dim": c.text_dim,
            "text_muted": c.text_muted,
            "primary": c.primary,
            "success": c.success,
            "warning": c.warning,
            "error": c.error,
            "info": c.info,
            "accent": c.accent,
            "border": c.border,
            
            # ═══════════════════════════════════════════════════════════
            # 组件样式 - 用于特定组件的默认样式
            # ═══════════════════════════════════════════════════════════
            "prompt": f"{'bold ' if self.prompt_bold else ''}{c.primary}",
            "dim": c.text_dim,
            "rule.line": c.border,
            "panel.border": c.border,
        })
    
    def to_prompt_style(self) -> Style:
        """转换为 prompt_toolkit Style"""
        c = self.colors
        return Style.from_dict({
            'separator': c.border,
            'banner': c.primary,
            'prompt': f'{c.primary}{" bold" if self.prompt_bold else ""}',
            'completion-menu': f'bg:{c.bg_lighter} {c.text}',
            'completion-menu.completion': f'bg:{c.bg_lighter} {c.text}',
            'completion-menu.completion.current': f'bg:{c.primary} #ffffff bold',
        })
    
    def save(self, path: Path | str) -> None:
        """保存主题配置到 JSON 文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, path: Path | str) -> "ThemeConfig":
        """从 JSON 文件加载主题配置"""
        path = Path(path)
        if not path.exists():
            return cls()  # 返回默认配置
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.model_validate(data)


# ═══════════════════════════════════════════════════════════════
# 预设主题
# ═══════════════════════════════════════════════════════════════


# Claude Code 风格
THEME_CLAUDE_CODE = ThemeConfig(
    name="claude-code",
    description="Claude Code 风格配色（柔和深色）",
    colors=ColorScheme(
        bg_dark="#1a1a1a",
        bg_lighter="#2d2d2d",
        text="#d4d4d4",
        text_dim="#6e6e6e",
        text_muted="#4a4a4a",
        primary="#e07a5f",
        success="#81b29a",
        warning="#f2cc8f",
        error="#e07a5f",
        info="#7eb8da",
        accent="#a7c4bc",
        border="#3d3d3d",
    ),
)

# Monokai 风格
THEME_MONOKAI = ThemeConfig(
    name="monokai",
    description="Monokai 经典配色",
    colors=ColorScheme(
        bg_dark="#272822",
        bg_lighter="#3e3d32",
        text="#f8f8f2",
        text_dim="#75715e",
        text_muted="#49483e",
        primary="#f92672",
        success="#a6e22e",
        warning="#e6db74",
        error="#f92672",
        info="#66d9ef",
        accent="#ae81ff",
        border="#49483e",
    ),
)

# Nord 风格
THEME_NORD = ThemeConfig(
    name="nord",
    description="Nord 极地配色",
    colors=ColorScheme(
        bg_dark="#2e3440",
        bg_lighter="#3b4252",
        text="#eceff4",
        text_dim="#4c566a",
        text_muted="#434c5e",
        primary="#88c0d0",
        success="#a3be8c",
        warning="#ebcb8b",
        error="#bf616a",
        info="#81a1c1",
        accent="#b48ead",
        border="#4c566a",
    ),
)

# 默认
DEFAULT_THEME = ThemeConfig(
    name="default",
    description="默认主题",
    colors=ColorScheme()
)

# 内置主题字典
BUILTIN_THEMES: dict[str, ThemeConfig] = {
    "claude-code": THEME_CLAUDE_CODE,
    "monokai": THEME_MONOKAI,
    "nord": THEME_NORD,
    "default": DEFAULT_THEME,
}


# ═══════════════════════════════════════════════════════════════
# 主题管理器
# ═══════════════════════════════════════════════════════════════

class ThemeManager:
    """主题管理器（单例）"""
    
    _instance: Optional["ThemeManager"] = None
    _theme: ThemeConfig = DEFAULT_THEME
    _console: Optional[Console] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def theme(self) -> ThemeConfig:
        return self._theme
    
    @property
    def colors(self) -> ColorScheme:
        return self._theme.colors
    
    @property
    def console(self) -> Console:
        if self._console is None:
            self._rebuild_console()
        return self._console
    
    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._rebuild_logger()
        return self._logger
    
    def set_theme(self, theme: ThemeConfig | str) -> None:
        """设置主题"""
        if isinstance(theme, str):
            if theme in BUILTIN_THEMES:
                theme = BUILTIN_THEMES[theme]
            else:
                raise ValueError(f"未知主题: {theme}，可用: {list(BUILTIN_THEMES.keys())}")
        
        self._theme = theme
        self._rebuild_console()
        self._rebuild_logger()
    
    def load_theme(self, path: Path | str) -> None:
        """从文件加载主题"""
        theme = ThemeConfig.load(path)
        self.set_theme(theme)
    
    def _rebuild_console(self) -> None:
        """重建 Console 实例"""
        self._console = Console(
            theme=self._theme.to_rich_theme(),
            force_terminal=True,
        )
    
    def _rebuild_logger(self) -> None:
        """重建 Logger"""
        self._logger = logging.getLogger("cli")
        self._logger.handlers.clear()
        self._logger.addHandler(RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
            markup=True,
        ))
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False


# 全局主题管理器实例
theme_manager = ThemeManager()

# 便捷访问
console = theme_manager.console
logger = theme_manager.logger

