# Checklist - 音色库缺失提示 (SoundFont Missing Prompt) 实施

## 路径解析

- [x] **`_resolve_soundfont_search_paths()` 已实现**
  - [x] 返回 `List[str]`，仅包含**目录存在**的路径
  - [x] 开发模式：`<项目根>/soundfont/`
  - [x] onedir (Windows/Linux) `_internal/soundfont/`
  - [x] onedir (Windows spec 用 '.') `soundfont/`
  - [x] macOS .app bundle `Contents/Resources/soundfont/`
  - [x] 异常（`sys.executable` 读取失败、OSError）静默处理

- [x] **`_init_audio_engine` 现有逻辑保持不变**
  - [x] 3066-3098 行搜索路径注册代码未被破坏

## 启动检测

- [x] **`_check_and_prompt_soundfont()` 方法**
  - [x] 在 `SelectionWindow` 中新增
  - [x] 检查 `FluidR3_GM.sf2` 是否在任一候选路径
  - [x] 任一存在 → 立即返回（不弹窗）
  - [x] 全部缺失 → 弹 `SoundFontMissingDialog`
  - [x] 设置 `self._soundfont_prompted = True`
  - [x] 整体 try/except 包裹

- [x] **`__init__` 中新增 `_soundfont_prompted: bool = False`**

- [x] **触发位置**
  - [x] `if __name__ == '__main__'` 中 `SelectionWindow()` 之后
  - [x] `app.exec_()` 之前
  - [x] 整体 try/except 包裹

## SoundFontMissingDialog

- [x] **类已定义**
  - [x] 继承 `QDialog`
  - [x] `SOUNDFONT_URL = "https://musical-artifacts.com/artifacts/1229"` 常量

- [x] **窗口属性**
  - [x] 标题：使用 `I18n.t("soundfont_missing.title")`
  - [x] 固定尺寸 560×380
  - [x] `setWindowFlag(Qt.WindowStaysOnTopHint, True)` 置顶
  - [x] `setAttribute(Qt.WA_QuitOnClose, False)` 关闭不退出主程序

- [x] **内容组件**
  - [x] 主消息 `QLabel`（加粗 13px，自动换行）
  - [x] 路径说明 `QTextEdit`（只读，3 平台）
  - [x] 下载推荐 `QLabel`（含可点击 URL）
  - [x] 按钮区 `QHBoxLayout`（下载 / 了解）

- [x] **按钮交互**
  - [x] 「下载」按钮 → `QDesktopServices.openUrl(QUrl(SOUNDFONT_URL))` + `self.accept()`
  - [x] 「了解」按钮 → `self.accept()`（不打开浏览器）
  - [x] 「下载」按钮为 `setDefault(True)` 默认按钮

## 三语翻译

- [x] **zh_CN.json 新增 `soundfont_missing` 节点**
  - [x] `title`
  - [x] `main_message`
  - [x] `source_hint`
  - [x] `macos_hint`
  - [x] `win_linux_hint`
  - [x] `recommend_label`
  - [x] `download_btn`
  - [x] `got_it_btn`

- [x] **en_US.json 新增对应 8 个键**
- [x] **ru_RU.json 新增对应 8 个键**
- [x] **三语 JSON 语法合法**

## 验证

- [x] **`python -m py_compile "TAB Score Viewer.py"` 无语法错误**
- [x] **三语 JSON `json.load()` 通过**
- [ ] **15 条 Test Case 全部通过**（详见 spec.md 表格 1-15）
  - [ ] Case 1: 源码模式 + 音色库存在 → 不弹窗
  - [ ] Case 2: 源码模式 + 音色库缺失 → 弹窗
  - [ ] Case 3: macOS .app + 音色库存在 → 不弹窗
  - [ ] Case 4: Windows onedir + 音色库存在 → 不弹窗
  - [ ] Case 5: Windows onedir fallback → 不弹窗
  - [ ] Case 6: 点击下载 → 浏览器打开 + 弹窗关闭
  - [ ] Case 7: 点击了解 → 弹窗关闭，浏览器未打开
  - [ ] Case 8: 弹窗显示时关闭主窗口 → 弹窗自动关闭
  - [ ] Case 9: 关闭弹窗后切换目录 → 不重新弹窗
  - [ ] Case 10: 弹窗显示时加载文件列表 → 列表正常加载
  - [ ] Case 11: 切换语言 → 弹窗文字切换
  - [ ] Case 12: `sys.executable` 异常 → 不崩溃
  - [ ] Case 13: 全部路径缺失 → 弹窗显示 4 条说明
  - [ ] Case 14: 弹窗置顶测试
  - [ ] Case 15: 关闭主窗口时弹窗未关闭 → 进程不悬挂

## 文档

- [ ] **`readme/功能更新.md` 追加 v2.5.3 记录**
- [ ] **主程序文件头注释新增「25. 启动时音色库缺失提示」条目**
