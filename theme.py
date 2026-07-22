# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Theme Manager Module

主题管理器（单例模式）+ 自定义主题加载 + 图标/QSS缓存

依赖:
  - constants: THEME_DARK, THEME_LIGHT, THEME_COLORS, CUSTOM_THEMES_DIR, ICON_PATH, _APP_BASE_DIR
  - ApolloTab ThemeConfig: 同步注册到GTP渲染主题
"""

import os
import sys
import copy
import json
import importlib.util
from typing import Dict, List, Optional

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon

from ApolloTab.utils.constants import ThemeConfig

from constants import (
    THEME_DARK,
    THEME_LIGHT,
    THEME_COLORS,
    CUSTOM_THEMES_DIR,
    _APP_BASE_DIR,
)


# ============================================================
# 应用图标加载
# ============================================================

def _find_icon_file(*dirs: str) -> str:
    """在给定目录中搜索图标文件 (支持 .icns .ico .png)"""
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in ("icon.icns", "icon.ico", "icon.png"):
            path = os.path.join(d, name)
            if os.path.exists(path):
                return path
    return ""


def get_app_icon() -> QIcon:
    """
    获取应用图标(QIcon对象)
    原理: 兼容开发和PyInstaller打包两种运行模式
      - 开发模式: 从脚本同目录读取图标
      - 打包模式(sys.frozen): 优先从exe所在目录读取，若不存在则从_internal/子目录读取
    支持格式: .icns (macOS), .ico (Windows), .png (通用)
    返回: QIcon对象，文件不存在时返回空 QIcon
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
        path = _find_icon_file(base, os.path.join(base, "_internal"))
    else:
        path = _find_icon_file(_APP_BASE_DIR)
    if path:
        return QIcon(path)
    return QIcon()  # 文件不存在时返回空图标


def load_icon(icon_name: str, size: tuple = None) -> QIcon:
    """
    加载 SVG 图标为 QIcon 对象 / Load SVG icon as QIcon object
    原理: 从 icons/ 目录读取 SVG 文件，使用 Qt 渲染为像素图标
         兼容开发模式和 PyInstaller 打包模式(onedir: _internal/)
    参数:
      icon_name: 图标文件名(不含扩展名), 如 "annotate", "export", "play"
      size:     可选图标尺寸 (宽, 高) 元组, 默认 None(使用SVG原始尺寸)
    返回:
      QIcon 对象, 文件不存在时返回空 QIcon
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller onedir 模式: 数据文件在 _internal/ 子目录
        base = os.path.join(os.path.dirname(sys.executable), '_internal')
    else:
        base = _APP_BASE_DIR
    svg_path = os.path.join(base, 'icons', f'{icon_name}.svg')
    if os.path.exists(svg_path):
        return QIcon(svg_path)
    return QIcon()


# ============================================================
# QSS样式表缓存（性能优化：P0-1）
# ============================================================
# 原理: 大量 setStyleSheet() 重复调用 f-string 拼接 QSS，每次 Qt 都会重新解析
#       缓存 key 为 (theme_name, window_class)，切换主题时自动刷新

# 全局QSS缓存: {theme_name: {window_class: qss_string}}
_QSS_CACHE: Dict[str, Dict[str, str]] = {}


def _get_cached_qss(window_class: str, theme_name: str, builder_fn) -> str:
    """
    获取缓存的QSS样式表字符串（首次调用时生成并缓存，后续直接返回）

    参数:
        window_class: 窗口类名，如 'DisplayWindow', 'SelectionWindow', 'SettingsDialog'
        theme_name:   主题名称，如 'dark', 'light'
        builder_fn:   无参构建函数，返回QSS字符串
    """
    if theme_name not in _QSS_CACHE:
        _QSS_CACHE[theme_name] = {}
    cache = _QSS_CACHE[theme_name]
    if window_class not in cache:
        cache[window_class] = builder_fn()
    return cache[window_class]


# ============================================================
# 主题管理器（单例模式）
# ============================================================

class ThemeManager(QObject):
    """
    全局主题管理器（单例模式）

    功能:
      1. 统一管理深色/浅色两套UI配色方案
      2. 提供运行时动态切换主题能力
      3. 通过 theme_changed 信号通知所有UI组件刷新样式
      4. 与 ApolloTab 渲染主题联动
      5. 支持用户自定义主题扩展
    """

    # === pyqtSignal 必须定义为类属性 (PyQt5硬性要求) ===
    theme_changed = pyqtSignal(str)

    _instance = None
    _initialized: bool = False

    # 用户自定义主题注册表
    _custom_themes: Dict[str, dict] = {}

    # GTP渲染主题映射
    _GTP_THEME_MAP = {
        'dark': 'dark',
        'light': 'light',
    }

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        super().__init__()
        self._current_theme_name = "dark"
        self._theme_data = dict(THEME_DARK)

    @classmethod
    def register_theme(cls, name: str, display_name: str, ui_colors: dict,
                       gtp_colors: dict = None) -> bool:
        """
        注册一个自定义主题到 ThemeManager
        """
        name_lower = name.lower().strip()
        if name_lower in ('dark', 'light'):
            print(f"[ThemeManager] 不允许覆盖内置主题 '{name_lower}'")
            return False
        if not ui_colors:
            print(f"[ThemeManager] 主题 '{name_lower}' 缺少 ui 颜色，注册失败")
            return False

        merged_ui = {**THEME_DARK, **ui_colors}

        cls._custom_themes[name_lower] = {
            'display_name': display_name or name_lower,
            'ui': merged_ui,
            'gtp': gtp_colors or {},
        }

        try:
            ThemeConfig.register_theme(name_lower, gtp_colors or {})
        except Exception as e:
            print(f"[ThemeManager] 注册 ApolloTab 主题 '{name_lower}' 失败: {e}")

        print(f"[ThemeManager] 自定义主题已注册: {name_lower} ({display_name})")
        return True

    @classmethod
    def unregister_theme(cls, name: str) -> bool:
        """
        注销自定义主题
        """
        name_lower = name.lower().strip()
        if name_lower in ('dark', 'light'):
            return False
        if name_lower not in cls._custom_themes:
            return False
        del cls._custom_themes[name_lower]
        try:
            ThemeConfig.unregister_theme(name_lower)
        except Exception:
            pass
        return True

    @classmethod
    def get(cls, key: str, default: str = None) -> str:
        """获取当前主题的颜色值"""
        instance = cls()
        return instance._theme_data.get(key, default or THEME_DARK.get(key, '#000000'))

    @classmethod
    def current(cls) -> dict:
        """获取当前完整的主题配色字典（副本）"""
        instance = cls()
        return dict(instance._theme_data)

    @classmethod
    def current_name(cls) -> str:
        """获取当前主题名称"""
        return cls()._current_theme_name

    @classmethod
    def is_dark(cls) -> bool:
        """判断当前是否为深色主题"""
        return cls()._current_theme_name == 'dark'

    @classmethod
    def is_light(cls) -> bool:
        """判断当前是否为浅色主题"""
        return cls()._current_theme_name == 'light'

    @property
    def gtp_render_theme(self) -> str:
        """获取当前UI主题对应的ApolloTab渲染主题名称"""
        if self._current_theme_name in self._custom_themes:
            return self._current_theme_name
        return self._GTP_THEME_MAP.get(self._current_theme_name, 'dark')

    @classmethod
    def get_gtp_render_theme(cls) -> str:
        """类方法接口: 获取GTP渲染主题名称"""
        return cls().gtp_render_theme

    @classmethod
    def is_custom_theme(cls, theme_name: str) -> bool:
        """判断指定名称是否为已注册的自定义主题"""
        return theme_name.lower().strip() in cls._custom_themes

    @classmethod
    def get_custom_theme(cls, theme_name: str) -> Optional[dict]:
        """获取自定义主题定义（副本）"""
        return copy.deepcopy(cls._custom_themes.get(theme_name.lower().strip()))

    @classmethod
    def set_theme(cls, theme_name: str) -> bool:
        """切换全局主题"""
        instance = cls()
        theme_name = theme_name.lower().strip()

        if theme_name == instance._current_theme_name:
            return True

        if theme_name == 'dark':
            instance._theme_data = dict(THEME_DARK)
        elif theme_name == 'light':
            instance._theme_data = dict(THEME_LIGHT)
        elif theme_name in instance._custom_themes:
            instance._theme_data = dict(instance._custom_themes[theme_name]['ui'])
        else:
            available = [t[0] for t in cls.available_themes()]
            print(f"[ThemeManager] 未知主题: '{theme_name}'，可用: {', '.join(available)}")
            return False

        old_theme = instance._current_theme_name
        instance._current_theme_name = theme_name

        # 更新向后兼容的全局变量
        global THEME_COLORS
        THEME_COLORS = instance._theme_data

        print(f"[ThemeManager] 主题已切换: {old_theme} → {theme_name}")

        try:
            instance.theme_changed.emit(theme_name)
        except Exception:
            pass

        return True

    @classmethod
    def available_themes(cls) -> list:
        """获取所有可用主题列表 [(name, display_name), ...]"""
        themes = [
            ('dark', '深色模式 (Dark)'),
            ('light', '浅色模式 (Light)'),
        ]
        for name, data in cls._custom_themes.items():
            themes.append((name, data.get('display_name', name)))
        return themes

    @classmethod
    def apply_stylesheet(cls, widget, extra_css: str = "") -> None:
        """
        为指定控件应用当前主题的基础样式表

        注意: 此方法依赖主文件中的 get_font_family_css()，因为它需要
              访问 _UI_FONT_FAMILY 全局状态。为避免循环依赖，
              字体函数保留在主文件，本方法延迟导入。
        """
        from fonts import get_font_family_css
        theme = cls.current()
        base_css = f"""
            {{ background-color: {theme['bg_primary']}; color: {theme['text_primary']};
               font-family: {get_font_family_css('ui')}; }}
            QLabel {{ color: {theme['text_primary']}; font-size: 13px; }}
            QLineEdit {{ background-color: {theme['bg_surface']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 5px; padding: 5px 8px; }}
            QSpinBox {{ background-color: {theme['bg_surface']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 4px; padding: 4px; }}
            QComboBox {{ background-color: {theme['bg_surface']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 4px; padding: 4px 8px; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{ background-color: {theme['bg_surface']}; color: {theme['text_primary']};
                selection-background-color: {theme['primary']}; }}
            QGroupBox {{ color: {theme['text_primary']}; border: 1px solid {theme['border']};
                border-radius: 8px; margin-top: 12px; padding-top: 8px; font-weight: bold; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
            QSlider::groove:horizontal {{ border: none; height: 4px;
                background: {theme['bg_surface']}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {theme['primary']};
                border: 2px solid {theme['bg_primary']}; width: 16px; margin: -7px 0; border-radius: 8px; }}
            QListWidget {{ background-color: {theme['bg_surface']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 6px; outline: none; }}
            QListWidget::item {{ padding: 6px; border-bottom: 1px solid {theme['border']}; }}
            QListWidget::item:selected {{ background-color: {theme['primary']}; color: white; }}
            QListWidget::item:hover {{ background-color: {theme['primary']}; opacity:0.15; border-radius:4px; }}
            QScrollBar:vertical {{ background: {theme['bg_secondary']}; width: 10px; border-radius: 5px; }}
            QScrollBar::handle:vertical {{ background: {theme['border']}; border-radius: 5px; min-height: 30px; }}
            QScrollBar::handle:vertical:hover {{ background: {theme['text_muted']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """
        widget.setStyleSheet(base_css + extra_css)


# ============================================================
# 自定义主题加载器
# ============================================================

def _load_theme_from_json(file_path: str) -> Optional[dict]:
    """
    从 JSON 文件加载主题定义

    文件格式:
        {
          "name": "sepia",
          "display_name": "Sepia (护眼纸色)",
          "ui": { "bg_primary": "#F5E6D3", ... },
          "gtp": { "COLOR_BG": "#F5E6D3", ... }
        }
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[主题加载] JSON 解析失败 '{file_path}': {e}")
        return None

    if not isinstance(data, dict):
        print(f"[主题加载] 文件内容必须是 JSON 对象 '{file_path}'")
        return None

    name = data.get('name')
    if not name or not isinstance(name, str):
        print(f"[主题加载] 缺少有效的 'name' 字段 '{file_path}'")
        return None

    ui_colors = data.get('ui')
    gtp_colors = data.get('gtp')
    if not isinstance(ui_colors, dict) or not ui_colors:
        print(f"[主题加载] 主题 '{name}' 缺少非空 'ui' 颜色定义，跳过")
        return None
    if not isinstance(gtp_colors, dict) or not gtp_colors:
        print(f"[主题加载] 主题 '{name}' 缺少非空 'gtp' 颜色定义，跳过")
        return None

    return {
        'name': name,
        'display_name': data.get('display_name', name),
        'ui': ui_colors,
        'gtp': gtp_colors,
    }


def _load_theme_from_py(file_path: str) -> Optional[dict]:
    """
    从 Python 文件加载主题定义

    文件格式:
        THEME = {
            "name": "sepia",
            "display_name": "Sepia (护眼纸色)",
            "ui": { ... },
            "gtp": { ... },
        }
    """
    try:
        spec = importlib.util.spec_from_file_location("custom_theme_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"[主题加载] Python 模块加载失败 '{file_path}': {e}")
        return None

    if not hasattr(module, 'THEME'):
        print(f"[主题加载] Python 文件中缺少 THEME 变量 '{file_path}'")
        return None

    data = module.THEME
    if not isinstance(data, dict):
        print(f"[主题加载] THEME 必须是字典 '{file_path}'")
        return None

    name = data.get('name')
    if not name or not isinstance(name, str):
        print(f"[主题加载] 缺少有效的 'name' 字段 '{file_path}'")
        return None

    ui_colors = data.get('ui')
    gtp_colors = data.get('gtp')
    if not isinstance(ui_colors, dict) or not ui_colors:
        print(f"[主题加载] 主题 '{name}' 缺少非空 'ui' 颜色定义，跳过")
        return None
    if not isinstance(gtp_colors, dict) or not gtp_colors:
        print(f"[主题加载] 主题 '{name}' 缺少非空 'gtp' 颜色定义，跳过")
        return None

    return {
        'name': name,
        'display_name': data.get('display_name', name),
        'ui': ui_colors,
        'gtp': gtp_colors,
    }


def load_all_custom_themes() -> int:
    """
    扫描 CUSTOM_THEMES_DIR 目录，自动加载所有 JSON/Python 主题文件

    返回:
        成功加载并注册的主题数量
    """
    if not os.path.isdir(CUSTOM_THEMES_DIR):
        try:
            os.makedirs(CUSTOM_THEMES_DIR, exist_ok=True)
            print(f"[主题加载] 已创建自定义主题目录: {CUSTOM_THEMES_DIR}")
        except Exception as e:
            print(f"[主题加载] 创建主题目录失败: {e}")
            return 0

    loaded_count = 0
    try:
        entries = sorted(os.listdir(CUSTOM_THEMES_DIR))
    except Exception as e:
        print(f"[主题加载] 读取主题目录失败: {e}")
        return 0

    for entry in entries:
        if entry.startswith('_') or entry.startswith('.'):
            continue

        file_path = os.path.join(CUSTOM_THEMES_DIR, entry)
        if not os.path.isfile(file_path):
            continue

        _, ext = os.path.splitext(entry)
        ext = ext.lower()

        theme_def = None
        if ext == '.json':
            theme_def = _load_theme_from_json(file_path)
        elif ext == '.py':
            theme_def = _load_theme_from_py(file_path)
        else:
            continue

        if theme_def is None:
            continue

        try:
            ThemeManager.register_theme(
                name=theme_def['name'],
                display_name=theme_def['display_name'],
                ui_colors=theme_def['ui'],
                gtp_colors=theme_def['gtp'],
            )
            loaded_count += 1
        except Exception as e:
            print(f"[主题加载] 注册主题失败 '{entry}': {e}")

    print(f"[主题加载] 共加载 {loaded_count} 个自定义主题")
    return loaded_count
