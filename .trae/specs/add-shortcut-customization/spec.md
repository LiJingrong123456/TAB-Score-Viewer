# 快捷键自定义面板 (Shortcut Customization Panel) Spec

## Why
当前主窗口的快捷键（如 Ctrl+Z / F11 / Space 等）全部硬编码在 `DisplayWindow.keyPressEvent` 中，用户无法修改。对于高频使用、习惯特定快捷键的吉他手/键盘手，需要一个**可视化面板**来重新绑定快捷键，使操作更顺手。

## What Changes
- **新增** `shortcuts.py` 模块：定义 `ShortcutAction`（操作元数据）+ `ShortcutManager`（解析/校验/序列化）+ 默认快捷键表
- **新增** `shortcuts_dialog.py` 模块：`ShortcutCustomizeDialog` —— 表格形式列出所有可自定义的操作，支持点击"快捷键"列捕获组合键
- **修改** `settings_dialog.py`：在 `QTabWidget` 中**新增 "快捷键" Tab**，嵌入 `ShortcutCustomizeDialog`
- **修改** `TAB Score Viewer.py`：
  - `DisplayWindow.keyPressEvent` 改为**先查 `ShortcutManager`**，按用户自定义 → 默认 → 内置映射 顺序分发
  - 启动时从 `config/settings.json` 加载 `custom_shortcuts` 字段
  - 提供"恢复默认"动作（绑定到 Tab 内的"重置所有"按钮）
- **修改** `config.py`：新增字段 `_DEFAULT_CUSTOM_SHORTCUTS = {}`（空字典表示全部走默认）
- **新增三语翻译键**（位于 `settings_dialog` 节点）：
  - `tab_shortcuts` / `shortcut_action_col` / `shortcut_key_col` / `shortcut_reset_all` / `shortcut_capture_hint` / `shortcut_press_to_set` / `shortcut_conflict_title` / `shortcut_conflict_msg` / `shortcut_invalid_modifier_only` / `shortcut_max_keys` / `shortcut_reset_success` / `shortcut_cleared`

## Impact
- Affected specs: `add-settings-panel`（新增 Tab 集成）
- Affected code:
  - `shortcuts.py` - **新增**（操作元数据 + 解析/校验逻辑）
  - `shortcuts_dialog.py` - **新增**（可视化表格 + 键盘捕获）
  - `settings_dialog.py` - **修改**（加 Tab + 嵌入 Dialog）
  - `config.py` - **修改**（加 `_DEFAULT_CUSTOM_SHORTCUTS` 字段）
  - `TAB Score Viewer.py` - **修改**（`DisplayWindow.keyPressEvent` 分发改造 + 加载自定义）
  - `locales/{zh_CN,en_US,ru_RU}.json` - **修改**（各 +12 键）
- 不影响：收藏、节拍器、最近文件、播放、导出、主题、难度评分

## ADDED Requirements

### Requirement: 快捷键操作注册表
The system SHALL provide a `ShortcutAction` dataclass and a `DEFAULT_SHORTCUTS` registry containing all user-customizable actions.

#### Scenario: 操作元数据
- **WHEN** 应用启动
- **THEN** `shortcuts.DEFAULT_SHORTCUTS` 包含 12 个操作：
  | ID | 名称 (zh) | 默认快捷键 | 触发方法 |
  |----|-----------|------------|----------|
  | `play_pause` | 播放/暂停 | `Space` | `DisplayWindow.toggle_playback` |
  | `scroll_up` | 向上滚动 | `Up` | 内置滚动逻辑 |
  | `scroll_down` | 向下滚动 | `Down` | 内置滚动逻辑 |
  | `speed_down` | 减速 | `Left` | `speed_spin` 减 25 |
  | `speed_up` | 加速 | `Right` | `speed_spin` 加 25 |
  | `fullscreen` | 切换全屏 | `F11` | `toggle_fullscreen` |
  | `exit_or_close` | 退出全屏 / 关闭窗口 | `Escape` | 条件分支 |
  | `anno_undo` | 撤销标注 | `Ctrl+Z` | `_anno_undo` |
  | `anno_redo` | 重做标注 | `Ctrl+Y` | `_anno_redo` |
  | `anno_create` | 创建标注 | `Ctrl+K` | `_create_annotation_at_cursor` |
  | `metronome_toggle` | 切换节拍器 | `Ctrl+M` | 切换 metronome_enable_check |
  | `anno_dummy` | (占位) | (空) | 占位，防止用户误改全部 11 个后没有空槽 |

#### Scenario: 操作不可用时
- **WHEN** DisplayWindow 缺少 `metronome_enable_check` 等属性
- **THEN** 该快捷键**静默忽略**，不报错

### Requirement: ShortcutManager 解析与校验
The system SHALL provide a `ShortcutManager` singleton that parses user input, validates the sequence, and detects conflicts.

#### Scenario: 输入解析
- **WHEN** 用户按下 `Ctrl+Shift+F`
- **THEN** `ShortcutManager.parse_keypress(modifiers, key)` 返回 `(keys_tuple, is_valid)` 其中 `keys_tuple = ('Ctrl', 'Shift', 'F')`
- **AND** 按键顺序按 **modifier → 字母/数字/功能键** 排序

#### Scenario: 修饰键集合
The system SHALL treat the following keys as **modifiers** (cannot be used alone):
- `Ctrl` (Qt.ControlModifier)
- `Shift` (Qt.ShiftModifier)
- `Alt` / `Option` (Mac) (Qt.AltModifier)
- `Meta` / `Win` / `Super` / `Command` (Qt.MetaModifier)
- `Caps` / `CapsLock`
- `Tab`

#### Scenario: 校验规则
- **WHEN** 用户按下的按键**全部**是修饰键（如 `Ctrl+Shift`）
- **THEN** `is_valid = False`，错误信息 `shortcut_invalid_modifier_only`
- **AND** UI 显示提示：「快捷键必须至少包含 1 个非修饰键（字母/数字/F1-F12 等）」

#### Scenario: 校验规则 - 键数上限
- **WHEN** 用户按下超过 3 个键（如 `Ctrl+Shift+Alt+A` 共 4 个）
- **THEN** `is_valid = False`，错误信息 `shortcut_max_keys`
- **AND** UI 显示提示：「快捷键最多由 3 个键组成」

#### Scenario: 冲突检测
- **WHEN** 用户为 `play_pause` 设置新键 `Ctrl+Z`
- **AND** `anno_undo` 已绑定 `Ctrl+Z`
- **THEN** 弹出 `shortcut_conflict` 对话框
- **AND** 用户可选择「替换」/「取消」/「为两个操作都保留」（清空另一个）
- **AND** 替换 → 旧快捷键恢复默认，保存新键

#### Scenario: 清空快捷键
- **WHEN** 用户在编辑行点击「清空」按钮（或按 Backspace/Delete）
- **THEN** 该操作的快捷键被**永久禁用**（不响应任何键）
- **AND** 序列化为空字符串 `""`

### Requirement: 键盘捕获 UI
The system SHALL provide a `ShortcutCaptureEditor` widget that captures the next keypress and validates the sequence.

#### Scenario: 激活捕获
- **WHEN** 用户点击表格行右侧的快捷键单元格
- **THEN** 该单元格进入"捕获模式"（视觉提示：高亮 / 闪烁下划线）
- **AND** 显示占位文字 `shortcut_press_to_set`（如「请按下快捷键…」）
- **AND** `shortcut_capture_hint` tooltip 提示用户「Esc 取消 / Backspace 清空 / Enter 确认」

#### Scenario: 按下组合键
- **WHEN** 捕获模式下用户按 `Ctrl+Shift+F`
- **THEN** 单元格显示 `Ctrl+Shift+F`
- **AND** 写入内存中的 `custom_shortcuts` 字典
- **AND** 退出捕获模式

#### Scenario: Esc 取消
- **WHEN** 捕获模式下用户按 `Esc`
- **THEN** 单元格恢复**原值**（不保存）
- **AND** 退出捕获模式

#### Scenario: Backspace 清空
- **WHEN** 捕获模式下用户按 `Backspace` 或 `Delete`
- **THEN** 单元格显示空（"<未设置>"）
- **AND** 该操作的快捷键被禁用
- **AND** 退出捕获模式

#### Scenario: Enter 确认
- **WHEN** 捕获模式下用户按 `Enter`
- **THEN** 确认当前组合键（不立即触发动作，仅在 OK 时统一保存）
- **AND** 退出捕获模式

### Requirement: 持久化
The system SHALL save custom shortcuts to `config/settings.json` under the `custom_shortcuts` key.

#### Scenario: 保存格式
```json
{
  "custom_shortcuts": {
    "play_pause": "Space",
    "anno_undo": "Ctrl+Shift+Z",
    "metronome_toggle": ""
  }
}
```
- 键：操作 ID
- 值：字符串序列（用 `+` 分隔），空字符串表示禁用

#### Scenario: 加载与回退
- **WHEN** 应用启动
- **THEN** 从 `config/settings.json` 读取 `custom_shortcuts`
- **AND** DisplayWindow.keyPressEvent 优先级：
  1. 用户自定义 → 命中即调用对应回调
  2. 内置默认（保持现有硬编码逻辑）→ 兼容未自定义的操作

#### Scenario: 恢复默认
- **WHEN** 用户点击 Tab 内的「重置所有」按钮
- **THEN** `custom_shortcuts` 字典清空
- **AND** 表格所有行恢复为默认快捷键
- **AND** 显示 `shortcut_reset_success` 提示

### Requirement: 三语翻译
The system SHALL provide trilingual support (zh_CN / en_US / ru_RU) for new UI strings.

#### Scenario: 必填键（位于 `settings_dialog` 节点）
- `tab_shortcuts`: "快捷键" / "Shortcuts" / "Горячие клавиши"
- `shortcut_action_col`: "操作" / "Action" / "Действие"
- `shortcut_key_col`: "快捷键" / "Shortcut" / "Клавиша"
- `shortcut_reset_all`: "重置所有" / "Reset All" / "Сбросить все"
- `shortcut_capture_hint`: "Esc 取消 / Backspace 清空 / Enter 确认" / 等
- `shortcut_press_to_set`: "请按下快捷键…" / "Press a key..." / "Нажмите клавишу..."
- `shortcut_conflict_title`: "快捷键冲突" / "Shortcut Conflict" / "Конфликт"
- `shortcut_conflict_msg`: "该快捷键已被「{action}」占用。是否替换？" / "Shortcut already used by '{action}'. Replace?" / 等
- `shortcut_invalid_modifier_only`: "必须包含至少 1 个非修饰键" / 等
- `shortcut_max_keys`: "最多 3 个键" / "Max 3 keys" / "Макс. 3 клавиши"
- `shortcut_reset_success`: "已恢复默认快捷键" / "Shortcuts reset" / "Сброшено"
- `shortcut_cleared`: "<未设置>" / "<None>" / "<Не задано>"

## MODIFIED Requirements

### Requirement: DisplayWindow.keyPressEvent (修改现有)
原硬编码 `if event.modifiers() & Qt.ControlModifier: if event.key() == Qt.Key_Z: ...`
改为：先构造 `(modifiers_tuple, key_name)`，查 `ShortcutManager` 自定义表 → 默认表 → 触发回调。

伪代码：
```python
def keyPressEvent(self, event):
    seq = ShortcutManager.event_to_sequence(event)
    action_id = ShortcutManager.lookup(seq)  # 用户优先 → 默认
    if action_id:
        self._dispatch_shortcut(action_id, event)
    else:
        super().keyPressEvent(event)
```

### Requirement: SettingsDialog (新增 Tab)
在 `_setup_ui` 末尾追加：
```python
self.shortcuts_tab = ShortcutCustomizeDialog()
self.tabs.addTab(self.shortcuts_tab, I18n.t("settings_dialog.tab_shortcuts"))
```

### Requirement: config.py (新增字段)
- `_DEFAULT_CUSTOM_SHORTCUTS: Dict[str, str] = {}`
- `apply_config_settings` 中读取 `config.custom_shortcuts` 注入 `ShortcutManager`

## REMOVED Requirements
None (pure additive)

## Technical Implementation Details

### shortcuts.py 模块结构

```python
# shortcuts.py
"""
TAB Score Viewer - Shortcut Customization
快捷键管理模块
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Dict, Optional, Set, Tuple, Callable
from PyQt5.QtCore import Qt, QObject
from PyQt5.QtGui import QKeyEvent


# 修饰键集合（不能单独作为快捷键）
MODIFIER_KEYS = {'Ctrl', 'Shift', 'Alt', 'Option', 'Meta', 'Win', 'Super', 'Command', 'CapsLock', 'Tab'}

# Qt.Key 名称映射 (用于跨平台)
KEY_NAME_MAP = {
    Qt.Key_Space: 'Space', Qt.Key_Up: 'Up', Qt.Key_Down: 'Down',
    Qt.Key_Left: 'Left', Qt.Key_Right: 'Right',
    Qt.Key_F1: 'F1',  # ... 到 F12
    Qt.Key_Escape: 'Escape', Qt.Key_Tab: 'Tab',
    Qt.Key_Return: 'Return', Qt.Key_Enter: 'Enter',
    Qt.Key_Backspace: 'Backspace', Qt.Key_Delete: 'Delete',
    # 字母和数字直接用 event.text()
}

@dataclass
class ShortcutAction:
    id: str
    name_key: str            # I18n 键 (如 "shortcuts.play_pause")
    default_key: str         # 默认序列
    callback_attr: str       # DisplayWindow 上要调用的方法名

DEFAULT_SHORTCUTS = [
    ShortcutAction('play_pause', 'shortcuts.play_pause', 'Space', 'toggle_playback'),
    ShortcutAction('scroll_up', 'shortcuts.scroll_up', 'Up', '_scroll_up'),
    # ... 11 个
]


class ShortcutManager(QObject):
    _instance = None
    
    def __init__(self):
        self._custom: Dict[str, str] = {}  # action_id -> key_seq
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_custom(self, action_id: str, key_seq: str) -> None:
        """设置自定义快捷键 (空字符串表示禁用)"""
        self._custom[action_id] = key_seq
    
    def clear_all(self) -> None:
        """恢复所有默认"""
        self._custom.clear()
    
    def get_key(self, action_id: str) -> str:
        """获取最终键序列 (用户 > 默认 > '')"""
        if action_id in self._custom:
            return self._custom[action_id]
        for a in DEFAULT_SHORTCUTS:
            if a.id == action_id:
                return a.default_key
        return ''
    
    def event_to_sequence(self, event: QKeyEvent) -> str:
        """QKeyEvent -> 'Ctrl+Shift+Z' 字符串"""
        parts = []
        mods = event.modifiers()
        if mods & Qt.ControlModifier: parts.append('Ctrl')
        if mods & Qt.ShiftModifier: parts.append('Shift')
        if mods & Qt.AltModifier: parts.append('Alt')
        if mods & Qt.MetaModifier: parts.append('Meta')
        key = event.key()
        if key in KEY_NAME_MAP:
            parts.append(KEY_NAME_MAP[key])
        else:
            text = event.text().upper()
            if text:
                parts.append(text)
        return '+'.join(parts)
    
    def parse_sequence(self, seq: str) -> Tuple[Set[str], bool]:
        """解析序列，返回 (修饰键集合, 是否有效)"""
        keys = [k.strip() for k in seq.split('+') if k.strip()]
        if len(keys) > 3:
            return (set(), False)
        non_mods = [k for k in keys if k not in MODIFIER_KEYS]
        if not non_mods:
            return (set(), False)
        return (set(keys), True)
    
    def lookup(self, key_seq: str) -> Optional[str]:
        """查 action_id (用户优先 > 默认)"""
        # 1. 用户自定义
        for action_id, custom_seq in self._custom.items():
            if custom_seq == key_seq:
                return action_id
        # 2. 默认
        for a in DEFAULT_SHORTCUTS:
            if a.default_key == key_seq:
                return action_id  # 修复: 应返回 a.id
        return None
```

### shortcuts_dialog.py 模块结构

```python
# shortcuts_dialog.py
"""
快捷键自定义对话框 - 表格 + 键盘捕获
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from shortcuts import DEFAULT_SHORTCUTS, ShortcutManager, MODIFIER_KEYS


class ShortcutCaptureEditor(QLabel):
    """自定义 Label 组件，捕获键盘事件"""
    captured = pyqtSignal(str)  # 发出捕获的序列
    cancelled = pyqtSignal()
    cleared = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._capturing = False
        self.setAlignment(Qt.AlignCenter)
    
    def start_capture(self):
        self._capturing = True
        self.setText(I18n.t("settings_dialog.shortcut_press_to_set"))
        self.setStyleSheet("background: yellow; color: black;")
    
    def keyPressEvent(self, event):
        if not self._capturing:
            return super().keyPressEvent(event)
        if event.key() == Qt.Key_Escape:
            self.cancelled.emit(); self._capturing = False; return
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            self.cleared.emit(); self._capturing = False; return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.captured.emit(self.text())  # 确认当前文本
            self._capturing = False; return
        # 构造序列
        mgr = ShortcutManager.instance()
        seq = mgr.event_to_sequence(event)
        keys, valid = mgr.parse_sequence(seq)
        if not valid:
            # 显示无效提示
            if all(k in MODIFIER_KEYS for k in seq.split('+') if k):
                QMessageBox.warning(self, ..., I18n.t("settings_dialog.shortcut_invalid_modifier_only"))
            elif len(seq.split('+')) > 3:
                QMessageBox.warning(self, ..., I18n.t("settings_dialog.shortcut_max_keys"))
            return
        self.setText(seq)
        self.captured.emit(seq)
        self._capturing = False


class ShortcutCustomizeDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_from_manager()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(len(DEFAULT_SHORTCUTS), 2)
        self.table.setHorizontalHeaderLabels([
            I18n.t("settings_dialog.shortcut_action_col"),
            I18n.t("settings_dialog.shortcut_key_col")
        ])
        # ... 填充行
        layout.addWidget(self.table)
        
        reset_btn = QPushButton(I18n.t("settings_dialog.shortcut_reset_all"))
        reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(reset_btn)
```

### DisplayWindow 分发改造

```python
# TAB Score Viewer.py
from shortcuts import ShortcutManager, DEFAULT_SHORTCUTS

class DisplayWindow:
    def keyPressEvent(self, event):
        try:
            mgr = ShortcutManager.instance()
            seq = mgr.event_to_sequence(event)
            action_id = mgr.lookup(seq)
            if not action_id:
                super().keyPressEvent(event)
                return
            # 命中后查找回调
            for a in DEFAULT_SHORTCUTS:
                if a.id == action_id and hasattr(self, a.callback_attr):
                    getattr(self, a.callback_attr)()
                    return
            # 回退: 原有硬编码逻辑 (处理回调不存在或默认快捷键需走原逻辑的情况)
            self._legacy_keypress(action_id, event)
        except Exception:
            super().keyPressEvent(event)
```

## Test Cases

| Case | 场景 | 预期结果 |
|------|------|----------|
| 1 | 启动程序，打开设置 → 快捷键 Tab | 显示 11 行表格，键序列与默认一致 |
| 2 | 点击「播放/暂停」行的快捷键列 | 进入捕获模式，显示「请按下快捷键…」 |
| 3 | 捕获模式下按 `Ctrl+Shift+P` | 单元格显示 `Ctrl+Shift+P`，操作生效 |
| 4 | 捕获模式下按 `Ctrl+Shift` (仅修饰键) | 弹出提示「必须包含至少 1 个非修饰键」 |
| 5 | 捕获模式下按 `Ctrl+Shift+Alt+A` (4 键) | 弹出提示「最多 3 个键」 |
| 6 | 把「播放/暂停」设为 `Ctrl+Z` (与「撤销标注」冲突) | 弹出冲突对话框，选「替换」后旧操作恢复默认 |
| 7 | 捕获模式下按 `Backspace` | 单元格清空，按下时操作不响应 |
| 8 | 捕获模式下按 `Esc` | 单元格恢复原值 |
| 9 | 点「重置所有」 | 所有行恢复默认，提示「已恢复默认快捷键」 |
| 10 | 修改后 OK 关闭对话框 | 立即生效（Space 不再播放，但 Ctrl+Shift+P 播放） |
| 11 | 重启程序 | 快捷键保留（从 config.json 加载） |
| 12 | 切换语言 | 表格列名和提示文字切换 |
| 13 | 鼠标点击捕获单元格外 | 退出捕获模式（恢复原值） |
| 14 | 按 F1 | 帮助？— 不冲突任何默认操作则不响应 |
| 15 | 关闭并重新打开设置对话框 | 表格显示当前已保存的自定义值 |
