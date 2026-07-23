# Tasks - 快捷键自定义面板 (Shortcut Customization) 实施

## Task Overview
在设置窗口新增"快捷键"Tab，提供表格化的快捷键自定义界面，支持 1-3 键组合、修饰键校验、冲突检测、持久化到 config.json。

---

- [x] Task 1: 创建 `shortcuts.py` 模块
  - [x] SubTask 1.1: 定义 `MODIFIER_KEYS` 集合（Ctrl/Shift/Alt/Meta/Caps/Tab 等 10 个）
  - [x] SubTask 1.2: 定义 `KEY_NAME_MAP`（Qt.Key → 字符串）
  - [x] SubTask 1.3: 定义 `ShortcutAction` dataclass（id/name_key/default_key/callback_attr）
  - [x] SubTask 1.4: 定义 `DEFAULT_SHORTCUTS` 列表（11 个操作）
  - [x] SubTask 1.5: 实现 `ShortcutManager` 单例（set_custom / clear_all / get_key / event_to_sequence / parse_sequence / lookup）
  - **验证**: ✅ 导入模块不报错，11 个默认操作可枚举

- [x] Task 2: 创建 `shortcuts_dialog.py` 模块
  - [x] SubTask 2.1: 实现 `ShortcutCaptureEditor(QWidget)` - 键盘捕获组件（captured / cancelled / cleared 信号）
  - [x] SubTask 2.2: 实现 `ShortcutCustomizeDialog(QWidget)` - 表格 + 重置按钮
  - [x] SubTask 2.3: 表格初始化：11 行 2 列（操作名 / 快捷键）
  - [x] SubTask 2.4: 冲突检测与对话框
  - [x] SubTask 2.5: 校验提示（仅修饰键 / 超过 3 键）
  - **验证**: ✅ Dialog 加载/显示无报错，表格列数 = 2，行数 = 11

- [x] Task 3: 添加三语翻译键
  - [x] SubTask 3.1: 在 `locales/zh_CN.json` 的 `settings_dialog` 节点新增 12 个键
  - [x] SubTask 3.2: 在 `locales/en_US.json` 添加对应英文翻译
  - [x] SubTask 3.3: 在 `locales/ru_RU.json` 添加对应俄文翻译
  - [x] SubTask 3.4: 在 `locales/zh_CN.json` 的 `shortcuts` 节点新增 11 个操作名
  - **验证**: ✅ 三个 JSON 文件 `json.load()` 合法

- [x] Task 4: 修改 `settings_dialog.py` 集成 Tab
  - [x] SubTask 4.1: 在 `_setup_ui` 末尾添加 `shortcuts_tab` 并 `addTab`
  - [x] SubTask 4.2: 处理 OK 按钮 → 将 `shortcut_custom` 字段写入 `config.settings`
  - **验证**: ✅ py_compile 通过

- [x] Task 5: 修改 `config.py` 加默认字段
  - [x] SubTask 5.1: 定义 `_DEFAULT_CUSTOM_SHORTCUTS: Dict[str, str] = {}`
  - [x] SubTask 5.2: 在 `apply_config_settings` 中读取并应用
  - **验证**: ✅ py_compile 通过

- [x] Task 6: 修改 `TAB Score Viewer.py` 集成 ShortcutManager
  - [x] SubTask 6.1: import `ShortcutManager` + `DEFAULT_SHORTCUTS`
  - [x] SubTask 6.2: 在 `DisplayWindow.__init__` 末尾加载自定义快捷键
  - [x] SubTask 6.3: 重构 `keyPressEvent`：先查 `ShortcutManager.lookup` → 触发回调 → 回退到原硬编码逻辑
  - [x] SubTask 6.4: 添加 `_dispatch_shortcut(action_id)` 私有方法
  - [x] SubTask 6.5: 添加 `set_shortcut(action_id, seq)` / `reset_shortcuts()` 公共方法（供 settings_dialog 调用）
  - **验证**: ✅ py_compile 通过；11 个默认快捷键全部命中

- [x] Task 7: 集成测试
  - [x] SubTask 7.1: `python -m py_compile` 全部通过
  - [x] SubTask 7.2: 三语 JSON `json.load()` 合法
  - [x] SubTask 7.3: 15 条 Test Case 静态分析全部通过
  - **验证**: ✅ shortcuts.py 单元测试（5 条核心场景）通过

- [ ] Task 8: 更新项目文档
  - [ ] SubTask 8.1: 在 `readme/功能更新.md` 追加 v2.5.0 记录
  - [ ] SubTask 8.2: 在主程序文件头注释中新增第 25 项「快捷键自定义」
  - **验证**: 文档内容准确反映实现

---

## Task Dependencies
- [Task 2] depends on [Task 1] (Dialog 依赖 Manager)
- [Task 4] depends on [Task 2, Task 3] (Tab 嵌入 + 翻译)
- [Task 6] depends on [Task 1, Task 5] (主程序集成 Manager + config)
- [Task 7] depends on [Task 1-6]
- [Task 8] depends on [Task 7]

## Parallel Execution Plan
**Phase 1 (并行)**: Task 1 + Task 3 (模块定义 + 翻译键互不依赖)
**Phase 2 (并行)**: Task 2 + Task 5 (Dialog 实现 + config 字段互不依赖)
**Phase 3 (并行)**: Task 4 + Task 6 (设置 Tab + 主程序分发)
**Phase 4 (串行)**: Task 7 → Task 8
