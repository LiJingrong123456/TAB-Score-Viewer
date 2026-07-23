# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Config Module

配置读写和应用

功能:
  - apply_config_settings(): 从配置字典应用语言、主题、字体、GTP 渲染参数
  - _DEFAULT_RENDER_VALUES: 渲染参数默认值快照
  - 启动时检查更新开关: 模块级状态, 由设置面板 / 启动检查逻辑共享
"""

from typing import Dict, Any

from ApolloTab.utils.constants import RenderConfig

from constants import _RENDER_PARAMS
from theme import ThemeManager
from i18n import I18n
from fonts import set_ui_font, get_ui_font_family


# 渲染参数默认值快照（用于"恢复默认"功能）
# 在模块加载时捕获 RenderConfig 类属性的初始值, 避免被运行时修改影响
_DEFAULT_RENDER_VALUES: Dict[str, Any] = {
    attr: getattr(RenderConfig, attr)
    for attr, _, _, _, _, _ in _RENDER_PARAMS
}


# ============================================================
# 启动时检查更新 - 模块级开关
# ============================================================
# 设计原因: settings_dialog 需要读取/写入此值, SelectionWindow 启动时需要读取此值
#   - 真实持久化位置: config/settings.json["check_update_on_startup"]
#   - 启动时由 load_config() 读取并写入本模块的 _CHECK_UPDATE_ON_STARTUP
#   - 设置面板修改时调用 set_check_update_on_startup() 立即更新本模块值
#   - 默认 False（不在用户没有主动开启的情况下打扰用户）

# 默认值（用于"恢复默认"功能）
_DEFAULT_CHECK_UPDATE_ON_STARTUP: bool = False

# 模块级状态 - 由 apply_config_settings() 初始化, 由 set_check_update_on_startup() 更新
_CHECK_UPDATE_ON_STARTUP: bool = _DEFAULT_CHECK_UPDATE_ON_STARTUP


# ============================================================
# 自定义快捷键 - 模块级状态
# ============================================================
# 设计原因: settings_dialog 通过 ShortcutManager.instance() 读写, DisplayWindow 启动时需要读取
#   - 真实持久化位置: config/settings.json["custom_shortcuts"]
#   - 启动时由 apply_config_settings() 读取并注入到 ShortcutManager
#   - 设置面板修改时调用 set_custom_shortcuts() 立即更新
#   - 默认 {} 表示全部走 DEFAULT_SHORTCUTS

# 默认值（用于"恢复默认"功能）
_DEFAULT_CUSTOM_SHORTCUTS: Dict[str, str] = {}


def get_check_update_on_startup() -> bool:
    """获取「启动时检查更新」当前值"""
    return _CHECK_UPDATE_ON_STARTUP


def set_check_update_on_startup(value: bool) -> None:
    """设置「启动时检查更新」当前值（立即生效，持久化由 save_config() 负责）"""
    global _CHECK_UPDATE_ON_STARTUP
    _CHECK_UPDATE_ON_STARTUP = bool(value)


def get_custom_shortcuts() -> Dict[str, str]:
    """获取当前自定义快捷键字典 (副本)"""
    try:
        from shortcuts import ShortcutManager
        return dict(ShortcutManager.instance()._custom)
    except Exception:
        return dict(_DEFAULT_CUSTOM_SHORTCUTS)


def set_custom_shortcuts(custom: Dict[str, str]) -> None:
    """
    设置自定义快捷键 (立即生效, 持久化由 save_config() 负责)

    参数:
        custom: {action_id: key_seq_str} 字典; 空字符串表示禁用
    """
    try:
        from shortcuts import ShortcutManager
        ShortcutManager.instance().set_custom_bulk(custom or {})
    except Exception:
        pass


def apply_config_settings(cfg: dict) -> None:
    """
    从配置字典应用语言、主题、字体和 GTP 渲染参数

    参数:
        cfg: 从 config/settings.json 读取到的字典

    说明:
        兼容旧配置: 缺少新字段时使用 RenderConfig 默认值, 不报错
    """
    # 语言
    lang = cfg.get("language", "zh_CN")
    if lang != I18n.current_language():
        I18n.set_language(lang)

    # 主题
    theme = cfg.get("theme", "dark")
    if theme != ThemeManager.current_name():
        ThemeManager.set_theme(theme)

    # UI 字体
    ui_font = cfg.get("ui_font")
    set_ui_font(ui_font if ui_font else None)

    # GTP 渲染字体
    gtp_font = cfg.get("gtp_font")
    if gtp_font:
        RenderConfig.NOTE_FONT_FAMILY = gtp_font

    # 启动时检查更新（兼容旧配置: 缺失字段时为 False）
    set_check_update_on_startup(bool(cfg.get("check_update_on_startup", False)))

    # 自定义快捷键 (兼容旧配置: 缺失字段时使用默认)
    custom_shortcuts = cfg.get("custom_shortcuts", {})
    if isinstance(custom_shortcuts, dict):
        set_custom_shortcuts(custom_shortcuts)

    # GTP 渲染数值参数
    render_cfg = cfg.get("render_config", {})
    for attr, _, typ, *_ in _RENDER_PARAMS:
        if attr not in render_cfg:
            continue
        try:
            val = render_cfg[attr]
            if typ is int:
                val = int(val)
            elif typ is float:
                val = float(val)
            setattr(RenderConfig, attr, val)
        except Exception:
            pass
