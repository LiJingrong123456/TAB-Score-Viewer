# Checklist - 快捷键自定义面板 (Shortcut Customization) 实施

## 资源与配置

- [x] **`shortcuts.py` 已创建**
  - [x] `MODIFIER_KEYS` 集合包含 10 个修饰键 (Ctrl/Shift/Alt/Meta/Caps/Tab 等)
  - [x] `KEY_NAME_MAP` 包含所有特殊键 (Space/Up/Down/F1-F12/Escape/Tab/Backspace/Delete/Enter/Return)
  - [x] `ShortcutAction` dataclass 4 字段
  - [x] `DEFAULT_SHORTCUTS` 11 个操作
  - [x] `ShortcutManager` 单例 (event_to_sequence / parse_sequence / lookup / set_custom / clear_all / get_key)

- [x] **`shortcuts_dialog.py` 已创建**
  - [x] `ShortcutCaptureEditor(QWidget)` 支持 capture_started/capture_finished/capture_cancelled 信号
  - [x] `ShortcutCustomizeDialog(QWidget)` 表格 11 行 × 2 列
  - [x] 冲突检测对话框
  - [x] 校验提示（仅修饰键 / 超 3 键）

- [x] **三语翻译键已添加**
  - [x] zh_CN.json: settings_dialog 节点 +12 键, shortcuts 节点 +11 键
  - [x] en_US.json: 同上
  - [x] ru_RU.json: 同上
  - [x] JSON 语法合法

## 核心逻辑

- [x] **修饰键集合**
  - [x] Ctrl / Shift / Alt / Option (Mac 同 Alt) / Meta / Win / Super / Command / CapsLock / Tab
  - [x] 任一不与字母/数字/F1-F12 混用 → 判定为仅修饰键

- [x] **键数上限**
  - [x] 最多 3 键 (Ctrl + Shift + A = 3 键合法)
  - [x] 超过 → 弹出 `shortcut_max_keys` 提示

- [x] **冲突检测**
  - [x] 用户为操作 A 设置已绑定到 B 的键
  - [x] 弹出 `shortcut_conflict` 对话框 (替换 / 取消 / 双向清空)
  - [x] 默认操作间不互相冲突（DEFAULT_SHORTCUTS 已验证）

- [x] **解析与回退**
  - [x] DisplayWindow.keyPressEvent 优先级: 用户自定义 > 内置默认 > 原硬编码
  - [x] 自定义序列为空 → 视为禁用
  - [x] 用户自定义后,原默认键不再响应（lookup 已排除"已被自定义"的操作）

## 键盘捕获 UI

- [x] **激活捕获**
  - [x] 点击右侧单元格进入捕获模式 (高亮)
  - [x] 占位文字 `shortcut_press_to_set`
  - [x] Esc 取消 (恢复原值)
  - [x] Backspace/Delete 清空 (操作禁用)
  - [x] Enter 确认 (保存当前文本)
  - [x] 鼠标点击外部 → 退出捕获

- [x] **输入反馈**
  - [x] 仅修饰键 → 弹 `shortcut_invalid_modifier_only` 提示
  - [x] 超过 3 键 → 弹 `shortcut_max_keys` 提示
  - [x] 有效组合 → 单元格显示序列并发出 captured 信号

## 持久化

- [x] **保存格式**
  - [x] config.json: `custom_shortcuts: {action_id: "Seq+Seq+..."}`
  - [x] 空字符串 = 禁用
  - [x] 缺失键 = 使用默认

- [x] **加载时机**
  - [x] 应用启动 → apply_config_settings 注入 ShortcutManager
  - [x] DisplayWindow 启动完成后立即生效

- [x] **重置**
  - [x] 「重置所有」按钮 → `clear_all()` + 刷新表格
  - [x] 提示 `shortcut_reset_success`

## UI 集成

- [x] **SettingsDialog Tab**
  - [x] 在 `QTabWidget` 末尾添加「快捷键」Tab
  - [x] 嵌入 `ShortcutCustomizeDialog`
  - [x] OK 时通过 `set_custom_shortcuts()` 同步到 ShortcutManager

- [x] **DisplayWindow 分发**
  - [x] import ShortcutManager + DEFAULT_SHORTCUTS
  - [x] keyPressEvent 重构: lookup → 触发回调
  - [x] 原硬编码逻辑保留作为回退 (`_legacy_keypress`)
  - [x] 修饰键组合通过 manager 后不再走原硬编码

## 验收

- [x] 15 条 Test Case 全部通过（详见 spec.md）
- [x] `python -m py_compile "TAB Score Viewer.py"` 无语法错误
- [x] `python -m py_compile shortcuts.py` 无语法错误
- [x] `python -m py_compile shortcuts_dialog.py` 无语法错误
- [x] `python -m py_compile settings_dialog.py` 无语法错误
- [x] `python -m py_compile config.py` 无语法错误
- [x] 三语 JSON 全部 `json.load()` 通过
- [x] 主程序文件头注释新增"快捷键自定义"条目
- [x] `readme/功能更新.md` 已追加 v2.5.0 记录
