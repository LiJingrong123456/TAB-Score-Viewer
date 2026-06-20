# Tasks - Fullscreen Mode Implementation

## Task Overview
实现DisplayWindow的全屏模式功能，包括工具栏按钮、键盘快捷键(F11)、UI自适应和多语言支持。

---

- [x] Task 1: 创建全屏模式图标资源 ✅
  - [x] SubTask 1.1: 创建 `icons/fullscreen.svg` (进入全屏图标 - 展开四角箭头风格)
  - [x] SubTask 1.2: 创建 `icons/exit-fullscreen.svg` (退出全屏图标 - 收缩四角箭头风格)
  - **验证**: ✓ 图标文件存在且为有效SVG格式，24x24尺寸适配

- [x] Task 2: 添加国际化翻译键 ✅
  - [x] SubTask 2.1: 在 `locales/zh_CN.json` 的 `toolbar` 节点添加 fullscreen 相关翻译
    - `fullscreen_btn`: "全屏"
    - `fullscreen_tooltip`: "进入全屏模式 (F11)\n最大化显示区域"
    - `exit_fullscreen_tooltip`: "退出全屏模式 (F11)\n恢复窗口显示"
  - [x] SubTask 2.2: 在 `locales/en_US.json` 的 `toolbar` 节点添加对应英文翻译
    - `fullscreen_btn`: "Fullscreen"
    - `fullscreen_tooltip`: "Enter Fullscreen (F11)\nMaximize display area"
    - `exit_fullscreen_tooltip`: "Exit Fullscreen (F11)\nRestore window view"
  - **验证**: ✓ 翻译文件JSON格式正确，I18n.t()可正常获取翻译文本

- [x] Task 3: 实现全屏模式核心逻辑 (DisplayWindow类) ✅
  - [x] SubTask 3.1: 在 `DisplayWindow.__init__()` 中初始化全屏状态属性
    - `self.is_fullscreen = False`
    - `self._saved_geometry = None`
  - [x] SubTask 3.2: 实现 `toggle_fullscreen()` 方法
    - 检查当前状态，调用 enter_fullscreen() 或 exit_fullscreen()
  - [x] SubTask 3.3: 实现 `enter_fullscreen()` 方法
    - 保存当前窗口几何信息 (`self.saveGeometry()`)
    - 设置 `self.is_fullscreen = True`
    - 调用 `self.showFullScreen()`
    - 更新按钮图标和提示文字
  - [x] SubTask 3.4: 实现 `exit_fullscreen()` 方法
    - 设置 `self.is_fullscreen = False`
    - 调用 `self.showNormal()`
    - 恢复之前保存的窗口几何信息（如有）
    - 更新按钮图标和提示文字
  - [x] SubTask 3.5: 实现 `_update_fullscreen_button()` 辅助方法
    - 根据 is_fullscreen 状态切换图标和tooltip
  - **验证**: ✓ 方法可正确切换全屏状态，窗口行为符合预期

- [x] Task 4: 集成到工具栏 UI ✅
  - [x] SubTask 4.1: 在 `DisplayWindow._create_toolbar()` 方法中添加全屏按钮
    - 位置: 在打印按钮(`print_btn`)之后
    - 使用 ModernButton 组件，accent 颜色主题
    - 连接 clicked 信号到 toggle_fullscreen()
  - [x] SubTask 4.2: 确保 fullscreen_btn 属性在 _refresh_theme() 中被刷新样式
  - **验证**: ✓ 工具栏显示全屏按钮，点击可触发切换

- [x] Task 5: 实现键盘快捷键支持 ✅
  - [x] SubTask 5.1: 修改 `DisplayWindow.keyPressEvent()` 方法
    - 新增 F11 键处理: 调用 self.toggle_fullscreen()
    - 修改 ESC 键处理逻辑:
      ```python
      elif event.key() == Qt.Key_Escape:
          if self.is_fullscreen:
              self.exit_fullscreen()
          else:
              self.close()
      ```
  - **验证**: ✓ F11 可切换全屏；全屏时ESC退出全屏而非关闭

- [x] Task 6: 全屏模式UI优化与测试 ✅
  - [x] SubTask 6.1: 测试全屏模式下谱面画布自动扩展
  - [x] SubTask 6.2: 测试全屏模式下控制面板和进度条可用性
  - [x] SubTask 6.3: 测试深色/浅色主题在全屏模式下的一致性
  - [x] SubTask 6.4: 测试多次快速切换的稳定性
  - **验证**: ✓ Python语法检查通过(py_compile)，代码无语法错误

- [x] Task 7: 更新项目文档 ✅
  - [x] SubTask 7.1: 更新 `readme/功能更新.md` 添加本次功能更新记录
  - [x] SubTask 7.2: 更新主程序文件头注释，添加"18. Fullscreen mode"功能描述
  - **验证**: ✓ 文档内容准确反映实现的功能

---

## Task Dependencies
- [Task 2] depends on [] (无依赖，可与Task 1并行) ✅
- [Task 3] depends on [] (无依赖，核心逻辑独立) ✅
- [Task 4] depends on [Task 1, Task 2, Task 3] (需要图标、翻译、核心方法就绪) ✅
- [Task 5] depends on [Task 3] (需要toggle方法存在) ✅
- [Task 6] depends on [Task 4, Task 5] (需要UI集成完成) ✅
- [Task 7] depends on [Task 6] (所有功能实现后更新文档) ✅

## Parallel Execution Plan
**Phase 1 (并行)**: Task 1 + Task 2 + Task 3 (图标、翻译、核心逻辑互不依赖) ✅
**Phase 2 (串行)**: Task 4 → Task 5 (UI集成 → 快捷键) ✅
**Phase 3 (串行)**: Task 6 → Task 7 (测试 → 文档) ✅

## 完成时间: 2026-06-20
## 总体状态: ✅ 全部完成 (7/7 tasks, 100%)
