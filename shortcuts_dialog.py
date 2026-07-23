# -*- coding: utf-8 -*-
"""
TAB Score Viewer - 快捷键自定义面板
====================================

提供:
  - :class:`ShortcutCaptureEditor`: 单个操作的快捷键捕获/显示单元
  - :class:`ShortcutCustomizeDialog`: 表格形式列出所有可自定义操作的对话框

设计要点:
  - 捕获模式: 点击单元格 -> 进入 capturing 状态 -> 等待下一次按键
  - Esc -> 取消并恢复原值
  - Backspace / Delete -> 清空快捷键 (禁用该操作)
  - Enter -> 确认当前已显示的序列 (或保持空)
  - 其它按键 -> 转序列 -> 校验 -> 通过则发射 capture_finished
  - 点击外部 / 失焦 -> 自动回到 display 模式

Usage Example
-------------
>>> from PyQt5.QtWidgets import QApplication
>>> app = QApplication([])
>>> dialog = ShortcutCustomizeDialog()
>>> dialog.show()
>>> # 修改完成后保存:
>>> custom = dialog.get_current_dict()
>>> ShortcutManager.instance().set_custom_bulk(custom)

依赖:
  - shortcuts.py:  :class:`ShortcutManager` / :data:`DEFAULT_SHORTCUTS`
  - i18n.py:       :class:`I18n`
  - theme.py:      :class:`ThemeManager` / :func:`get_app_icon`
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional, Set

# Qt imports - 若环境无 PyQt5 仍允许模块被 import (仅 UI 不可用)
try:  # pragma: no cover
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QKeyEvent, QKeySequence
    from PyQt5.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    _QT_AVAILABLE = True
except Exception:  # pragma: no cover - 极少见
    _QT_AVAILABLE = False

    class _DummySignal:
        def __init__(self, *args, **kwargs):
            pass

        def connect(self, *args, **kwargs):
            return None

        def emit(self, *args, **kwargs):
            return None

    def pyqtSignal(*args, **kwargs):  # type: ignore
        return _DummySignal()

    Qt = None  # type: ignore[assignment]


from shortcuts import (  # noqa: E402
    DEFAULT_SHORTCUTS,
    MODIFIER_KEYS,
    ShortcutManager,
    _MODIFIER_KEY_MAP,
    _MODIFIER_SORT_KEY,
    sequence_to_display,
)
from i18n import I18n  # noqa: E402
from theme import ThemeManager, get_app_icon  # noqa: E402


# i18n 命名空间前缀
_I18N_SETTINGS = "settings_dialog."
_I18N_SHORTCUT_NAME_PREFIX = "shortcuts."


# ============================================================
# 样式常量 (供 _apply_theme 使用)
# ============================================================
# 捕获模式: 黄色高亮
_CAPTURE_STYLE_LIGHT = "background: #FFF3B0; color: #222; border: 1px solid #E0A000;"
_CAPTURE_STYLE_DARK = "background: #5A4A00; color: #FFD; border: 1px solid #FFA000;"
_DISPLAY_STYLE = ""


# ============================================================
# ShortcutCaptureEditor
# ============================================================
class ShortcutCaptureEditor(QWidget):
    """可点击的快捷键捕获单元。

    显示模式 (mode == "display"):
      - 显示当前 ``current_seq`` (经过 ``sequence_to_display`` 渲染)
      - 鼠标点击 -> 进入 capturing 模式 (发射 ``capture_started``)

    捕获模式 (mode == "capturing"):
      - 显示 ``settings_dialog.shortcut_press_to_set`` 占位文字
      - 监听 ``keyPressEvent``:
        * Esc        -> 取消,发射 ``capture_cancelled``
        * Backspace
          / Delete   -> 清空,发射 ``capture_finished(action_id, "")``
        * Enter      -> 确认当前已显示的 ``current_seq`` (可能为空)
        * 其它       -> 走 :meth:`ShortcutManager.event_to_sequence` 解析
                       校验失败时弹 :class:`QMessageBox`,校验通过则发射
                       ``capture_finished(action_id, new_seq)`` 并退出

    失焦 (focusOutEvent) 时若仍在 capturing,自动取消并恢复原值。
    """

    # ---- signals (类级别声明,PyQt5 硬性要求) -----------------
    capture_started = pyqtSignal(str)           # action_id
    capture_finished = pyqtSignal(str, str)     # (action_id, new_seq)
    capture_cancelled = pyqtSignal(str)         # action_id

    def __init__(self, action_id: str = "", parent: Optional[QWidget] = None) -> None:
        """初始化编辑器。

        Args:
            action_id: 对应的操作 ID (如 ``"play_pause"``)
            parent:    父 QWidget
        """
        super().__init__(parent)
        self.action_id: str = action_id
        self.current_seq: str = ""
        self._mode: str = "display"
        # 记录"修改前"的值,便于 cancel 时回滚
        self._prev_seq: str = ""
        # v2.5.2 third pass: 跟踪捕获模式下用户当前按下的修饰键 (display name set)
        # 解决 Mac 上单独按 modifier 立即弹 "modifier only" 错误、导致用户没机会
        # 按非修饰键的 UX 问题. 同时绕开 Mac "event.modifiers() 报告所有 4 个 flag" bug.
        self._held_modifiers: Set[str] = set()

        # UI 初始化
        self.setFocusPolicy(Qt.StrongFocus if Qt is not None else 0)
        self.setAutoFillBackground(False)
        try:
            self.setAttribute(Qt.WA_StyledBackground, True)  # type: ignore[attr-defined]
        except Exception:
            pass

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)
        self._label = QLabel("", self)
        self._label.setAlignment(Qt.AlignCenter if Qt is not None else 0)
        # 让 label 也能点击 -> 转发到父 widget
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents if Qt is not None else 0, True)  # type: ignore[attr-defined]
        layout.addWidget(self._label)
        self.setLayout(layout)

        self._refresh_display()

    # --------------------------------------------------------
    # 属性
    # --------------------------------------------------------
    @property
    def mode(self) -> str:
        """当前模式: ``"display"`` 或 ``"capturing"``。"""
        return self._mode

    # --------------------------------------------------------
    # 对外方法
    # --------------------------------------------------------
    def set_sequence(self, seq: str) -> None:
        """设置当前显示的快捷键序列。

        Args:
            seq: 序列字符串,如 ``"Ctrl+Shift+P"``;空字符串表示未设置
        """
        self.current_seq = seq or ""
        self._prev_seq = self.current_seq
        self._refresh_display()

    def start_capture(self) -> None:
        """主动进入捕获模式 (供外部调用)。"""
        if self._mode == "capturing":
            return
        self._enter_capture_mode()

    def cancel_capture(self) -> None:
        """主动退出捕获模式并恢复原值。"""
        if self._mode != "capturing":
            return
        self._mode = "display"
        self.current_seq = self._prev_seq
        self._held_modifiers.clear()
        self._refresh_display()
        try:
            self.capture_cancelled.emit(self.action_id)
        except Exception:
            pass

    # --------------------------------------------------------
    # 事件
    # --------------------------------------------------------
    def mousePressEvent(self, event):  # type: ignore[override]
        """点击进入捕获模式。"""
        if self._mode == "capturing":
            # 已经在捕获中,把焦点抢回来即可
            self.setFocus()
            return
        # 其它按钮 (如右键) 不响应
        try:
            if event.button() != Qt.LeftButton:
                return super().mousePressEvent(event)
        except Exception:
            pass
        self._enter_capture_mode()
        try:
            self.setFocus()
        except Exception:
            pass

    def keyPressEvent(self, event):  # type: ignore[override]
        """捕获模式下处理按键。

        v2.5.2 third pass 重构: 引入 ``_held_modifiers`` 状态, 单独按修饰键
        时不再弹错误, 而是静默跟踪, 等待用户按下非修饰键后才校验整个组合。
        关键点:
          - 单按修饰键 (event_to_sequence 全部返回 modifier name) -> 加入
            ``_held_modifiers``, 显示 "Cmd + ..." 提示, 不退出 capture
          - 按非修饰键 -> 用 ``_held_modifiers`` + 当前 key 合成最终序列, 校验
          - **不使用** event.modifiers() 的 flag, 因为 Mac 会报告所有 4 个 flag
            (Mac bug), 改用自己累积的 held 状态

        v2.5.2 fourth pass: 在入口处显式判断修饰键 (``event.key() in
        _MODIFIER_KEY_MAP``), 不依赖 ``event_to_sequence`` 的输出。
        Mac 上某些版本/键盘布局下, ``event_to_sequence`` 可能因 modifier
        press bug (event.modifiers() 报告所有 4 个 flag) 而返回包含非修饰键
        部分的字符串,导致误触"非修饰键"错误。直接根据 Qt 键码判断最稳。
        """
        if self._mode != "capturing":
            return super().keyPressEvent(event)

        # 平台修正 (v2.5.2): 忽略 autorepeat 事件, 防止按住修饰键时
        # 反复弹错误对话框 (Mac 上尤其严重)
        try:
            if event.isAutoRepeat():
                event.accept()
                return
        except Exception:
            pass

        key = event.key() if event is not None else 0

        # Esc -> 取消
        if key == Qt.Key_Escape:
            self._mode = "display"
            self.current_seq = self._prev_seq
            self._held_modifiers.clear()
            self._refresh_display()
            try:
                self.capture_cancelled.emit(self.action_id)
            except Exception:
                pass
            event.accept()
            return

        # Backspace / Delete -> 清空
        if key in (Qt.Key_Backspace, Qt.Key_Delete):
            self._mode = "display"
            self.current_seq = ""
            self._held_modifiers.clear()
            self._refresh_display()
            try:
                self.capture_finished.emit(self.action_id, "")
            except Exception:
                pass
            event.accept()
            return

        # Enter / Return -> 确认 (使用 prev_seq 作为结果,可能为空)
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self._mode = "display"
            # 若用户已经在 capturing 中间显示了某个序列 (current_seq),
            # 我们把它作为结果;否则回退到 prev_seq
            result = self.current_seq or self._prev_seq
            self.current_seq = result
            self._prev_seq = result
            self._held_modifiers.clear()
            self._refresh_display()
            try:
                self.capture_finished.emit(self.action_id, result)
            except Exception:
                pass
            event.accept()
            return

        # === v2.5.2 fourth pass: 入口处显式识别修饰键 ===
        # 优先级: 修饰键的 key() 在 _MODIFIER_KEY_MAP 中 → 一定按修饰键处理
        # 完全绕过 event_to_sequence / event.modifiers() (Mac 平台 bug).
        # 这保证单按 Cmd/Ctrl/Alt/Shift 在任何 Mac 平台/键盘布局下都
        # 静默加入 _held_modifiers, 不会触发任何错误对话框.
        if key in _MODIFIER_KEY_MAP:
            self._held_modifiers.add(_MODIFIER_KEY_MAP[key])
            self._show_held_progress()
            event.accept()
            return

        # === v2.5.2 fourth pass: 兼容 key=0/Key_unknown (Mac 平台 bug) ===
        # Mac 上某些版本/键盘布局下, 单按 Cmd 会报告 event.key()=0/Key_unknown
        # 而非 Key_Control. 此时 key 不在 _MODIFIER_KEY_MAP, 但
        # event.modifiers() 报告所有 4 个 flag. 用 event.modifiers() 启发式
        # 判断 "只有 modifier flags, 没有其它" → 视为修饰键事件.
        if Qt is not None and key in (0, int(Qt.Key_unknown) if hasattr(Qt, "Key_unknown") else -1):
            try:
                mods_raw = getattr(event, "modifiers", lambda: 0)()
                mods = int(mods_raw) if mods_raw is not None else 0
            except Exception:
                mods = 0
            all_mod_flags = (
                int(Qt.ShiftModifier) | int(Qt.ControlModifier) |
                int(Qt.AltModifier) | int(Qt.MetaModifier)
            )
            # 必须只有 modifier flags (Mac bug 下 all 4 都置位,符合)
            only_mods = mods & all_mod_flags
            extras = mods & ~all_mod_flags
            if only_mods and not extras:
                # 启发式映射: Mac 上 ControlModifier 优先识别为 Cmd
                if int(Qt.ControlModifier) & mods:
                    self._held_modifiers.add("Cmd")
                elif int(Qt.MetaModifier) & mods:
                    self._held_modifiers.add("Ctrl")
                elif int(Qt.AltModifier) & mods:
                    self._held_modifiers.add("Alt")
                elif int(Qt.ShiftModifier) & mods:
                    self._held_modifiers.add("Shift")
                self._show_held_progress()
                event.accept()
                return

        # 其它键 -> 用 event_to_sequence 解析
        mgr = ShortcutManager.instance()
        try:
            seq = mgr.event_to_sequence(event)
        except Exception:
            seq = ""

        if not seq:
            # 没解析出任何东西 (例如 Qt.Key_unknown 等极端情况)
            return

        parts = [k for k in seq.split("+") if k]
        _ALL_MODIFIER_NAMES = MODIFIER_KEYS | {"Cmd", "Win", "Super", "Option", "Command"}
        _CANONICAL_MODS = {"Ctrl", "Shift", "Alt", "Meta", "CapsLock", "Tab"}
        non_mods = [
            k for k in parts
            if k not in _ALL_MODIFIER_NAMES and k not in _CANONICAL_MODS
        ]

        if not non_mods:
            # === 纯修饰键事件 (防御性, 通常在前面已经被入口处理) ===
            # Mac 上 event_to_sequence 用 early return 只返回刚按下的那一个
            # modifier (如 "Shift"), 所以我们必须 **追加** 到 _held_modifiers
            # (而不是替换), 否则用户按 Cmd+Shift 时第二次 press 会把 Cmd 丢掉.
            mod_parts = [
                k for k in parts
                if k in _ALL_MODIFIER_NAMES or k in _CANONICAL_MODS
            ]
            for m in mod_parts:
                self._held_modifiers.add(m)
            self._show_held_progress()
            event.accept()
            return

        # === 非修饰键事件, 合成最终序列 ===
        # 关键: 只使用 _held_modifiers, 不用 event.modifiers() / event_to_sequence
        # 解析出的 modifier 部分. 因为 Mac 上 event_to_sequence 会把 4 个 flag 全
        # 输出, 污染最终序列. 而 _held_modifiers 是从实际 modifier press 事件累积,
        # 反映用户真实按下的组合.
        key_name = non_mods[0]  # 主键 (非修饰键部分)
        held_sorted = sorted(
            self._held_modifiers,
            key=lambda n: _MODIFIER_SORT_KEY.get(n, 999),
        )
        seq_parts = held_sorted + [key_name]

        if len(seq_parts) > 3:
            self._show_invalid("shortcut_max_keys")
            self._mode = "display"
            self.current_seq = self._prev_seq
            self._held_modifiers.clear()
            self._refresh_display()
            event.accept()
            return

        # 通过 ShortcutManager 再做一次正式校验 (防御性)
        # 注意: 此时 non_mods 必非空 (已通过上面的 if not non_mods 检查),
        # 所以唯一可能失败的原因是 max 3 keys (parse_sequence 内部也会检查).
        # 因此这里不再需要"modifier only"分支 (那是死代码).
        candidate = "+".join(seq_parts)
        try:
            keys_set, valid = mgr.parse_sequence(candidate)
            if not valid:
                self._show_invalid("shortcut_max_keys")
                self._mode = "display"
                self.current_seq = self._prev_seq
                self._held_modifiers.clear()
                self._refresh_display()
                event.accept()
                return
        except Exception:
            # parse_sequence 异常时仍以本地校验为准
            pass

        # 通过 -> 提交
        self._mode = "display"
        self.current_seq = candidate
        self._prev_seq = candidate
        self._held_modifiers.clear()
        self._refresh_display()
        try:
            self.capture_finished.emit(self.action_id, candidate)
        except Exception:
            pass
        event.accept()

    def focusOutEvent(self, event):  # type: ignore[override]
        """失焦时若在 capturing 模式,自动取消 (恢复原值)。"""
        if self._mode == "capturing":
            self._mode = "display"
            self.current_seq = self._prev_seq
            self._held_modifiers.clear()
            self._refresh_display()
            try:
                self.capture_cancelled.emit(self.action_id)
            except Exception:
                pass
        try:
            super().focusOutEvent(event)
        except Exception:
            pass

    def keyReleaseEvent(self, event):  # type: ignore[override]
        """v2.5.2 third pass: 捕获模式下的修饰键释放事件.

        当用户释放一个修饰键时, 从 ``_held_modifiers`` 中移除, 这样后续按
        下的非修饰键组合就是用户最终想要的 (例如: 按 Cmd -> 释放 Cmd -> 按 Z,
        最终序列是 "Z" 而不是 "Cmd+Z").
        """
        if self._mode != "capturing":
            return super().keyReleaseEvent(event)

        # autorepeat 过滤 (release 也会有 autorepeat)
        try:
            if event.isAutoRepeat():
                event.accept()
                return
        except Exception:
            pass

        if Qt is None or event is None:
            return

        key = event.key() if event is not None else 0
        # 复用 _MODIFIER_KEY_MAP (与 keyPressEvent 同样的早返回映射)
        if key in _MODIFIER_KEY_MAP:
            self._held_modifiers.discard(_MODIFIER_KEY_MAP[key])
            self._show_held_progress()
            event.accept()
            return

        return super().keyReleaseEvent(event)

    # --------------------------------------------------------
    # 内部
    # --------------------------------------------------------
    def _enter_capture_mode(self) -> None:
        self._prev_seq = self.current_seq
        self._mode = "capturing"
        # v2.5.2 third pass: 清空 modifier 跟踪状态
        self._held_modifiers.clear()
        # 捕获模式占位文字
        try:
            self._label.setText(I18n.t(_I18N_SETTINGS + "shortcut_press_to_set"))
        except Exception:
            self._label.setText("Press a key...")
        # 视觉高亮 (与 theme 兼容)
        self._apply_capture_style()
        # tooltip
        try:
            self.setToolTip(I18n.t(_I18N_SETTINGS + "shortcut_capture_hint"))
        except Exception:
            self.setToolTip("Esc 取消 / Backspace 清空 / Enter 确认")
        # 抢焦点
        try:
            self.setFocus()
        except Exception:
            pass
        # 通知父
        try:
            self.capture_started.emit(self.action_id)
        except Exception:
            pass

    def _show_held_progress(self) -> None:
        """v2.5.2 third pass: 在 capture 模式下显示已按下的修饰键 + 提示.

        例: 用户按了 Cmd 和 Shift, 显示 "Cmd + Shift + ..."
        """
        if not self._held_modifiers:
            try:
                self._label.setText(I18n.t(_I18N_SETTINGS + "shortcut_press_to_set"))
            except Exception:
                self._label.setText("Press a key...")
            return
        held_sorted = sorted(
            self._held_modifiers,
            key=lambda n: _MODIFIER_SORT_KEY.get(n, 999),
        )
        try:
            text = sequence_to_display("+".join(held_sorted)) + " + ..."
        except Exception:
            text = " + ".join(held_sorted) + " + ..."
        self._label.setText(text)

    def _refresh_display(self) -> None:
        """根据 current_seq 刷新显示。"""
        if self._mode == "capturing":
            # v2.5.2 third pass: capture 模式下根据 _held_modifiers 显示进度
            self._show_held_progress()
            return
        if not self.current_seq:
            try:
                text = I18n.t(_I18N_SETTINGS + "shortcut_cleared")
            except Exception:
                text = "<未设置>"
        else:
            try:
                text = sequence_to_display(self.current_seq)
            except Exception:
                text = self.current_seq
        self._label.setText(text)
        self._apply_display_style()
        # 恢复默认 tooltip
        try:
            self.setToolTip(I18n.t(_I18N_SETTINGS + "shortcut_capture_hint"))
        except Exception:
            self.setToolTip("Esc 取消 / Backspace 清空 / Enter 确认")

    def _apply_capture_style(self) -> None:
        try:
            theme = ThemeManager.current()
        except Exception:
            theme = {}
        bg_primary = theme.get("bg_primary", "#FFFFFF")
        is_dark = isinstance(bg_primary, str) and bg_primary.lower() < "#808080"
        style = _CAPTURE_STYLE_DARK if is_dark else _CAPTURE_STYLE_LIGHT
        try:
            self.setStyleSheet(style)
        except Exception:
            pass

    def _apply_display_style(self) -> None:
        try:
            self.setStyleSheet(_DISPLAY_STYLE)
        except Exception:
            pass

    def _show_invalid(self, error_key: str) -> None:
        """弹出无效输入提示 (不退出 capturing 模式)。"""
        try:
            title = I18n.t(_I18N_SETTINGS + "shortcut_conflict_title")
        except Exception:
            title = "快捷键"
        try:
            text = I18n.t(_I18N_SETTINGS + error_key)
        except Exception:
            text = error_key
        try:
            QMessageBox.warning(self, title, text)
        except Exception:
            # 无 GUI 环境时退化为 print
            try:
                print(f"[ShortcutCaptureEditor] {error_key}: {text}", file=sys.stderr)
            except Exception:
                pass


# ============================================================
# ShortcutCustomizeDialog
# ============================================================
class ShortcutCustomizeDialog(QWidget):
    """快捷键自定义面板。

    布局:
      +---------------------------------------------------+
      | 操作            | 快捷键                          |
      +-----------------+---------------------------------+
      | 播放/暂停       | [        Space        ]         |
      | 向上滚动        | [         Up          ]         |
      | ...             | ...                              |
      +---------------------------------------------------+
      |              [   重置所有   ]                      |
      +---------------------------------------------------+
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        # 记录当前正在捕获的 editor (用于视觉去重)
        self._active_editor: Optional[ShortcutCaptureEditor] = None
        # 缓存 action_id -> 行号
        self._row_by_action: Dict[str, int] = {}

        self._init_ui()
        self._load_from_manager()
        self._apply_theme()

    # --------------------------------------------------------
    # 初始化
    # --------------------------------------------------------
    def _init_ui(self) -> None:
        if not _QT_AVAILABLE:  # pragma: no cover
            return

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ---- 表格 ----
        self.table = QTableWidget(len(DEFAULT_SHORTCUTS), 2, self)
        self.table.setHorizontalHeaderLabels([
            I18n.t(_I18N_SETTINGS + "shortcut_action_col"),
            I18n.t(_I18N_SETTINGS + "shortcut_key_col"),
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)

        header = self.table.horizontalHeader()
        try:
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
        except Exception:
            pass

        # 填充行
        for row, action in enumerate(DEFAULT_SHORTCUTS):
            # ---- col 0: action name ----
            try:
                name_text = I18n.t(_I18N_NAME(action))
            except Exception:
                name_text = action.id
            name_item = QTableWidgetItem(name_text)
            try:
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            except Exception:
                pass
            self.table.setItem(row, 0, name_item)

            # ---- col 1: capture editor ----
            editor = ShortcutCaptureEditor(action_id=action.id, parent=self)
            # 信号
            editor.capture_started.connect(self._on_capture_started)
            editor.capture_finished.connect(self._on_capture_finished)
            editor.capture_cancelled.connect(self._on_capture_cancelled)
            self.table.setCellWidget(row, 1, editor)

            self._row_by_action[action.id] = row

        root.addWidget(self.table)

        # ---- 重置按钮 ----
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.reset_btn = QPushButton(
            I18n.t(_I18N_SETTINGS + "shortcut_reset_all"), self
        )
        self.reset_btn.setFixedWidth(140)
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch(1)
        root.addLayout(btn_row)

    def _load_from_manager(self) -> None:
        """根据 ShortcutManager 当前状态刷新每个 editor。"""
        if not _QT_AVAILABLE:
            return
        try:
            mgr = ShortcutManager.instance()
        except Exception:
            mgr = None
        for row, action in enumerate(DEFAULT_SHORTCUTS):
            editor = self.table.cellWidget(row, 1)
            if editor is None:
                continue
            try:
                seq = mgr.get_key(action.id) if mgr is not None else action.default_key
            except Exception:
                seq = action.default_key
            try:
                editor.set_sequence(seq or "")
            except Exception:
                pass

    # --------------------------------------------------------
    # 对外方法
    # --------------------------------------------------------
    def get_current_dict(self) -> Dict[str, str]:
        """返回当前面板状态,key=action_id,value=序列字符串。

        不会调用 ShortcutManager,只读编辑器自身的 current_seq,
        由调用方负责 ``set_custom_bulk`` 持久化。
        """
        result: Dict[str, str] = {}
        if not _QT_AVAILABLE:
            return result
        for action in DEFAULT_SHORTCUTS:
            row = self._row_by_action.get(action.id, -1)
            if row < 0:
                continue
            editor = self.table.cellWidget(row, 1)
            if editor is None:
                result[action.id] = action.default_key
            else:
                result[action.id] = editor.current_seq or ""
        return result

    def apply_state(self, custom: Dict[str, str]) -> None:
        """用给定的 custom_dict 直接刷新每个 editor。"""
        if not _QT_AVAILABLE:
            return
        for action in DEFAULT_SHORTCUTS:
            row = self._row_by_action.get(action.id, -1)
            if row < 0:
                continue
            editor = self.table.cellWidget(row, 1)
            if editor is None:
                continue
            try:
                editor.set_sequence(custom.get(action.id, action.default_key) or "")
            except Exception:
                pass

    def refresh(self) -> None:
        """重新从 ShortcutManager 加载并刷新表格显示。"""
        self._load_from_manager()

    # --------------------------------------------------------
    # 编辑器回调
    # --------------------------------------------------------
    def _on_capture_started(self, action_id: str) -> None:
        """某个 editor 进入捕获模式:高亮它,把其它设为非 active。"""
        editor = self._find_editor(action_id)
        if editor is None:
            return
        # 取消其它正在 capturing 的 editor
        if self._active_editor is not None and self._active_editor is not editor:
            try:
                self._active_editor.cancel_capture()
            except Exception:
                pass
        self._active_editor = editor
        # 加额外高亮
        try:
            theme = ThemeManager.current()
        except Exception:
            theme = {}
        accent = theme.get("primary", "#4A90E2")
        try:
            editor.setStyleSheet(
                f"background: {accent}; color: white; border: 2px solid {accent};"
            )
        except Exception:
            pass

    def _on_capture_finished(self, action_id: str, new_seq: str) -> None:
        """捕获结束: 校验冲突 -> 写入或回滚 -> 刷新。"""
        mgr = ShortcutManager.instance()

        if new_seq:
            # 检查冲突 (排除自身)
            try:
                conflict = mgr.find_conflict(new_seq, exclude_action_id=action_id)
            except Exception:
                conflict = None

            if conflict:
                # 弹出冲突对话框
                choice = self._show_conflict_dialog(conflict, new_seq)
                if choice == "cancel":
                    # 取消 -> 恢复原值
                    self._restore_editor_value(action_id)
                    self._active_editor = None
                    self._apply_theme()
                    return
                elif choice == "clear":
                    # 清空被占用的那个
                    try:
                        mgr.set_custom(conflict, "")
                    except Exception:
                        pass
                # choice == "replace" 或 "clear" -> 应用 new_seq
                try:
                    mgr.set_custom(action_id, new_seq)
                except Exception:
                    pass
            else:
                # 无冲突,直接应用
                try:
                    mgr.set_custom(action_id, new_seq)
                except Exception:
                    pass
        else:
            # new_seq 为空 -> 直接清空该操作
            try:
                mgr.set_custom(action_id, "")
            except Exception:
                pass

        # 刷新整张表 (可能其它行的显示也要变)
        self._active_editor = None
        self._apply_theme()
        self.refresh()

    def _on_capture_cancelled(self, action_id: str) -> None:
        """捕获被取消: 恢复原值,刷新高亮。"""
        self._restore_editor_value(action_id)
        if self._active_editor is not None and self._active_editor.action_id == action_id:
            self._active_editor = None
        self._apply_theme()

    def _on_reset_clicked(self) -> None:
        """重置所有快捷键为默认。"""
        mgr = ShortcutManager.instance()
        try:
            mgr.clear_all()
        except Exception:
            pass
        self._active_editor = None
        self._apply_theme()
        self.refresh()
        # 成功提示
        try:
            QMessageBox.information(
                self,
                I18n.t(_I18N_SETTINGS + "shortcut_conflict_title"),
                I18n.t(_I18N_SETTINGS + "shortcut_reset_success"),
            )
        except Exception:
            pass

    # --------------------------------------------------------
    # 主题
    # --------------------------------------------------------
    def _apply_theme(self) -> None:
        """根据当前主题刷新 QTableWidget / QPushButton 的 QSS。"""
        if not _QT_AVAILABLE:
            return
        try:
            theme = ThemeManager.current()
        except Exception:
            return
        bg_primary = theme.get("bg_primary", "#FFFFFF")
        bg_surface = theme.get("bg_surface", "#F5F5F5")
        text_primary = theme.get("text_primary", "#222222")
        border = theme.get("border", "#CCCCCC")
        primary = theme.get("primary", "#4A90E2")
        # 让 active editor 恢复默认样式
        if self._active_editor is not None:
            try:
                self._active_editor.setStyleSheet(
                    f"background: {primary}; color: white; border: 2px solid {primary};"
                )
            except Exception:
                pass
        qss = f"""
            QTableWidget {{
                background-color: {bg_surface};
                color: {text_primary};
                gridline-color: {border};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
            QHeaderView::section {{
                background-color: {bg_primary};
                color: {text_primary};
                border: 1px solid {border};
                padding: 6px;
                font-weight: bold;
            }}
            QPushButton {{
                background-color: {primary};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {theme.get('primary_hover', primary)};
            }}
            QPushButton:pressed {{
                background-color: {theme.get('primary_pressed', primary)};
            }}
        """
        try:
            self.setStyleSheet(qss)
        except Exception:
            pass

    # --------------------------------------------------------
    # 工具
    # --------------------------------------------------------
    def _find_editor(self, action_id: str) -> Optional[ShortcutCaptureEditor]:
        if not _QT_AVAILABLE:
            return None
        row = self._row_by_action.get(action_id, -1)
        if row < 0:
            return None
        return self.table.cellWidget(row, 1)

    def _restore_editor_value(self, action_id: str) -> None:
        """从 ShortcutManager 重新读取并刷新某个 editor。"""
        if not _QT_AVAILABLE:
            return
        editor = self._find_editor(action_id)
        if editor is None:
            return
        mgr = ShortcutManager.instance()
        action = mgr.get_action(action_id) if hasattr(mgr, "get_action") else None
        if action is None:
            # fallback: 从 DEFAULT_SHORTCUTS 找
            for a in DEFAULT_SHORTCUTS:
                if a.id == action_id:
                    action = a
                    break
        if action is None:
            return
        try:
            seq = mgr.get_key(action_id)
        except Exception:
            seq = action.default_key
        try:
            editor.set_sequence(seq or "")
        except Exception:
            pass

    def _show_conflict_dialog(self, conflict_action_id: str, new_seq: str) -> str:
        """弹出冲突对话框。

        Returns:
            ``"replace"`` / ``"clear"`` / ``"cancel"``
        """
        if not _QT_AVAILABLE:
            return "cancel"
        mgr = ShortcutManager.instance()
        # 拿到冲突操作的显示名
        try:
            action_name = I18n.t(_I18N_SHORTCUT_NAME_PREFIX + conflict_action_id)
        except Exception:
            action_name = conflict_action_id
        try:
            msg_text = I18n.t(
                _I18N_SETTINGS + "shortcut_conflict_msg", action=action_name
            )
        except Exception:
            msg_text = f"该快捷键已被「{action_name}」占用。\n是否替换为新快捷键？"
        try:
            title = I18n.t(_I18N_SETTINGS + "shortcut_conflict_title")
        except Exception:
            title = "快捷键冲突"

        # 自定义按钮: 替换 / 清空原快捷键 / 取消
        try:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle(title)
            box.setText(msg_text)
            replace_btn = box.addButton("替换", QMessageBox.AcceptRole)
            clear_btn = box.addButton("清空原快捷键", QMessageBox.DestructiveRole)
            cancel_btn = box.addButton("取消", QMessageBox.RejectRole)
            box.setDefaultButton(replace_btn)
            box.exec_()
            clicked = box.clickedButton()
        except Exception:
            return "cancel"

        if clicked is replace_btn:
            return "replace"
        if clicked is clear_btn:
            return "clear"
        return "cancel"


# ============================================================
# 模块级辅助
# ============================================================
def _I18N_NAME(action: "ShortcutAction") -> str:  # type: ignore[name-defined]
    """拼接 ``shortcuts.<id>`` 形式的 i18n 键。"""
    return _I18N_SHORTCUT_NAME_PREFIX + action.id


__all__ = [
    "ShortcutCaptureEditor",
    "ShortcutCustomizeDialog",
]
