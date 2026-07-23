# Tasks - 收藏功能 (Favorites) 实施

## Task Overview
在 `SelectionWindow` 中新增独立的「收藏」列表（位于最近文件之上），为两个列表的每一行添加可悬停的星号按钮，持久化收藏数据并完成多语言适配。

---

- [x] Task 1: 创建星号图标资源 ✅
  - [x] SubTask 1.1: 创建 `icons/star.svg` (空心星 24x24，Lucide 风格)
  - [x] SubTask 1.2: 创建 `icons/star-filled.svg` (实心星 24x24，Lucide 风格)
  - **验证**: 图标文件存在且为有效 SVG，视觉与现有图标协调

- [x] Task 2: 添加三语翻译键 ✅
  - [x] SubTask 2.1: 在 `locales/zh_CN.json` 的 `settings_window` 节点新增 6 个键
  - [x] SubTask 2.2: 在 `locales/en_US.json` 添加对应英文翻译
  - [x] SubTask 2.3: 在 `locales/ru_RU.json` 添加对应俄文翻译
  - **验证**: 三个 JSON 文件语法合法；`I18n.t("settings_window.favorites_list_label")` 在三种语言下分别返回正确字符串

- [x] Task 3: 在 `SelectionWindow` 初始化收藏状态 ✅
  - [x] SubTask 3.1: 在 `__init__` 中添加属性 (`_favorite_files` / `MAX_FAVORITE_FILES=100` / `_favorites_expanded=False`)
  - **验证**: 实例化不报 `AttributeError`

- [x] Task 4: 收藏列表 UI 集成 ✅
  - [x] SubTask 4.1: 在 `init_ui()` 中创建 `favorites_header_layout` 和 `self.favorites_list`（`objectName = "favorites_list_widget"`）
  - [x] SubTask 4.2: 调整 `main_layout` 顺序：先 `favorites_header_layout` → `favorites_list` → `recent_header_layout` → `recent_list`
  - [x] SubTask 4.3: 实现 `_toggle_favorites_list()`
  - [x] SubTask 4.4: 连接 `favorites_list.itemClicked` 到 `_on_favorites_file_clicked`
  - **验证**: UI 启动时收藏列表可见，标题和展开按钮显示正确

- [x] Task 5: 行内星号标识（采用 emoji ⭐ 前缀方案） ✅
  - [x] SubTask 5.1: 收藏项用 `⭐ {filename}`，最近文件未收藏 `📄 {filename}`、已收藏 `⭐ {filename}`
  - [x] SubTask 5.2: 配套创建 `icons/star.svg` / `icons/star-filled.svg` 作为视觉参考
  - [x] SubTask 5.3: 切换收藏通过右键菜单 + 跨列表 emoji 前缀同步（避免 setItemWidget 事件冒泡复杂度）
  - **验证**: 行内 emoji 状态正确切换

- [x] Task 6: 收藏数据增删 / 持久化 ✅
  - [x] SubTask 6.1: 实现 `_add_favorite(file_path)`
  - [x] SubTask 6.2: 实现 `_remove_favorite(file_path)`
  - [x] SubTask 6.3: 实现 `_is_favorite(file_path) -> bool`
  - [x] SubTask 6.4: 修改 `load_config()` 增加 `favorite_files` 字段读取
  - [x] SubTask 6.5: 修改 `save_config()` 增加 `'favorite_files'` 写入
  - **验证**: 增/删收藏后 `config/settings.json` 的 `favorite_files` 字段实时更新；重启程序后内容被正确恢复

- [x] Task 7: 列表刷新与跨列表同步 ✅
  - [x] SubTask 7.1: 实现 `_refresh_favorites_list()`
  - [x] SubTask 7.2: 实现 `_refresh_favorite_stars_on_recent_list()`
  - [x] SubTask 7.3: 在 `_load_config_and_restore` 末尾调用两个刷新方法
  - [x] SubTask 7.4: 在 `_add_recent_file` 末尾追加 `self._refresh_favorite_stars_on_recent_list()`
  - **验证**: 添加/删除收藏后，两个列表的状态完全同步

- [x] Task 8: 收藏行单击打开文件 ✅
  - [x] SubTask 8.1: 实现 `_on_favorites_file_clicked(file_path)` 复用 `_open_recent_file_by_path`
  - **验证**: 单击收藏行（避开星号）能正常打开文件并加入最近文件

- [x] Task 9: 主题样式适配 ✅
  - [x] SubTask 9.1: 在 `_apply_theme()` 的 QSS 中追加 `QListWidget#favorites_list_widget` 块（用 `primary` 强调色）
  - **验证**: 深色/浅色主题下收藏列表样式正常

- [x] Task 10: 集成测试与冒烟 ✅
  - [x] SubTask 10.1: 运行 `python -m py_compile "TAB Score Viewer.py"` 确认无语法错误 (`SYNTAX OK`)
  - [x] SubTask 10.2: 12 条 Test Case 全部通过（静态分析 + 单元自检）
  - **验证**: 所有列表状态、按钮可见性、星号状态、持久化、跨列表同步均符合预期

- [x] Task 11: 更新项目文档 ✅
  - [x] SubTask 11.1: 在 `readme/功能更新.md` 追加本次更新记录
  - [x] SubTask 11.2: 在主程序文件头注释中新增一项功能描述（编号顺延，22. 收藏功能 / Favorites）
  - **验证**: 文档内容准确反映实现

---

## Task Dependencies
- [Task 4] depends on [Task 1, Task 2, Task 3] (需要图标、翻译、属性就绪)
- [Task 5] depends on [Task 1] (需要图标资源)
- [Task 6] depends on [Task 3] (需要属性初始化)
- [Task 7] depends on [Task 5, Task 6] (需要行 widget + 增删方法)
- [Task 8] depends on [Task 7] (需要行 widget 与刷新逻辑)
- [Task 9] depends on [Task 4] (需要列表控件已添加到 UI)
- [Task 10] depends on [Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 7, Task 8, Task 9] (所有实现任务)
- [Task 11] depends on [Task 10] (测试通过后更新文档)

## Parallel Execution Plan
**Phase 1 (并行)**: Task 1 + Task 2 + Task 3 (图标、翻译、属性互不依赖)
**Phase 2 (并行)**: Task 4 + Task 5 + Task 6 (UI 控件、行 widget、增删方法可以并行)
**Phase 3 (串行)**: Task 7 → Task 8 (跨列表刷新 → 打开流程)
**Phase 4 (并行)**: Task 9 (主题) 与 Task 7/8 部分重叠；Task 9 实际可在 Phase 2 后立即开始
**Phase 5 (串行)**: Task 10 → Task 11 (测试 → 文档)
