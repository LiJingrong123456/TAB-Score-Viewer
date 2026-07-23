# 收藏功能 (Favorites) Spec

## Why
现有「最近文件」只按时间排序保存用户最近打开的文件，无法表达「我喜欢/经常练的」这类长期意图。用户需要一个独立的收藏列表，可手动添加/移除常用谱面，并配合最近文件形成两级快速访问面板。

## What Changes
- 在 `SelectionWindow` 的「最近文件」列表**上方**新增一个独立的「收藏」列表（独立 `QListWidget`）。
- 「收藏」列表**默认折叠**，只显示最新收藏的 **3 项**；展开后视口高度显示 **6 项**，可滚动查看更多。
- 在「收藏」和「最近文件」**两个列表的每一项最右侧**增加一个 ⭐ 按钮：
  - **未收藏：空心星** ☆
  - **已收藏：实心星** ★
  - 鼠标**悬停在行上**时显示，离开时隐藏（避免长期占用空间）
  - 点击后立即切换收藏状态，再点一次取消收藏
  - 点击星号**不触发**该行的"打开文件"行为（事件需被消费）
- 收藏数据持久化到 `config/settings.json` 的 `favorite_files` 字段（绝对路径字符串数组）。
- 启动时与「最近文件」一样，**过滤已不存在的文件**。
- 新增中/英/俄三语翻译键。
- 新增 `icons/star.svg` / `icons/star-filled.svg` 两个图标资源。
- 主题样式复用 `recent_list_widget` 的强调色，保持视觉一致。

## Impact
- Affected specs: 无（新功能）
- Affected code:
  - `TAB Score Viewer.py` - `SelectionWindow` 类（主要改动：`__init__` / `init_ui` / `_apply_theme` / `load_config` / `save_config` / 新增收藏相关方法 / `_add_recent_file` 处同步刷新收藏星号）
  - `locales/zh_CN.json` - `settings_window` 节点新增键
  - `locales/en_US.json` - `settings_window` 节点新增键
  - `locales/ru_RU.json` - `settings_window` 节点新增键
  - `icons/star.svg` - 新增（空心星 24x24）
  - `icons/star-filled.svg` - 新增（实心星 24x24）
  - `readme/功能更新.md` - 更新日志

## ADDED Requirements

### Requirement: 收藏列表控件 (Favorites List Widget)
The system SHALL provide a Favorites list widget placed above the Recent Files list in the SelectionWindow.

#### Scenario: 列表位置与结构
- **WHEN** `SelectionWindow` 初始化
- **THEN** 在 `recent_header_layout` / `recent_list` 之上插入一组独立的 `favorites_header_layout` + `favorites_list`（结构与最近文件对称）
- **AND** 收藏列表的 `objectName` 为 `favorites_list_widget`，便于 QSS 选择
- **AND** 收藏列表与最近文件列表的间距保持 8px

#### Scenario: 列表标题与展开/折叠按钮
- **WHEN** 收藏列表显示
- **THEN** 标题行显示 `I18n.t("settings_window.favorites_list_label")`
- **AND** 右侧显示 `expand_btn` 按钮（`I18n.t("settings_window.favorites_expand")` / `favorites_collapse` 切换文案）
- **AND** 点击 `expand_btn` 触发 `_toggle_favorites_list()` 切换 `_favorites_expanded: bool` 状态

#### Scenario: 列表默认折叠态（3 项）
- **WHEN** `_favorites_expanded == False`
- **THEN** 收藏列表视口固定高度为 **3 行**（按当前 `QListWidget` 单行高度推算，使用 `setFixedHeight(item_height * 3 + 2)`）
- **AND** 超过 3 项的内容可通过 `QScrollBar` 滚动查看

#### Scenario: 列表展开态（6 项）
- **WHEN** `_favorites_expanded == True`
- **THEN** 收藏列表视口固定高度为 **6 行**（`setFixedHeight(item_height * 6 + 2)`）
- **AND** 超过 6 项的内容可通过 `QScrollBar` 滚动查看

#### Scenario: 空状态提示
- **WHEN** 收藏列表为空
- **THEN** 显示一行 `I18n.t("settings_window.favorites_empty")` 灰色禁用项（与最近文件空态一致）

### Requirement: 星号按钮 (Star Button)
The system SHALL provide a star button on the right side of every file item in both the Favorites and Recent Files lists.

#### Scenario: 按钮可见性
- **WHEN** 鼠标悬停在任一列表的某一行上
- **THEN** 该行最右侧的星号按钮**显示**
- **WHEN** 鼠标离开该行
- **THEN** 星号按钮**隐藏**（不影响列表项其他区域布局）

#### Scenario: 按钮视觉状态
- **WHEN** 该文件**未在收藏列表**中
- **THEN** 星号按钮显示为 `☆`（使用 `icons/star.svg`）
- **WHEN** 该文件**已在收藏列表**中
- **THEN** 星号按钮显示为 `★`（使用 `icons/star-filled.svg`，使用主题强调色）

#### Scenario: 点击切换收藏
- **WHEN** 用户点击空心星 ☆
- **THEN** 该文件被添加到收藏列表头部，`save_config()` 立即持久化，两个列表的 UI 同步刷新
- **WHEN** 用户点击实心星 ★
- **THEN** 该文件从收藏列表移除，`save_config()` 立即持久化，两个列表的 UI 同步刷新
- **AND** 点击星号的事件**不会冒泡**到列表项的 `itemClicked`（不触发打开文件）

#### Scenario: Tooltip
- **WHEN** 鼠标悬停在星号按钮上
- **THEN** Tooltip 显示：
  - 空心：`I18n.t("settings_window.favorite_add")` ("添加到收藏" / "Add to Favorites" / "Добавить в избранное")
  - 实心：`I18n.t("settings_window.favorite_remove")` ("取消收藏" / "Remove from Favorites" / "Удалить из избранного")

### Requirement: 收藏数据持久化 (Persistence)
The system SHALL persist favorites to `config/settings.json`.

#### Scenario: 启动加载
- **WHEN** `load_config()` 读取 `favorite_files` 字段
- **THEN** 过滤掉 `os.path.isfile(p) == False` 的失效路径
- **AND** 仅保留 `SUPPORTED_ALL_EXTENSIONS` 后缀的文件

#### Scenario: 写回磁盘
- **WHEN** 用户增删收藏或启动加载
- **THEN** `save_config()` 写入 `favorite_files: List[str]` 字段（绝对路径，最多 `MAX_FAVORITE_FILES=100` 条）
- **AND** 已有 `recent_files` / `language` / `theme` 等字段保持不变

#### Scenario: 文件被移动/删除
- **WHEN** 下次启动时收藏路径在磁盘上不存在
- **THEN** 该路径被静默过滤掉，不影响其他记录

### Requirement: 收藏与最近文件联动 (Cross-List Sync)
The system SHALL keep the star button state in sync between Favorites and Recent Files lists.

#### Scenario: 在最近文件列表点星加入收藏
- **WHEN** 用户在 `recent_list` 点击某项的 ☆
- **THEN** 该路径加入 `self._favorite_files`
- **AND** `favorites_list` 立即出现该条目
- **AND** 两列表中同一文件的星号都变为 ★

#### Scenario: 在收藏列表点星取消收藏
- **WHEN** 用户在 `favorites_list` 点击某项的 ★
- **THEN** 该路径从 `self._favorite_files` 移除
- **AND** `recent_list` 中同路径的星号变为 ☆

### Requirement: 与现有打开流程协同 (Open Flow Integration)
The system SHALL reuse the existing show_display() logic to open files from the favorites list.

#### Scenario: 单击收藏行打开文件
- **WHEN** 用户单击 `favorites_list` 中某项（不在星号区域）
- **THEN** 复用 `_on_recent_file_clicked` 的相同调度逻辑，按扩展名分派到 `show_display(fpath, ftype)`
- **AND** 打开后自动 `_add_recent_file(fpath)`（保留原有最近文件语义）

### Requirement: 国际化 (Internationalization)
The system SHALL provide trilingual support (zh_CN / en_US / ru_RU) for all new UI text.

#### Scenario: 三语键完整
- **WHEN** 增加新键
- **THEN** 三个 `locales/*.json` 文件同时添加，JSON 语法合法
- **REQUIRED KEYS**（位于 `settings_window` 节点下）：
  - `favorites_list_label` / `favorites_expand` / `favorites_collapse`
  - `favorites_empty` / `favorite_add` / `favorite_remove`

## MODIFIED Requirements

### Requirement: SelectionWindow.__init__()
新增收藏相关属性：
```python
self._favorite_files: List[str] = []          # 收藏文件绝对路径（最多 100）
self.MAX_FAVORITE_FILES: int = 100
self._favorites_expanded: bool = False         # 默认折叠
```

### Requirement: SelectionWindow.init_ui()
在 `recent_header_layout` / `recent_list` 上方插入对称的收藏列表组；`main_layout` 顺序：
```python
main_layout.addLayout(favorites_header_layout)   # 收藏标题
main_layout.addWidget(self.favorites_list)       # 收藏列表
main_layout.addLayout(recent_header_layout)      # 最近文件标题
main_layout.addWidget(self.recent_list)          # 最近文件列表
main_layout.addSpacing(8)
...
```

### Requirement: SelectionWindow._apply_theme()
新增 `QListWidget#favorites_list_widget` 的 QSS 块（与 `recent_list_widget` 视觉一致，仅区分颜色为 `primary` 而非 `accent`，避免两个高亮色块紧邻造成视觉冲突）。

### Requirement: SelectionWindow._add_recent_file()
在末尾追加一行 `self._refresh_favorite_stars_on_recent_list()`，保证新加入的最近文件项的星号状态正确显示。

### Requirement: SelectionWindow.load_config() / save_config()
- `load_config`：增加 `raw_fav = cfg.get('favorite_files', [])` 过滤逻辑
- `save_config`：增加 `'favorite_files': self._favorite_files` 字段

## REMOVED Requirements
None (pure additive feature)

## Technical Implementation Details

### 核心方法（新增）
1. `_toggle_favorites_list()` - 切换收藏列表折叠/展开，更新按钮文字与高度
2. `_refresh_favorites_list()` - 清空 `favorites_list` 并按 `_favorite_files` 重新填充
3. `_add_favorite(file_path: str)` - 添加收藏（去重 + 头插 + 截断到 `MAX_FAVORITE_FILES` + 持久化 + 刷新两个列表）
4. `_remove_favorite(file_path: str)` - 移除收藏（持久化 + 刷新两个列表）
5. `_is_favorite(file_path: str) -> bool` - 判断给定路径是否已收藏
6. `_on_favorite_star_clicked(file_path: str)` - 星号点击槽：调用 `_add_favorite` 或 `_remove_favorite`
7. `_make_file_item(name, path, is_dir=False) -> tuple[QListWidgetItem, QWidget]` - 工厂函数：返回带星号按钮的 `QListWidgetItem`（使用 `setItemWidget` 嵌入自定义 widget）
8. `_refresh_favorite_stars_on_recent_list()` - 重刷最近文件列表每行的星号状态

### 状态管理
- `_favorite_files: List[str]` - 收藏列表（绝对路径，**最新在前**）
- `MAX_FAVORITE_FILES: int = 100`
- `_favorites_expanded: bool` - 折叠/展开状态

### 关键实现点：自定义 Item Widget
为让"行内嵌星号按钮"且能"悬停显示"，使用 `QListWidget.setItemWidget(row, custom_widget)`：
- `custom_widget = QWidget`，水平布局：`[stretch: 文本] [star_btn]`
- `star_btn.setFixedSize(20, 20)`，`setFlat(True)`，`setStyleSheet("background: transparent; border: none;")`
- 给 `custom_widget` 安装 `enterEvent` / `leaveEvent`：触发时 `star_btn.setVisible(True/False)`
- `custom_widget` 整体可点击（`_on_favorites_file_clicked` 调 `_open_recent_file_by_path`），但 `star_btn` 自身拦截 `mousePressEvent` 并 `event.accept()` 防止冒泡

### 高度计算
- `QListWidget` 单行高度 = `QListWidget.sizeHintForRow(0)` 或 22px 兜底
- 折叠 3 行：`setFixedHeight(3 * row_h + 2)`（含边框）
- 展开 6 行：`setFixedHeight(6 * row_h + 2)`
- 切换时调用 `setFixedHeight` + `setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)`

### 图标资源
- `icons/star.svg` - 空心星 24x24（Lucide 风格）
- `icons/star-filled.svg` - 实心星 24x24（与上一致填充版）
- 颜色通过 Qt 主题色或 SVG `currentColor` 在 QSS 中控制

## Test Cases (12 Cases)

| Case | 场景 | 预期结果 |
|------|------|----------|
| 1 | 收藏列表为空时打开窗口 | 收藏列表显示"(暂无收藏)"灰色提示；最近文件保持原有行为 |
| 2 | 通过最近文件某行的 ☆ 加入收藏 | 收藏列表立即出现该条目；该行与其他列表同路径行的星号变 ★ |
| 3 | 在收藏列表点击 ★ 取消收藏 | 收藏列表移除该条；最近文件同路径行星号变 ☆ |
| 4 | 收藏列表默认折叠 | 视口高度 = 3 行；超过 3 项可滚动；按钮显示"展开 ▼" |
| 5 | 点击展开按钮 | 视口高度 = 6 行；按钮显示"折叠 ▲" |
| 6 | 鼠标悬停在最近文件行 | 该行最右侧 ☆ 显示；离开后隐藏 |
| 7 | 鼠标悬停在收藏行 | 该行最右侧 ★ 显示；离开后隐藏 |
| 8 | 点击星号 | 切换收藏状态，但**不**打开该文件 |
| 9 | 单击收藏行（不在星号区域） | 正常打开文件并加入最近文件 |
| 10 | 关闭并重启程序 | `config/settings.json` 中 `favorite_files` 字段被正确读取，过滤掉磁盘不存在项 |
| 11 | 收藏 100+ 项后再添加 | 自动截断到 100 条；最早一项被淘汰 |
| 12 | 切换语言（中/英/俄） | 收藏相关 6 个键全部正确翻译；JSON 无语法错误 |
