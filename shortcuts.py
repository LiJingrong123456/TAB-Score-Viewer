# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Shortcut Customization
快捷键管理模块

提供:
  - :data:`MODIFIER_KEYS`: 不能单独作为快捷键的修饰键集合
  - :data:`KEY_NAME_MAP`: Qt.Key -> 显示名 映射
  - :class:`ShortcutAction`: 操作元数据 dataclass
  - :data:`DEFAULT_SHORTCUTS`: 默认注册的操作列表 (11 个)
  - :class:`ShortcutManager`: 单例,负责解析/校验/查表
  - :func:`sequence_to_display`: 把 "Ctrl+Shift+Z" 渲染成 "Ctrl + Shift + Z"

Usage Example
-------------
>>> from shortcuts import ShortcutManager, DEFAULT_SHORTCUTS
>>> mgr = ShortcutManager.instance()
>>> mgr.set_custom("play_pause", "Ctrl+Shift+P")
>>> mgr.lookup("Ctrl+Shift+P")
'play_pause'
>>> mgr.parse_sequence("Ctrl+Z")
({'Ctrl', 'Z'}, True)
>>> mgr.parse_sequence("Ctrl+Shift")  # 仅修饰键
(set(), False)
"""
from __future__ import annotations

import sys
import platform as _platform_mod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Qt 导入容错: 当环境无 PyQt5 时允许 map 为空,避免在 CLI 场景崩溃
# ---------------------------------------------------------------------------
try:  # pragma: no cover - 由环境决定是否可用
    from PyQt5.QtCore import Qt  # type: ignore
except Exception:  # pragma: no cover
    Qt = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 修饰键集合 (不能单独作为快捷键)
# ---------------------------------------------------------------------------
MODIFIER_KEYS: Set[str] = {
    "Ctrl",
    "Shift",
    "Alt",
    "Option",
    "Meta",
    "Win",
    "Super",
    "Command",
    "CapsLock",
    "Caps",  # 别名
    "Tab",
}

# 用于解析事件时把 Qt modifier flags 翻译为统一名称
_MODIFIER_FLAG_TO_NAME: Dict[int, str] = {}
if Qt is not None:
    _MODIFIER_FLAG_TO_NAME = {
        Qt.ControlModifier: "Ctrl",
        Qt.ShiftModifier: "Shift",
        Qt.AltModifier: "Alt",       # macOS 上 Alt 叫 Option,这里统一叫 Alt
        Qt.MetaModifier: "Meta",     # macOS Command / Windows Win / Linux Super
    }

# Qt.MetaModifier 在不同平台的语义略有差异(macOS=Command, Windows=Win, Linux=Super)
# 当用户写 "Option" / "Win" / "Super" / "Command" / "Cmd" 时,把它们都视作元修饰键
# 注意: Option 是 Mac 上 Alt 键的命名,属于 Alt 族,不是 Meta 族
_META_ALIASES: Set[str] = {"Meta", "Win", "Super", "Command", "Cmd"}

# 用于校验/排序时把 "Option/Win/Super/Command" 归到 Meta 的同一族
_MODIFIER_CANONICAL: Dict[str, str] = {
    "Ctrl": "Ctrl",
    "Shift": "Shift",
    "Alt": "Alt",
    "Option": "Alt",      # macOS 习惯命名 (Option = Alt)
    "Meta": "Meta",
    "Win": "Meta",        # Windows 键
    "Super": "Meta",      # Linux Super 键
    "Command": "Meta",    # macOS Command 键
    "Cmd": "Meta",        # macOS Command 键 (缩写)
    "CapsLock": "CapsLock",
    "Caps": "CapsLock",
    "Tab": "Tab",
}

# 输出时的固定排序:Ctrl -> Shift -> Alt/Option -> Meta/Win/Cmd -> Key
_MODIFIER_ORDER: List[str] = ["Ctrl", "Shift", "Alt", "Meta", "Cmd", "Win", "Super", "CapsLock", "Tab"]


# ---------------------------------------------------------------------------
# 平台检测 (必须在使用它的常量之前定义)
# ---------------------------------------------------------------------------
_IS_MAC: bool = sys.platform == "darwin"


# ---------------------------------------------------------------------------
# Meta 修饰键的显示名 (Win/Super/Cmd)
# ---------------------------------------------------------------------------


# 排序键值 (用于 event_to_sequence 与 _normalize_sequence)
# 跨平台保持一致: Ctrl → Shift → Alt → OS-specific-modifier → CapsLock → Tab
# Mac 上虽然 "Cmd" 是主修饰键, 但为了与 Windows/Linux 兼容, 把 "Cmd" 也
# 放在与 Meta/Win/Super 相同的位置 (3), 这样用户在 Mac 上设置 "Ctrl+Shift+P"
# 后看到的规范化字符串仍然是 "Ctrl+Shift+P" 而不是 "Shift+Ctrl+P", 与其它
# 平台保持一致。
_MODIFIER_SORT_KEY: Dict[str, int] = {
    "Ctrl": 0,
    "Shift": 1,
    "Alt": 2,
    "Cmd": 3, "Meta": 3, "Win": 3, "Super": 3,  # OS-specific modifier
    "CapsLock": 4,
    "Tab": 5,
}


# ---------------------------------------------------------------------------
# 平台感知: 根据操作系统决定 Qt.MetaModifier 显示为 Cmd / Win / Super
# ---------------------------------------------------------------------------
def _detect_meta_display_name() -> str:
    """根据当前操作系统返回 Qt.MetaModifier 的友好显示名。

    - macOS / Darwin : "Cmd"   (用户认知中的 Command 键)
    - Windows        : "Win"   (Windows 键)
    - Linux / 其他   : "Super" (Linux 上的 Super 键)
    - Qt 不可用      : "Meta"  (兜底,跨平台中性名)
    """
    # 优先用 sys.platform (更快, 避免 platform.system 内部 fork)
    plat = sys.platform
    if plat == "darwin":
        return "Cmd"
    if plat.startswith("win"):
        return "Win"
    if plat.startswith("linux") or plat.startswith("freebsd") or plat.startswith("openbsd"):
        return "Super"
    # 兜底: 用 platform.system() 再判断一次
    try:
        name = _platform_mod.system()
        if name == "Darwin":
            return "Cmd"
        if name == "Windows":
            return "Win"
        if name == "Linux":
            return "Super"
    except Exception:
        pass
    return "Meta"


_META_DISPLAY_NAME: str = _detect_meta_display_name()


# ---------------------------------------------------------------------------
# 修饰键的 Qt.Key 枚举值 → 显示名映射
# ---------------------------------------------------------------------------
# 用于 event_to_sequence 中的"平台修正"逻辑。
# 当 event.key() 本身就是修饰键时,直接用此映射返回,绕过 event.modifiers()
# 中可能包含的所有修饰键标志位 (Mac 平台 bug)。
#
# **Mac Qt 平台特殊行为 (v2.5.2+)**:
#   Qt 在 macOS 上会"互换" Ctrl 和 Cmd 的语义:
#     - 物理 Command (⌘) → Qt 报告为 Qt.Key_Control + Qt.ControlModifier
#     - 物理 Control  (^) → Qt 报告为 Qt.Key_Meta    + Qt.MetaModifier
#   因此,为了让"显示名"与用户**实际按下的物理键**一致,
#   必须在 Mac 上做 swap。
# (注意: _IS_MAC 已在文件靠前位置定义)

_MODIFIER_KEY_MAP: Dict[int, str] = {}  # 延迟构造,等 Qt 可用时填充


def _build_modifier_key_map() -> Dict[int, str]:
    """构造 Qt.Key_* 修饰键枚举值 → 显示名字典。Qt 不可用时返回空 dict。

    **左右键覆盖 (v2.5.2+)**:
        Mac 上按左/右 Cmd 时,Qt 可能报告:
          - Key_Control   (左 ⌘)
          - Key_Control_R (右 ⌘)
        按左/右 ^ 时:
          - Key_Meta   (左 ^)
          - Key_Meta_R (右 ^)
        如果 _MODIFIER_KEY_MAP 只包含 Key_Control/Key_Meta, 当用户按右 ⌘ 时
        early return 不会触发, event_to_sequence 会走 fallback 把
        event.modifiers() 的所有 4 个 flag 都输出, 触发 "max 3 keys" 误报。

        类似地, 非 Mac 平台上 Qt.Key_Control_L/R 可能是左右 Ctrl,
        Qt.Key_Meta_L/R 可能是左右 Super/Win, 也要覆盖。
    """
    if Qt is None:
        return {}
    m: Dict[int, str] = {}
    if _IS_MAC:
        # Mac 物理键: ⌘ = Qt.Key_Control(+L/R), ^ = Qt.Key_Meta(+L/R)
        m[Qt.Key_Control] = "Cmd"   # 左 ⌘
        m[Qt.Key_Meta] = "Ctrl"     # 左 ^
        # 左右键 (Mac 上 Key_Control_R = 右 ⌘, Key_Meta_R = 右 ^)
        for k_attr, name in (
            ("Key_Control_L", "Cmd"),
            ("Key_Control_R", "Cmd"),
            ("Key_Meta_L", "Ctrl"),
            ("Key_Meta_R", "Ctrl"),
        ):
            k = getattr(Qt, k_attr, None)
            if k is not None:
                m[int(k)] = name
        # Mac 上某些 Qt 版本/键盘布局可能把 ⌘ 报告为 Key_Super_L/R
        # (例如外接键盘或某些 Mac mini 机型)
        for k_attr in ("Key_Super_L", "Key_Super_R"):
            k = getattr(Qt, k_attr, None)
            if k is not None and k not in m:
                m[int(k)] = "Cmd"
    else:
        m[Qt.Key_Control] = "Ctrl"
        m[Qt.Key_Meta] = _META_DISPLAY_NAME  # Win/Super
        for k_attr in ("Key_Control_L", "Key_Control_R",
                       "Key_Meta_L", "Key_Meta_R",
                       "Key_Super_L", "Key_Super_R"):
            k = getattr(Qt, k_attr, None)
            if k is not None and k not in m:
                if k_attr.startswith("Key_Control"):
                    m[int(k)] = "Ctrl"
                else:
                    m[int(k)] = _META_DISPLAY_NAME
    m[Qt.Key_Shift] = "Shift"
    m[Qt.Key_Alt] = "Alt"  # Mac 上 Option 键也产生 Qt.Key_Alt
    # Shift_L/R / Alt_L/R (左右 Shift/Option)
    for k_attr in ("Key_Shift_L", "Key_Shift_R", "Key_Alt_L", "Key_Alt_R"):
        k = getattr(Qt, k_attr, None)
        if k is not None and k not in m:
            if k_attr.startswith("Key_Shift"):
                m[int(k)] = "Shift"
            else:
                m[int(k)] = "Alt"
    return m


_MODIFIER_KEY_MAP = _build_modifier_key_map()


# ---------------------------------------------------------------------------
# Qt.Key -> 显示名 映射
# ---------------------------------------------------------------------------
def _build_key_name_map() -> Dict[int, str]:
    """构造 KEY_NAME_MAP,Qt 不可用时返回空 dict。"""
    if Qt is None:
        return {}
    mapping: Dict[int, str] = {}

    # 空白 / 常用控制
    mapping[Qt.Key_Space] = "Space"
    mapping[Qt.Key_Tab] = "Tab"
    mapping[Qt.Key_Backspace] = "Backspace"
    mapping[Qt.Key_Delete] = "Delete"
    mapping[Qt.Key_Insert] = "Insert"
    mapping[Qt.Key_Return] = "Return"
    mapping[Qt.Key_Enter] = "Enter"
    mapping[Qt.Key_Escape] = "Escape"

    # 方向键
    mapping[Qt.Key_Up] = "Up"
    mapping[Qt.Key_Down] = "Down"
    mapping[Qt.Key_Left] = "Left"
    mapping[Qt.Key_Right] = "Right"

    # 导航
    mapping[Qt.Key_Home] = "Home"
    mapping[Qt.Key_End] = "End"
    mapping[Qt.Key_PageUp] = "PageUp"
    mapping[Qt.Key_PageDown] = "PageDown"

    # F1 - F12
    for i in range(1, 13):
        mapping[getattr(Qt, f"Key_F{i}")] = f"F{i}"

    # 标点/编辑键 (常见的几个)
    mapping[Qt.Key_Semicolon] = ";"
    mapping[Qt.Key_Comma] = ","
    mapping[Qt.Key_Period] = "."
    mapping[Qt.Key_Slash] = "/"
    mapping[Qt.Key_Backslash] = "\\"
    mapping[Qt.Key_BracketLeft] = "["
    mapping[Qt.Key_BracketRight] = "]"
    mapping[Qt.Key_QuoteLeft] = "`"
    mapping[Qt.Key_Apostrophe] = "'"
    mapping[Qt.Key_Minus] = "-"
    mapping[Qt.Key_Equal] = "="
    mapping[Qt.Key_Plus] = "+"
    mapping[Qt.Key_Question] = "?"

    return mapping


KEY_NAME_MAP: Dict[int, str] = _build_key_name_map()


# ---------------------------------------------------------------------------
# KEY_NAME_MAP 之外的字母/数字键兜底映射
# ---------------------------------------------------------------------------
# KEY_NAME_MAP 已包含 Space / 方向键 / F1-F12 / 标点,
# 但不包含 A-Z / 0-9 等"通过 event.text() 获取"的键。
# 在 _qt_key_to_name 中,event.text() 为空时 (例如某些合成事件) 退化到此映射。
def _build_qt_key_fallback() -> Dict[int, str]:
    """构造 A-Z / 0-9 等 fallback 映射。Qt 不可用时返回空 dict。"""
    if Qt is None:
        return {}
    fb: Dict[int, str] = {}
    # A-Z
    for i in range(26):
        k = getattr(Qt, f"Key_{chr(ord('A') + i)}", None)
        if k is not None:
            fb[int(k)] = chr(ord('A') + i)
    # 0-9
    for i in range(10):
        k = getattr(Qt, f"Key_{i}", None)
        if k is not None:
            fb[int(k)] = str(i)
    return fb


_QT_KEY_FALLBACK: Dict[int, str] = _build_qt_key_fallback()


# ---------------------------------------------------------------------------
# 操作元数据
# ---------------------------------------------------------------------------
@dataclass
class ShortcutAction:
    """单个可自定义快捷键的操作元数据。

    Attributes:
        id:            操作的唯一 ID (持久化时用)
        name_key:      国际化键,如 ``shortcuts.play_pause``
        default_key:   默认快捷键序列,如 ``"Ctrl+Z"`` / ``"Space"``
        callback_attr: 在 :class:`DisplayWindow` 上要调用的方法名
    """

    id: str
    name_key: str
    default_key: str
    callback_attr: str


DEFAULT_SHORTCUTS: List[ShortcutAction] = [
    ShortcutAction(
        id="play_pause",
        name_key="shortcuts.play_pause",
        default_key="Space",
        callback_attr="toggle_playback",
    ),
    ShortcutAction(
        id="scroll_up",
        name_key="shortcuts.scroll_up",
        default_key="Up",
        callback_attr="_scroll_up",
    ),
    ShortcutAction(
        id="scroll_down",
        name_key="shortcuts.scroll_down",
        default_key="Down",
        callback_attr="_scroll_down",
    ),
    ShortcutAction(
        id="speed_down",
        name_key="shortcuts.speed_down",
        default_key="Left",
        callback_attr="_speed_down",
    ),
    ShortcutAction(
        id="speed_up",
        name_key="shortcuts.speed_up",
        default_key="Right",
        callback_attr="_speed_up",
    ),
    ShortcutAction(
        id="fullscreen",
        name_key="shortcuts.fullscreen",
        default_key="F11",
        callback_attr="toggle_fullscreen",
    ),
    ShortcutAction(
        id="exit_or_close",
        name_key="shortcuts.exit_or_close",
        default_key="Escape",
        callback_attr="_exit_or_close",
    ),
    ShortcutAction(
        id="anno_undo",
        name_key="shortcuts.anno_undo",
        default_key="Ctrl+Z",
        callback_attr="_anno_undo",
    ),
    ShortcutAction(
        id="anno_redo",
        name_key="shortcuts.anno_redo",
        default_key="Ctrl+Y",
        callback_attr="_anno_redo",
    ),
    ShortcutAction(
        id="anno_create",
        name_key="shortcuts.anno_create",
        default_key="Ctrl+K",
        callback_attr="_create_annotation_at_cursor",
    ),
    ShortcutAction(
        id="metronome_toggle",
        name_key="shortcuts.metronome_toggle",
        default_key="Ctrl+M",
        callback_attr="_metronome_toggle",
    ),
    ShortcutAction(
        id="tuner_toggle",
        name_key="shortcuts.tuner_toggle",
        default_key="Ctrl+T",
        callback_attr="_open_tuner",
    ),
]


# ---------------------------------------------------------------------------
# ShortcutManager 单例
# ---------------------------------------------------------------------------
class ShortcutManager:
    """快捷键注册/解析/校验/查表 (单例)。

    关键方法:
      - :meth:`set_custom` / :meth:`set_custom_bulk` / :meth:`clear_all`
      - :meth:`get_key` / :meth:`get_action`
      - :meth:`event_to_sequence` / :meth:`parse_sequence`
      - :meth:`lookup` / :meth:`find_conflict` / :meth:`validate`
    """

    _instance: Optional["ShortcutManager"] = None

    def __new__(cls) -> "ShortcutManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        # action_id -> key_seq,空字符串表示该操作被禁用
        self._custom: Dict[str, str] = {}

    # ------------------------------------------------------------------ 工厂
    @classmethod
    def instance(cls) -> "ShortcutManager":
        """获取单例。"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_singleton(cls) -> None:
        """重置单例 (主要用于测试)。"""
        cls._instance = None

    # ------------------------------------------------------------------ 写入
    def set_custom(self, action_id: str, key_seq: str) -> None:
        """设置自定义快捷键。

        Args:
            action_id: :data:`DEFAULT_SHORTCUTS` 中某个操作的 ID
            key_seq:   序列字符串,如 ``"Ctrl+Shift+P"``;空字符串表示禁用
        """
        if not action_id:
            return
        # 规范化: 把 Option/Win/Super/Command 等别名归到 Alt/Meta
        norm = self._normalize_sequence(key_seq)
        self._custom[action_id] = norm

    def set_custom_bulk(self, custom_dict: Dict[str, str]) -> None:
        """批量加载用户自定义。空字符串表示禁用。"""
        if not custom_dict:
            return
        for action_id, key_seq in custom_dict.items():
            self.set_custom(action_id, key_seq or "")

    def clear_all(self) -> None:
        """清空所有自定义,所有操作恢复默认快捷键。"""
        self._custom.clear()

    def remove_custom(self, action_id: str) -> None:
        """移除某个操作的自定义 (恢复默认)。"""
        self._custom.pop(action_id, None)

    # ------------------------------------------------------------------ 读取
    def get_key(self, action_id: str) -> str:
        """获取最终快捷键序列。

        优先级: 用户自定义 > 默认 > 空字符串。
        若用户自定义为空字符串 (禁用),直接返回空字符串。
        """
        if action_id in self._custom:
            return self._custom[action_id]
        for action in DEFAULT_SHORTCUTS:
            if action.id == action_id:
                return action.default_key
        return ""

    def get_action(self, action_id: str) -> Optional[ShortcutAction]:
        """根据 ID 查找 :class:`ShortcutAction`。"""
        for action in DEFAULT_SHORTCUTS:
            if action.id == action_id:
                return action
        return None

    # ------------------------------------------------------------------ 解析
    def event_to_sequence(self, event: Any) -> str:
        """把 :class:`QKeyEvent` 转成 ``"Ctrl+Shift+Z"`` 字符串。

        排序规则:Ctrl -> Shift -> Alt -> Meta -> (CapsLock) -> Tab -> Key。

        **平台修正** (v2.5.2+):
            1. **Mac Qt 互换 Ctrl/Cmd 语义**:Qt 在 macOS 上把物理 Command (⌘)
               报告为 ``Qt.Key_Control`` + ``Qt.ControlModifier``,把物理 Control (^)
               报告为 ``Qt.Key_Meta`` + ``Qt.MetaModifier``。本函数会把这些
               "Qt 名" 重新映射为"用户物理按键名":
                 - Mac: ``Qt.ControlModifier`` → "Cmd" (⌘), ``Qt.MetaModifier`` → "Ctrl" (^)
                 - 其它平台: 保持原语义

            2. **Mac modifier press bug**:Mac 上按 Control 时,Qt 会在
               ``event.modifiers()`` 中报告**所有**修饰键标志。本函数会检测
               当 ``event.key()`` 本身是修饰键时,只输出对应的修饰键,
               避免 ``"Ctrl+Shift+Alt+Cmd"`` 这种误报。

            3. **Mac 单独修饰键事件 (v2.5.2 second pass)**:
               某些 Qt 版本/系统组合下,按 Command 时 ``event.key()`` 可能是
               ``0`` 或 ``Qt.Key_unknown`` (而不是 ``Qt.Key_Control``),同时
               ``event.modifiers()`` 报告所有 4 个 modifier flags. 此时早期
               return (修正 #2) 不会触发, 会走 fallback 路径输出 4 个 modifier
               触发 "max 3 keys" 误报。修正 #3 专门处理这种情况: 当
               ``event.key() == 0/Key_unknown`` 且只有 modifier flags 时, 按
               优先级输出单个 modifier 名称。
        """
        if event is None:
            return ""

        key = getattr(event, "key", lambda: 0)()

        # 平台修正 #2: 如果按下的键本身是修饰键,只输出该修饰键
        # (Mac 上 modifier press event 会把其他 modifier flag 也置位,这是
        # 系统全局状态,不是用户实际同时按下的组合,必须忽略)
        if Qt is not None and key in _MODIFIER_KEY_MAP:
            return _MODIFIER_KEY_MAP[key]

        # 平台修正 #3 (v2.5.2 second pass):
        # Mac 上某些 Qt 版本/系统组合, 按 Command 时 event.key() 返回 0 或
        # Key_unknown, 此时走不到上面的 early return, 会 fallback 到下面
        # 解析 event.modifiers() 的代码, 把所有 4 个 modifier flag 都输出.
        # 这里专门处理"key 未知 + 只有 modifier flags"的情况.
        if Qt is not None:
            try:
                key_unknown = int(Qt.Key_unknown)
            except (AttributeError, Exception):  # noqa: BLE001
                key_unknown = -1
            if key in (0, key_unknown):
                mods_raw = getattr(event, "modifiers", lambda: 0)()
                # 注意: PyQt5 的 mods 是 Qt.KeyboardModifiers 枚举对象,
                # 不是 int, 直接做位运算会得到 KeyboardModifiers 对象,
                # == 0 比较会失败. 必须先转 int.
                try:
                    mods = int(mods_raw)
                except (TypeError, Exception):  # noqa: BLE001
                    mods = 0
                all_mod_flags = (
                    int(Qt.ShiftModifier) | int(Qt.ControlModifier) |
                    int(Qt.AltModifier) | int(Qt.MetaModifier)
                )
                only_mods = mods & all_mod_flags
                # 必须是"只有 modifier flags", 没有其它 flag (例如按键 lock 等)
                if only_mods and (mods & ~all_mod_flags) == 0:
                    # 按优先级输出第一个 modifier
                    if _IS_MAC:
                        # Mac 物理键: ⌘ = ControlModifier, ^ = MetaModifier,
                        # Option = AltModifier. 用户最常按的是 ⌘, 优先识别
                        if mods & Qt.ControlModifier:
                            return "Cmd"   # 物理 ⌘
                        if mods & Qt.MetaModifier:
                            return "Ctrl"  # 物理 ^
                        if mods & Qt.AltModifier:
                            return "Alt"   # 物理 Option
                        if mods & Qt.ShiftModifier:
                            return "Shift"
                    else:
                        if mods & Qt.ControlModifier:
                            return "Ctrl"
                        if mods & Qt.MetaModifier:
                            return _META_DISPLAY_NAME
                        if mods & Qt.AltModifier:
                            return "Alt"
                        if mods & Qt.ShiftModifier:
                            return "Shift"
                # 如果连 modifier flags 都没有, 这是一个无效事件, 返回空字符串
                if not only_mods:
                    return ""

        # 1) 修饰键 (正常按键情况,event.key() 不是修饰键)
        mods = getattr(event, "modifiers", lambda: 0)()
        present: List[str] = []
        if Qt is not None:
            # 平台修正 #1: Mac 上 Qt 把 Ctrl/Cmd 互换, 显示名要反向回来
            if _IS_MAC:
                # Mac: Qt.ControlModifier 实际是物理 ⌘, Qt.MetaModifier 实际是物理 ^
                mod_pairs = (
                    (Qt.ControlModifier, "Cmd"),   # 物理 ⌘
                    (Qt.ShiftModifier, "Shift"),
                    (Qt.AltModifier, "Alt"),        # 物理 Option
                    (Qt.MetaModifier, "Ctrl"),      # 物理 ^
                )
            else:
                mod_pairs = (
                    (Qt.ControlModifier, "Ctrl"),
                    (Qt.ShiftModifier, "Shift"),
                    (Qt.AltModifier, "Alt"),
                    (Qt.MetaModifier, _META_DISPLAY_NAME),
                )
            for flag, name in mod_pairs:
                if mods & flag:
                    present.append(name)
        # 某些平台会带有 CapsLock / NumLock state,这里保守忽略

        # 2) 主键
        key = getattr(event, "key", lambda: 0)()
        key_name = self._qt_key_to_name(key, event)

        # 3) 排序
        # 注意: _MODIFIER_ORDER 在 Mac 上需要 "Cmd" 和 "Ctrl" 都在合适位置
        # 这里用一个 dict 做键序映射,避免 list.index 对不存在的项报错
        ordered_mods = sorted(
            present,
            key=lambda n: _MODIFIER_SORT_KEY.get(n, 999),
        )
        parts = ordered_mods + ([key_name] if key_name else [])
        return "+".join(parts)

    @staticmethod
    def _qt_key_enum_name(key: int) -> str:
        """把 Qt.Key 枚举值转换为 ``"Z"`` / ``"F1"`` 等短名称。

        PyQt5 的 ``Qt.Key`` 是 int 别名,既不能 ``Qt.Key(key).name`` 也不能迭代
        ``Qt.Key``。因此用 :data:`_QT_KEY_FALLBACK` 静态映射兜底,
        涵盖 A-Z / 0-9 等所有 letter/digit 键 (KEY_NAME_MAP 之外的)。
        """
        if Qt is None:
            return ""
        return _QT_KEY_FALLBACK.get(int(key), "")

    def _qt_key_to_name(self, key: int, event: Any) -> str:
        """Qt 键值 -> 统一名称 (用于显示与持久化)。"""
        if Qt is None:
            return ""
        if key in KEY_NAME_MAP:
            return KEY_NAME_MAP[key]
        # 字母/数字: 优先用 event.text() (大写)
        text = ""
        try:
            text = (event.text() or "") if event is not None else ""
        except Exception:
            text = ""
        if text and text.isprintable():
            return text.upper()
        # 退化: 从 Qt.Key 枚举名拼接 (Key_A -> "A")
        return self._qt_key_enum_name(key)

    def parse_sequence(self, seq: str) -> Tuple[Set[str], bool]:
        """解析序列,返回 ``(keys_set, is_valid)``。

        校验规则:
          1. 拆分后键数 1-3,否则无效
          2. 至少包含 1 个非修饰键,否则无效
        """
        if not seq:
            return (set(), False)

        # 拆分 + 规范化
        raw_keys = [k.strip() for k in seq.split("+")]
        raw_keys = [k for k in raw_keys if k]

        if not raw_keys or len(raw_keys) > 3:
            return (set(), False)

        normalized: List[str] = []
        for k in raw_keys:
            # 规范化别名: Option -> Alt, Win/Super/Command -> Meta, Caps -> CapsLock
            canon = _MODIFIER_CANONICAL.get(k, k)
            normalized.append(canon)

        # 去重,保持顺序
        seen: Set[str] = set()
        uniq: List[str] = []
        for k in normalized:
            if k not in seen:
                uniq.append(k)
                seen.add(k)

        if len(uniq) > 3:
            return (set(), False)

        non_mods = [k for k in uniq if k not in MODIFIER_KEYS and k not in _MODIFIER_CANONICAL]
        # 也要排除 _MODIFIER_CANONICAL 别名映射出的值
        non_mods = [k for k in uniq if k not in {"Ctrl", "Shift", "Alt", "Meta", "CapsLock", "Tab"}]
        if not non_mods:
            return (set(), False)

        return (set(uniq), True)

    # ------------------------------------------------------------------ 查表
    def lookup(self, key_seq: str) -> Optional[str]:
        """根据快捷键序列查找 :attr:`action.id`。

        优先级: 用户自定义 > 默认表。使用**精确匹配**。
        - 若某个操作已有自定义 (含空字符串"禁用"),其默认键**不再响应**,
          避免「同一个动作被两个键同时触发」的问题。
        - 用户的空字符串 ("") 视为禁用,不会在 lookup 中命中。
        """
        if not key_seq:
            return None
        norm = self._normalize_sequence(key_seq)

        # 1) 用户自定义 (空字符串视为禁用, 不参与查表)
        for action_id, custom_seq in self._custom.items():
            if custom_seq and self._normalize_sequence(custom_seq) == norm:
                return action_id

        # 2) 默认 - 跳过"已有自定义"的操作
        for action in DEFAULT_SHORTCUTS:
            if action.id in self._custom:
                continue  # 该操作已被用户自定义, 默认键失效
            if action.default_key and self._normalize_sequence(action.default_key) == norm:
                return action.id
        return None

    def find_conflict(
        self, key_seq: str, exclude_action_id: str = ""
    ) -> Optional[str]:
        """查找与 ``key_seq`` 冲突的 action_id。

        Args:
            key_seq:           待设置的新序列
            exclude_action_id: 排除自身 (用于编辑时)
        """
        if not key_seq:
            return None
        norm = self._normalize_sequence(key_seq)

        # 1) 自定义表
        for action_id, custom_seq in self._custom.items():
            if action_id == exclude_action_id:
                continue
            if custom_seq and self._normalize_sequence(custom_seq) == norm:
                return action_id

        # 2) 默认表 (但要排除"自己原本就占的"那个)
        for action in DEFAULT_SHORTCUTS:
            if action.id == exclude_action_id:
                continue
            if action.default_key and self._normalize_sequence(action.default_key) == norm:
                return action.id
        return None

    # ------------------------------------------------------------------ 校验
    def validate(self, key_seq: str) -> Tuple[bool, str]:
        """校验序列。

        Returns:
            (valid, error_key) —— error_key 是 i18n key,如
            ``"shortcut_invalid_modifier_only"`` / ``"shortcut_max_keys"``,
            校验通过时为 ``""``。
        """
        if not key_seq or not key_seq.strip():
            return (True, "")  # 空序列表示禁用,允许通过

        raw_keys = [k.strip() for k in key_seq.split("+")]
        raw_keys = [k for k in raw_keys if k]
        if len(raw_keys) > 3:
            return (False, "shortcut_max_keys")

        non_mods = [
            k
            for k in raw_keys
            if k not in MODIFIER_KEYS and k not in _MODIFIER_CANONICAL
        ]
        if not non_mods:
            return (False, "shortcut_invalid_modifier_only")
        return (True, "")

    # ------------------------------------------------------------------ 内部
    @staticmethod
    def _normalize_sequence(seq: str) -> str:
        """把 ``"Ctrl+option+P"`` 等变体归一化,便于比较。

        归一化规则:
          1. 拆分 + 去除空白
          2. 通过 :data:`_MODIFIER_CANONICAL` 把别名映射为规范名
             (Option→Alt, Win/Super/Command/Cmd→Meta, Caps→CapsLock)
          3. 修饰键按固定顺序排在主键之前
          4. 同名去重
        """
        if not seq:
            return ""
        parts: List[str] = []
        for k in seq.split("+"):
            k = k.strip()
            if not k:
                continue
            # 别名归一
            k = _MODIFIER_CANONICAL.get(k, k)
            parts.append(k)
        # 修饰键集合: 包含规范名 + 平台显示名 (Cmd/Win/Super)
        # 注意: 在 Mac 上 "Cmd" 和 "Ctrl" 都是修饰键, 都参与排序
        _MOD_SET = {
            "Ctrl", "Shift", "Alt", "Meta", "CapsLock", "Tab",
            "Cmd", "Win", "Super",
        }
        mods = [p for p in parts if p in _MOD_SET]
        others = [p for p in parts if p not in _MOD_SET]
        # 复用 event_to_sequence 的平台感知排序
        mods.sort(key=lambda n: _MODIFIER_SORT_KEY.get(n, 999))
        return "+".join(mods + others)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------
def sequence_to_display(seq: str) -> str:
    """把 ``"Ctrl+Shift+Z"`` 渲染为 ``"Ctrl + Shift + Z"`` (带空格)。"""
    if not seq:
        return ""
    return " + ".join(p for p in seq.split("+") if p)


__all__ = [
    "MODIFIER_KEYS",
    "KEY_NAME_MAP",
    "ShortcutAction",
    "DEFAULT_SHORTCUTS",
    "ShortcutManager",
    "sequence_to_display",
]
