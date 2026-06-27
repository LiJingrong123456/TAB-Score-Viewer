# Tasks

- [x] Task 1: 创建 `SettingsDialog` 类与基础 UI 结构
  - [x] SubTask 1.1: 在 `TAB Score Viewer.py` 中新增 `SettingsDialog(QDialog)` 类，文件头注释说明用途
  - [x] SubTask 1.2: 使用 `QTabWidget` 或 `QGroupBox` 创建「常规」和「GTP 渲染」两个分组
  - [x] SubTask 1.3: 应用当前主题样式表，保持深色/浅色模式一致
  - [x] SubTask 1.4: 添加「确定」「取消」按钮，点击确定保存配置并关闭，取消不保存

- [x] Task 2: 实现「常规」设置项
  - [x] SubTask 2.1: 语言选择下拉框（复用 `I18n.available_languages()`）
  - [x] SubTask 2.2: 主题选择下拉框（复用 `ThemeManager.available_themes()`）
  - [x] SubTask 2.3: UI 字体选择下拉框/输入框（列出系统可用字体或提供常用字体列表）
  - [x] SubTask 2.4: 从当前配置加载上述三项的默认值

- [x] Task 3: 实现「GTP 渲染」设置项
  - [x] SubTask 3.1: GTP 渲染字体选择（修改 `RenderConfig.NOTE_FONT_FAMILY`）
  - [x] SubTask 3.2: 为 `RenderConfig` 第 359–390 行的每个参数创建对应控件
    - 数值型参数使用 `QSpinBox` / `QDoubleSpinBox`
    - 每个控件旁添加中文标签，并在注释/标签说明中描述参数作用及调整效果
  - [x] SubTask 3.3: 定义渲染参数到控件的双向映射，保存时批量写回 `RenderConfig` 类属性

- [x] Task 4: 改造 `SelectionWindow` 主界面
  - [x] SubTask 4.1: 移除 `init_ui()` 中的语言和主题下拉框布局
  - [x] SubTask 4.2: 在主界面合适位置（如文件夹选择行右侧）添加「设置」按钮（齿轮 SVG 图标）
  - [x] SubTask 4.3: 绑定按钮点击事件，打开 `SettingsDialog` 并传入当前配置
  - [x] SubTask 4.4: 设置对话框关闭后，根据返回结果刷新主界面必要文本/样式

- [x] Task 5: 扩展配置持久化
  - [x] SubTask 5.1: 扩展 `save_config()`，新增 `ui_font`、`gtp_font`、`render_config` 字段
  - [x] SubTask 5.2: 扩展 `load_config()` 和启动恢复逻辑，读取并应用新增字段
  - [x] SubTask 5.3: 提供默认值和兼容性处理（旧配置缺失新字段时使用默认值）

- [x] Task 6: 运行时应用与刷新
  - [x] SubTask 6.1: 主题切换保持实时刷新所有窗口
  - [x] SubTask 6.2: UI 字体切换后实时刷新 `SelectionWindow` 和已打开 `DisplayWindow` 的样式表
  - [x] SubTask 6.3: GTP 渲染参数修改后，提示用户「重新打开 GTP 文件后生效」或自动重新加载当前文件

- [x] Task 7: 多语言翻译与文档同步
  - [x] SubTask 7.1: 在 `locales/zh_CN.json` 和 `locales/en_US.json` 中添加设置面板相关翻译键
  - [x] SubTask 7.2: 在 `locales/ru_RU.json` 中补充 `settings_dialog` 翻译键，保持俄语界面完整
  - [x] SubTask 7.3: 更新 `readme/功能更新.md`（超过 200 行时删除最旧记录）
  - [x] SubTask 7.4: 同步更新 `readme/开发文档.md` 和 `readme/实施文档.md` 中关于设置界面和渲染参数的说明
  - [x] SubTask 7.5: 更新 `TAB Score Viewer.py` 文件头注释，说明新增设置面板功能

- [x] Task 8: 验证与测试
  - [x] SubTask 8.1: 语法检查 `python -m py_compile "TAB Score Viewer.py"`
  - [x] SubTask 8.2: 验证设置对话框能正常打开、保存、取消
  - [x] SubTask 8.3: 验证语言和主题切换行为与之前一致
  - [x] SubTask 8.4: 验证 UI 字体切换实时生效
  - [x] SubTask 8.5: 验证 GTP 渲染参数保存后，重新打开 GTP 文件渲染效果变化

# Task Dependencies

- Task 2 依赖 Task 1
- Task 3 依赖 Task 1
- Task 4 依赖 Task 1
- Task 5 依赖 Task 2 和 Task 3
- Task 6 依赖 Task 4 和 Task 5
- Task 7 依赖 Task 6
- Task 8 依赖 Task 7
