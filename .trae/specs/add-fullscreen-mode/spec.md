# Fullscreen Mode Spec (全屏模式)

## Why
用户在查看吉他谱时需要更大的显示区域来获得更好的阅读体验，特别是在演示或练习场景下。当前DisplayWindow固定大小(1100x850)，无法充分利用屏幕空间。实现全屏模式可以让谱面内容占据整个屏幕，提升用户体验。

## What Changes
- 在DisplayWindow顶部工具栏新增**全屏切换按钮**（F11快捷键支持）
- **全屏模式行为**:
  - 隐藏窗口标题栏和边框（Qt.FramelessWindowHint）
  - 谱面画布自动扩展填充整个屏幕
  - 工具栏和控制面板保持可用（可选择性简化显示）
  - 底部进度条保持可见
- **退出方式**:
  - 再次点击全屏按钮
  - 按F11键
  - 按ESC键（修改原有ESC关闭行为为：全屏模式下ESC退出全屏而非关闭窗口）
- **状态持久化**: 记住用户上次是否使用全屏模式（可选）
- **多语言支持**: 添加中英文翻译键
- **图标资源**: 新增fullscreen/exit-fullscreen SVG图标

## Impact
- Affected specs: 无（新功能）
- Affected code:
  - `TAB Score Viewer.py` - DisplayWindow类（主要改动）
  - `locales/zh_CN.json` - 中文翻译
  - `locales/en_US.json` - 英文翻译
  - `icons/` - 新增SVG图标文件
  - `readme/功能更新.md` - 更新日志

## ADDED Requirements

### Requirement: Fullscreen Toggle Button (全屏切换按钮)
The system SHALL provide a fullscreen toggle button in the DisplayWindow toolbar.

#### Scenario: Enter fullscreen mode
- **WHEN** user clicks the fullscreen button OR presses F11 key
- **THEN** the DisplayWindow enters fullscreen mode:
  - Window decoration (title bar, borders) is hidden
  - Window expands to fill entire screen
  - Toolbar remains visible at top
  - Control panel and progress bar remain accessible
  - Button icon changes to "exit fullscreen" indicator
  - Tooltip updates to indicate exit action

#### Scenario: Exit fullscreen mode
- **WHEN** user clicks the exit fullscreen button OR presses F11 OR presses ESC (when in fullscreen)
- **THEN** the DisplayWindow exits fullscreen mode:
  - Window restores to previous size and position
  - Window decoration reappears
  - All UI elements return to normal layout
  - Button icon changes back to "enter fullscreen"
  - Tooltip updates to indicate enter action

### Requirement: Keyboard Shortcuts (键盘快捷键)
The system SHALL support F11 and modified ESC behavior for fullscreen control.

#### Scenario: F11 toggle
- **WHEN** user presses F11 key in DisplayWindow
- **THEN** fullscreen mode toggles (enter if windowed, exit if fullscreen)

#### Scenario: ESC behavior modification
- **WHEN** user presses ESC key in normal windowed mode
- **THEN** window closes (existing behavior preserved)
- **WHEN** user presses ESC key in fullscreen mode
- **THEN** exits fullscreen instead of closing window (new behavior)

### Requirement: UI Adaptation (UI自适应)
The system SHALL adapt the interface layout when entering/exiting fullscreen.

#### Scenario: Fullscreen layout optimization
- **WHEN** entering fullscreen mode on different screen resolutions
- **THEN** the display widget automatically resizes to fill available space
- **AND** splitter proportions are maintained or optimized for wider screens
- **AND** all interactive controls remain functional

#### Scenario: Theme consistency
- **WHEN** toggling fullscreen mode
- **THEN** current theme (dark/light) is preserved without visual glitches
- **AND** all colors and styles remain consistent

### Requirement: Internationalization (国际化)
The system SHALL provide bilingual support for fullscreen feature.

#### Scenario: Chinese locale
- **WHEN** system language is zh_CN
- **THEN** button tooltip shows "进入全屏" / "退出全屏"
- **AND** all related UI text is in Simplified Chinese

#### Scenario: English locale
- **WHEN** system language is en_US
- **THEN** button tooltip shows "Enter Fullscreen" / "Exit Fullscreen"
- **AND** all related UI text is in English

## MODIFIED Requirements

### Requirement: DisplayWindow.keyPressEvent (键盘事件处理)
Modified to add F11 handling and conditional ESC behavior:

```python
def keyPressEvent(self, event):
    # ... existing code ...
    elif event.key() == Qt.Key_F11:        # NEW: F11 切换全屏
        self.toggle_fullscreen()
    elif event.key() == Qt.Key_Escape:     # MODIFIED: 全屏时退出全屏，否则关闭
        if self.is_fullscreen:
            self.exit_fullscreen()
        else:
            self.close()
```

### Requirement: DisplayWindow._create_toolbar (工具栏创建)
Modified to include fullscreen button after existing buttons:

```python
# After print_btn in _create_toolbar()
self.fullscreen_btn = ModernButton(I18n.t("toolbar.fullscreen_btn"), 'accent', 'fullscreen')
self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
tb.addWidget(self.fullscreen_btn)
```

## REMOVED Requirements
None (pure additive feature)

## Technical Implementation Details

### Core Methods to Add
1. `toggle_fullscreen()` - 切换全屏/窗口模式的主方法
2. `enter_fullscreen()` - 进入全屏模式的详细逻辑
3. `exit_fullscreen()` - 退出全屏模式的详细逻辑
4. `_save_window_state()` - 保存当前窗口状态（位置/大小）
5. `_restore_window_state()` - 恢复之前保存的窗口状态

### State Management
- `is_fullscreen: bool` - 当前是否处于全屏模式
- `_saved_geometry: QRect` - 进入全屏前保存的窗口几何信息
- `_saved_window_flags: Qt.WindowFlags` - 原始窗口标志位

### Qt API Usage
- `showFullScreen()` - 显示全屏窗口
- `showNormal()` - 恢复正常窗口显示
- `setWindowFlags()` - 修改窗口标志（隐藏标题栏等）

### Icon Resources Needed
- `icons/fullscreen.svg` - 进入全屏图标（展开四角箭头）
- `icons/exit-fullscreen.svg` - 退出全屏图标（收缩四角箭头）或复用同一图标

## Test Cases (10 Cases)

| Case | 场景 | 预期结果 |
|------|------|----------|
| 1 | 点击全屏按钮进入全屏 | 窗口无标题栏，填满屏幕，按钮变为退出图标 |
| 2 | 全屏状态下点击退出按钮 | 窗口恢复正常大小位置，标题栏重现 |
| 3 | 按F11键进入全屏 | 同Case 1 |
| 4 | 全屏状态按F11键 | 同Case 2 |
| 5 | 全屏状态按ESC键 | 退出全屏（不关闭窗口） |
| 6 | 窗口状态按ESC键 | 关闭窗口（保持原有行为） |
| 7 | 全屏模式下播放音乐 | 正常播放，进度条更新，控制面板可用 |
| 8 | 全屏模式下切换主题 | 主题正常切换，无样式异常 |
| 9 | 不同分辨率屏幕进入全屏 | 自适应填充，控件不溢出 |
| 10 | 多次快速切换全屏 | 无闪烁或布局错乱，状态正确同步 |
