# 音色库缺失提示功能 (SoundFont Missing Prompt) Spec

## Why
GTP 文件播放依赖 `FluidR3_GM.sf2` 音色库（由 `ApolloTab.audio.synth_engine.SynthEngine` 通过 `SOUNDFONT_SEARCH_PATHS` 加载）。当前程序在用户打开第一个 GTP 文件并初始化音频引擎失败时，只会把音频按钮置灰并设置 tooltip，**缺少对"为什么没有声音"的引导**——绝大多数用户不会主动去查错误 tooltip。

在程序启动时检测一次音色库是否存在，如缺失立即弹出**专门的引导窗口**，告知用户：
1. 音色库缺失导致 GTP 播放不可用；
2. 在源码/打包模式下应放在哪个目录；
3. 提供一键下载链接（`https://musical-artifacts.com/artifacts/1229`）；
4. 用户可选择"了解"暂不处理或"下载"立即获取。

避免用户因"无声"问题放弃使用。

## What Changes
- 在 `__main__` 启动流程中、**主窗口显示之前**调用 `_check_and_prompt_soundfont()`，**只检测一次**（每次进程启动一次，不随目录切换重复弹窗）。
- 复用 `_init_audio_engine` 中已有的 4 类搜索路径：
  1. **开发模式**：`<项目根>/soundfont/FluidR3_GM.sf2`
  2. **PyInstaller onedir (Windows/Linux)**：`<exe_dir>/_internal/soundfont/FluidR3_GM.sf2`
  3. **PyInstaller onedir (Windows spec 用 '.')**：`<exe_dir>/soundfont/FluidR3_GM.sf2`
  4. **macOS .app bundle**：`<.app>/Contents/Resources/soundfont/FluidR3_GM.sf2`
- 任意一处存在 → 视为已配置，**不弹窗**。
- 全部不存在 → 弹出自定义 `QDialog`（`SoundFontMissingDialog`），**无模式阻塞**（主窗口可以照常加载列表），但默认置顶吸引注意。
- 新增三语翻译键（`soundfont_missing` 节点）：
  - `title` / `main_message` / `source_hint` / `macos_hint` / `win_linux_hint` / `recommend_label` / `download_btn` / `got_it_btn`
- 关键交互：
  - **下载按钮** → 用 `QDesktopServices.openUrl(QUrl("https://musical-artifacts.com/artifacts/1229"))` 打开浏览器 → 关闭对话框
  - **了解按钮** → 关闭对话框
  - 用户关闭主窗口 → 对话框自动关闭（避免悬挂进程）
  - **不修改**音频引擎加载逻辑，仅在缺失时给用户引导

## Impact
- Affected specs: 无（新功能）
- Affected code:
  - `TAB Score Viewer.py`
    - 在 `if __name__ == '__main__'` 中、`SelectionWindow()` 实例化之后、`app.exec_()` 之前调用新方法
    - 新增 `_check_and_prompt_soundfont()` 方法
    - 新增 `_resolve_soundfont_search_paths() -> List[str]` 辅助方法（复用 `_init_audio_engine` 的搜索路径解析逻辑）
    - 新增内部类 `SoundFontMissingDialog(QDialog)`
  - `locales/zh_CN.json` / `en_US.json` / `ru_RU.json` - 各 +8 键
  - `readme/功能更新.md` - 追加 v2.5.3 记录
- 不影响：音频引擎、GTP 解析、收藏、难度评分、设置面板、最近文件、节拍器

## ADDED Requirements

### Requirement: 启动时音色库存在性检测
The system SHALL detect whether `FluidR3_GM.sf2` is accessible in any of the supported search paths when the program launches.

#### Scenario: 启动期检测
- **WHEN** `if __name__ == '__main__'` 主流程创建 `QApplication` 之后、`SelectionWindow()` 显示之后
- **THEN** 调用 `SelectionWindow._check_and_prompt_soundfont()`
- **AND** 收集所有候选路径（开发模式 + 3 类打包模式）
- **AND** 任意路径下 `FluidR3_GM.sf2` 文件存在 → 立即返回（不弹窗）
- **AND** 全部缺失 → 弹出 `SoundFontMissingDialog`

#### Scenario: 候选路径解析
- **WHEN** `_resolve_soundfont_search_paths()` 被调用
- **THEN** 返回以下路径列表（按检索顺序）：
  1. **开发模式**：`os.path.join(_APP_BASE_DIR, 'soundfont')`
  2. **PyInstaller onedir (Windows/Linux)**：`os.path.join(exe_dir, '_internal', 'soundfont')`
  3. **PyInstaller onedir (Windows spec 用 '.')**：`os.path.join(exe_dir, 'soundfont')`
  4. **macOS .app bundle**：`os.path.join(<Resources>, 'soundfont')`
- **AND** 若 `getattr(sys, 'frozen', False)` 为 True → 添加 2/3/4 三条
- **AND** 否则（开发模式）→ 仅添加第 1 条
- **AND** 每条路径对应的**目录**存在才纳入搜索（避免无效路径噪声）

#### Scenario: 一次进程仅一次检测
- **WHEN** 主窗口被打开后用户切换目录
- **THEN** **不再**重新检测音色库（避免每次切换都弹窗骚扰用户）
- **AND** 仅依赖进程内 `self._soundfont_prompted: bool` 标志，首次检测后置为 True

#### Scenario: 检测异常静默
- **WHEN** `_resolve_soundfont_search_paths()` 内部出现异常（如 `sys.executable` 读取失败、路径拼接异常）
- **THEN** 静默忽略，主程序不崩溃
- **AND** 视为"未配置"→ 弹窗引导

### Requirement: SoundFontMissingDialog 弹窗
The system SHALL provide a custom `QDialog` that informs the user about the missing soundfont and provides download/got-it actions.

#### Scenario: 弹窗内容
- **WHEN** 弹窗显示
- **THEN** 包含以下元素（自上而下）：
  1. **标题**：使用翻译键 `soundfont_missing.title`
  2. **主消息**：`soundfont_missing.main_message`
     - 默认（zh_CN）：`未找到 FluidR3_GM.sf2 音色库，GTP 文件播放将不可用。`
  3. **路径说明（多平台）**：
     - `soundfont_missing.source_hint`（源码运行）：`如果是从源码运行，请将音色库文件放到项目根目录的 soundfont 文件夹。`
     - `soundfont_missing.macos_hint`（macOS 打包）：`macOS（打包好的 .app）：<app>.app/Contents/Resources/soundfont/`
     - `soundfont_missing.win_linux_hint`（Windows/Linux 打包）：`Windows / Linux：可执行文件同目录的 _internal/soundfont/`
  4. **下载推荐**：
     - `soundfont_missing.recommend_label`：`推荐下载：` + URL `https://musical-artifacts.com/artifacts/1229`（可点击）
     - 附带说明：`下载后请重命名为 FluidR3_GM.sf2`
  5. **按钮区**（右下角）：
     - **下载按钮**（`soundfont_missing.download_btn`，主色高亮）
     - **了解按钮**（`soundfont_missing.got_it_btn`，次要色）

#### Scenario: 下载按钮交互
- **WHEN** 用户点击「下载」按钮
- **THEN** 调用 `QDesktopServices.openUrl(QUrl("https://musical-artifacts.com/artifacts/1229"))` 打开系统默认浏览器
- **AND** 弹窗自动 `accept()` 关闭
- **AND** 主程序继续正常运行

#### Scenario: 了解按钮交互
- **WHEN** 用户点击「了解」按钮
- **THEN** 弹窗立即 `accept()` 关闭
- **AND** **不**打开浏览器
- **AND** 主程序继续正常运行

#### Scenario: 关闭主窗口
- **WHEN** 用户在弹窗未关闭的情况下关闭 `SelectionWindow`
- **THEN** 弹窗自动 `reject()` 关闭，避免悬挂进程
- **AND** 弹窗 `setAttribute(Qt.WA_QuitOnClose, False)`：关闭弹窗**不**触发 `app.quit()`

#### Scenario: 弹窗样式
- **WHEN** 弹窗显示
- **THEN** 使用 PyQt5 Fusion 样式 + 主题色（与 `about_dialog` 风格一致）
- **AND** 窗口大小固定（约 560 × 380 px）
- **AND** 不可调整大小（`setFixedSize`）
- **AND** 默认置顶（`setWindowFlag(Qt.WindowStaysOnTopHint, True)`）

### Requirement: 国际化支持
The system SHALL provide trilingual translations (zh_CN / en_US / ru_RU) for all new UI strings.

#### Scenario: 必填键
- `soundfont_missing.title`
- `soundfont_missing.main_message`
- `soundfont_missing.source_hint`
- `soundfont_missing.macos_hint`
- `soundfont_missing.win_linux_hint`
- `soundfont_missing.recommend_label`
- `soundfont_missing.download_btn`
- `soundfont_missing.got_it_btn`

#### Scenario: 英文翻译示例（en_US）
- `title`: `SoundFont Library Missing`
- `main_message`: `FluidR3_GM.sf2 soundfont not found. GTP file playback will be unavailable.`
- `source_hint`: `If running from source, place the soundfont file in the project's root `soundfont` folder.`
- `macos_hint`: `macOS (packaged .app): <app>.app/Contents/Resources/soundfont/`
- `win_linux_hint`: `Windows / Linux: <executable_dir>/_internal/soundfont/`
- `recommend_label`: `Recommended download: https://musical-artifacts.com/artifacts/1229 (rename to FluidR3_GM.sf2)`
- `download_btn`: `Download`
- `got_it_btn`: `Got it`

#### Scenario: 俄文翻译示例（ru_RU）
- `title`: `Звуковая библиотека не найдена`
- `main_message`: `Не найдена библиотека FluidR3_GM.sf2. Воспроизведение GTP-файлов будет недоступно.`
- `source_hint`: `Если вы запускаете из исходного кода, поместите файл библиотеки в папку `soundfont` в корне проекта.`
- `macos_hint`: `macOS (упакованный .app): <app>.app/Contents/Resources/soundfont/`
- `win_linux_hint`: `Windows / Linux: <executable_dir>/_internal/soundfont/`
- `recommend_label`: `Рекомендуемая загрузка: https://musical-artifacts.com/artifacts/1229 (переименуйте в FluidR3_GM.sf2)`
- `download_btn`: `Скачать`
- `got_it_btn`: `Понятно`

## MODIFIED Requirements

### Requirement: `if __name__ == '__main__'`
在 `SelectionWindow()` 之后、`sys.exit(app.exec_())` 之前追加：
```python
# v2.5.3: 启动时检测音色库（如缺失则引导下载）
try:
    settings._check_and_prompt_soundfont()
except Exception as e:
    print(f"[SoundFont] 启动检测失败: {e}")
```

## REMOVED Requirements
None (pure additive)

## Technical Implementation Details

### `_check_and_prompt_soundfont()` 方法

```python
def _check_and_prompt_soundfont(self) -> None:
    """
    v2.5.3: 启动时检测 FluidR3_GM.sf2 是否存在。
    缺失则弹出 SoundFontMissingDialog 引导用户下载。
    每个进程仅执行一次。
    """
    if getattr(self, '_soundfont_prompted', False):
        return  # 已检测过，跳过
    self._soundfont_prompted = True

    try:
        import sys, os
        from PyQt5.QtCore import QUrl
        from PyQt5.QtGui import QDesktopServices

        search_dirs = self._resolve_soundfont_search_paths()
        for d in search_dirs:
            sf2_path = os.path.join(d, 'FluidR3_GM.sf2')
            if os.path.isfile(sf2_path):
                return  # 已配置

        # 全部缺失 → 弹窗
        dlg = SoundFontMissingDialog(self)
        dlg.exec_()
    except Exception as e:
        print(f"[SoundFont] 启动检测失败: {e}")
```

### `_resolve_soundfont_search_paths()` 方法

```python
def _resolve_soundfont_search_paths(self) -> list:
    """复用 _init_audio_engine 中的路径解析逻辑（仅返回存在的目录）"""
    import sys, os
    paths = []
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        for sub in ['_internal/soundfont', 'soundfont']:
            p = os.path.join(exe_dir, sub)
            if os.path.isdir(p):
                paths.append(p)
        if '.app/Contents/MacOS' in exe_dir:
            resources_dir = os.path.join(os.path.dirname(exe_dir), 'Resources')
            p = os.path.join(resources_dir, 'soundfont')
            if os.path.isdir(p):
                paths.append(p)
    else:
        p = os.path.join(_APP_BASE_DIR, 'soundfont')
        if os.path.isdir(p):
            paths.append(p)
    return paths
```

### `SoundFontMissingDialog` 类

```python
class SoundFontMissingDialog(QDialog):
    """
    v2.5.3: 音色库缺失引导对话框
    - 显示缺失说明与各平台路径
    - 提供「下载」按钮(打开浏览器)和「了解」按钮(直接关闭)
    - 默认置顶、无模式阻塞
    """
    SOUNDFONT_URL = "https://musical-artifacts.com/artifacts/1229"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(I18n.t("soundfont_missing.title"))
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WA_QuitOnClose, False)  # 关闭弹窗不退出主程序
        self.setFixedSize(560, 380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 主消息
        msg = QLabel(I18n.t("soundfont_missing.main_message"))
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(msg)

        # 路径说明
        hint_box = QTextEdit()
        hint_box.setReadOnly(True)
        hint_box.setStyleSheet("font-size: 12px; background: transparent; border: none;")
        hint_text = (
            f"{I18n.t('soundfont_missing.source_hint')}\n"
            f"{I18n.t('soundfont_missing.macos_hint')}\n"
            f"{I18n.t('soundfont_missing.win_linux_hint')}"
        )
        hint_box.setPlainText(hint_text)
        layout.addWidget(hint_box)

        # 下载推荐
        recommend = QLabel(
            f"{I18n.t('soundfont_missing.recommend_label')}<br>"
            f"<a href='{self.SOUNDFONT_URL}'>{self.SOUNDFONT_URL}</a>"
        )
        recommend.setOpenExternalLinks(True)
        recommend.setTextFormat(Qt.RichText)
        recommend.setWordWrap(True)
        layout.addWidget(recommend)

        # 按钮
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        download_btn = QPushButton(I18n.t("soundfont_missing.download_btn"))
        download_btn.setDefault(True)
        download_btn.clicked.connect(self._on_download)
        got_it_btn = QPushButton(I18n.t("soundfont_missing.got_it_btn"))
        got_it_btn.clicked.connect(self.accept)
        btn_box.addWidget(download_btn)
        btn_box.addWidget(got_it_btn)
        layout.addLayout(btn_box)

    def _on_download(self):
        QDesktopServices.openUrl(QUrl(self.SOUNDFONT_URL))
        self.accept()
```

### 触发位置

`if __name__ == '__main__'` 入口的 `SelectionWindow()` 之后：

```python
settings = SelectionWindow()
# v2.5.3: 启动检测音色库
try:
    settings._check_and_prompt_soundfont()
except Exception as e:
    print(f"[SoundFont] 启动检测失败: {e}")
sys.exit(app.exec_())
```

## Test Cases

| Case | 场景 | 预期结果 |
|------|------|----------|
| 1 | 源码运行，根目录 `soundfont/` 下存在 `FluidR3_GM.sf2` | 启动不弹窗 |
| 2 | 源码运行，根目录 `soundfont/` 缺失或 `FluidR3_GM.sf2` 不存在 | 启动时弹窗，按钮齐备 |
| 3 | 打包 .app 运行，`.app/Contents/Resources/soundfont/FluidR3_GM.sf2` 存在 | 启动不弹窗 |
| 4 | 打包 onedir (Windows)，`_internal/soundfont/FluidR3_GM.sf2` 存在 | 启动不弹窗 |
| 5 | 打包 onedir (Windows)，`_internal/soundfont/` 缺失但 `soundfont/FluidR3_GM.sf2` 存在 | 启动不弹窗（fallback） |
| 6 | 点击「下载」按钮 | 浏览器打开指定 URL，弹窗关闭 |
| 7 | 点击「了解」按钮 | 弹窗关闭，浏览器未打开 |
| 8 | 弹窗显示时关闭主窗口 | 弹窗自动关闭，进程正常退出 |
| 9 | 关闭弹窗后再切换目录 | **不**重新弹窗（`_soundfont_prompted=True`） |
| 10 | 启动后通过 `load_file_list_async` 加载 GTP 列表 | 列表正常加载，弹窗不影响列表 |
| 11 | 切换语言（zh ↔ en ↔ ru）后重启 | 弹窗文字切换为对应语言 |
| 12 | `sys.executable` 读取失败 | 异常静默，主程序不崩溃 |
| 13 | 所有候选路径均不存在 | 弹窗显示 4 条平台路径说明 + 下载链接 |
| 14 | 弹窗焦点测试（点其他窗口） | 弹窗置顶在最前（`WindowStaysOnTopHint`） |
| 15 | 关闭主窗口时弹窗尚未关闭 | 进程不悬挂（`WA_QuitOnClose=False`） |
