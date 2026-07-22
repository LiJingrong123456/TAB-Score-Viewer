# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Fonts Module

平台自适应字体工具函数
"""

import platform
from typing import Optional, List

# 用户自定义 UI 字体，None 表示使用平台默认推荐字体
# 通过设置面板修改后，全局样式表会优先使用该字体
_UI_FONT_FAMILY: Optional[str] = None


def set_ui_font(family: Optional[str]) -> None:
    """
    设置用户自定义 UI 字体

    参数:
        family: 字体族名称，None 或空字符串表示恢复平台默认
    """
    global _UI_FONT_FAMILY
    _UI_FONT_FAMILY = family if family else None


def get_ui_font_family() -> Optional[str]:
    """获取当前用户自定义 UI 字体（可能是 None）"""
    return _UI_FONT_FAMILY


def get_font_families(font_type: str = "ui") -> List[str]:
    """
    根据当前操作系统返回推荐的字体族列表(含 fallback)

    参数:
        font_type: 字体用途类型
            - "ui":      主UI/标注字体, 优先保证中文显示效果
            - "numeric": 数字/英文标签字体, 优先清晰可读
            - "mono":    等宽字体, 用于 dB 值、页码等需对齐的场景

    返回:
        字体族名称列表
    """
    sys_name = platform.system()
    if font_type == "mono":
        if sys_name == "Windows":
            return ["Consolas", "DejaVu Sans Mono", "monospace"]
        elif sys_name == "Darwin":
            return ["Menlo", "Monaco", "DejaVu Sans Mono", "monospace"]
        else:
            return ["DejaVu Sans Mono", "Consolas", "monospace"]
    elif font_type == "numeric":
        if sys_name == "Windows":
            return ["Segoe UI", "Microsoft YaHei", "Arial", "sans-serif"]
        elif sys_name == "Darwin":
            return ["SF Pro Text", "PingFang SC", "Helvetica Neue", "Arial", "sans-serif"]
        else:
            return ["DejaVu Sans", "Noto Sans CJK SC", "WenQuanYi Micro Hei", "sans-serif"]
    else:  # "ui" 默认
        defaults = []
        if sys_name == "Windows":
            defaults = ["Microsoft YaHei", "Segoe UI", "Arial", "sans-serif"]
        elif sys_name == "Darwin":
            defaults = ["PingFang SC", "Heiti SC", "STHeiti", "Helvetica Neue", "Arial", "sans-serif"]
        else:
            defaults = ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans", "sans-serif"]
        if font_type == "ui" and _UI_FONT_FAMILY and _UI_FONT_FAMILY not in defaults:
            return [_UI_FONT_FAMILY] + defaults
        return defaults


def get_font_family(font_type: str = "ui") -> str:
    """
    返回当前平台指定类型的首选字体族名称(单个字体名)

    用途: 直接传给 QFont(family, size) 构造函数
    """
    return get_font_families(font_type)[0]


def get_font_family_css(font_type: str = "ui") -> str:
    """
    返回当前平台指定类型的 CSS font-family 字符串(含 fallback 列表)
    """
    return ", ".join(f"'{f}'" for f in get_font_families(font_type))
