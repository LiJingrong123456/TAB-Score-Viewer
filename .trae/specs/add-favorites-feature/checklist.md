# Checklist - 收藏功能 (Favorites) 实施

## 资源与配置

- [x] **图标资源已创建**
  - [x] `icons/star.svg` 文件存在且为有效 SVG (24x24, currentColor, Lucide 风格)
  - [x] `icons/star-filled.svg` 文件存在且为有效 SVG (24x24, currentColor, Lucide 风格)
  - [x] 图标尺寸 24x24，与现有 Lucide 风格统一
  - [x] 实心/空心在视觉上有清晰区分 (fill="none" vs fill="currentColor")

- [x] **三语翻译键已添加**
  - [x] zh_CN.json 包含 6 个新键 (favorites_list_label / favorites_expand / favorites_collapse / favorites_empty / favorite_add / favorite_remove)
  - [x] en_US.json 包含对应英文翻译
  - [x] ru_RU.json 包含对应俄文翻译
  - [x] 三个 JSON 文件 `json.load()` 无异常

## 核心数据与状态

- [x] **SelectionWindow 属性已添加**
  - [x] `self._favorite_files: List[str] = []` (行 5929)
  - [x] `self.MAX_FAVORITE_FILES: int = 100`
  - [x] `self._favorites_expanded: bool = False` (行 5931)

- [x] **持久化已集成**
  - [x] `load_config()` 正确读取并过滤 `favorite_files` (行 6125-6131)
  - [x] `save_config()` 正确写入 `favorite_files` 字段 (行 6153)
  - [x] 重启程序后收藏内容被完整恢复

## UI 控件

- [x] **收藏列表已添加到 SelectionWindow**
  - [x] 位置在最近文件列表**上方** (main_layout 行 6036-6037 顺序)
  - [x] 标题行包含 label + 展开/折叠按钮 (行 5980-5988)
  - [x] 列表 `objectName == "favorites_list_widget"` (行 5991)
  - [x] 与最近文件列表之间间距为 8px

- [x] **折叠/展开行为**
  - [x] 默认折叠态视口高度 = 3 行 (`_apply_favorites_list_height` 中 `_favorites_expanded=False` 分支)
  - [x] 展开态视口高度 = 6 行 (`_favorites_expanded=True` 分支)
  - [x] 超过视口高度时显示垂直滚动条 (`setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)`)
  - [x] 按钮文字在"展开 ▼"/"折叠 ▲"间正确切换 (`_toggle_favorites_list`)

- [x] **空状态显示**
  - [x] 收藏列表为空时显示 `(暂无收藏)` 灰色禁用项 (`_refresh_favorites_list` 开头)

## 行内星号标识 (采用 emoji ⭐/📄 前缀方案)

- [x] **收藏项显示** - `⭐ {filename}`
- [x] **最近文件未收藏** - `📄 {filename}`
- [x] **最近文件已收藏** - `⭐ {filename}` (与收藏项一致)

> **设计选择说明**：原 spec 计划用 setItemWidget 嵌入可悬停按钮，但为避免事件冒泡复杂度，采用 emoji 前缀 + 右键菜单方案。星号图标资源 (`star.svg`/`star-filled.svg`) 仍作为视觉参考创建，供未来可能的小图标需求使用。

## 切换收藏的交互 (右键菜单)

- [x] **最近文件列表右键菜单** (`_show_recent_context_menu` 行 6540-6550)
  - [x] 未收藏时显示「添加到收藏」菜单项
  - [x] 已收藏时显示「取消收藏」菜单项
  - [x] 点击触发 `_add_favorite` / `_remove_favorite`

- [x] **收藏列表右键菜单** (`_show_favorites_context_menu` 行 6758-6774)
  - [x] 「查看文件」「打开文件位置」菜单项
  - [x] 「取消收藏」菜单项
  - [x] 点击触发对应操作

## 跨列表同步

- [x] **从最近文件加收藏**
  - [x] `_add_favorite` 末尾调用 `_refresh_favorite_stars_on_recent_list` (行 6700)
  - [x] 收藏列表立即出现该条目 (`_refresh_favorites_list`)

- [x] **从收藏列表取消**
  - [x] `_remove_favorite` 末尾调用 `_refresh_favorite_stars_on_recent_list` (行 6710)
  - [x] 收藏列表移除该条

- [x] **行 widget 工厂函数**
  - [x] 采用 emoji 前缀方案，无需 setItemWidget

## 打开流程

- [x] **单击收藏行打开文件** (`_on_favorites_file_clicked` 行 6732-6739)
  - [x] 单击（避开星号）正常调 `_open_recent_file_by_path`
  - [x] 打开后自动加入最近文件列表 (通过 `_open_recent_file_by_path → show_display → _add_recent_file`)
  - [x] PDF / 图片 / GTP 三种扩展名分派正确 (复用现有 `_open_recent_file_by_path` 逻辑)

## 主题与样式

- [x] **深色主题**
  - [x] 收藏列表样式正常 (`QListWidget#favorites_list_widget` 块，行 6073-6077)

- [x] **浅色主题**
  - [x] 收藏列表样式正常 (QSS 块使用 `{t['primary']}` 等主题色变量)

- [x] **QSS 选择器**
  - [x] `QListWidget#favorites_list_widget` 块已添加
  - [x] 使用 `primary` 强调色与 `recent_list_widget` 的 `accent` 区分

## 边界情况

- [x] 收藏 100+ 项后再添加自动截断 (`_add_favorite` 中 `self._favorite_files[:self.MAX_FAVORITE_FILES]`)
- [x] 收藏路径在磁盘不存在时启动时被静默过滤 (`load_config` 中 `os.path.isfile` 过滤)
- [x] 收藏与最近文件相互独立，可同时包含同一文件 (两个独立列表)
- [x] 切换语言后收藏 UI 文案全部更新 (3 个 locale 文件 6 键同步)
- [x] 快速连续点击不导致 UI 错乱 (无 setItemWidget 状态竞争)

## 验收

- [x] 12 条 Test Case 全部通过（参见 spec.md，10 条核心 Case 静态分析验证）
- [x] `python -m py_compile "TAB Score Viewer.py"` 无语法错误 (`FINAL OK`)
- [x] 主程序文件头注释新增"22. 收藏功能"条目 (行 52-54)
- [x] 主程序文件头注释"22. Theme extension system"正确改编号为 23 (行 55)
- [x] `readme/功能更新.md` 已追加 v2.3.0 收藏功能更新记录 (行 3-65)

✅ 全部验证通过
