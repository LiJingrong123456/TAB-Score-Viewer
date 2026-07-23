# TAB Score Viewer / 万能吉他谱查看器

**[English](#english)** | **[中文](#中文)**

A powerful Guitar TAB score viewer powered by [ApolloTab](https://github.com/Zhuwenqian/ApolloTab) engine, with multi-format support, smooth auto-scroll playback, speed curve control, text annotations, loop playback, audio synthesis, and multilingual UI.

一个功能强大的吉他谱（TAB）查看器，基于 ApolloTab 引擎，支持多种格式文件浏览、自动滚动播放（30fps平滑）、速度曲线调节、文本标注、循环播放和音频合成。

---

# English

<p align="center">
  <img src="renderedlight (1).png" alt="TAB Score Viewer - Light Theme Screenshot 1" width="45%" />
  <img src="renderedlight (2).png" alt="TAB Score Viewer - Dark Theme Screenshot 2" width="45%" />
</p>

## Features

| Feature                      | Description                                                                                           |
| ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Multi-format**             | PNG, JPG, JPEG, WEBP images; PDF documents; GP3/GP4/GP5/GPX Guitar Pro files                          |
| **GTP Parsing & Rendering**  | Powered by ApolloTab engine: complete parser, TAB renderer with 18 technique symbols, track switching |
| **Audio Playback**           | FluidSynth engine with SoundFont, All tracks / Single track / Mute modes, Pitch Bend gradual effect   |
| **Playhead**                 | Red vertical line following playback progress, current measure highlight                              |
| **Auto-scroll**              | 30fps fixed-rate smooth scrolling, time-driven (synced with music rhythm)                             |
| **Speed Control**            | Image/PDF: 1-500ms range; GTP: BPM-driven, auto-hides manual controls                                 |
| **Speed Curve Editor**       | Bezier curve visualization with preset templates (Image/PDF mode only)                                |
| **Loop Playback**            | No loop / Global loop / A-B region loop                                                               |
| **Text Annotations**         | Double-click to add notes with color/font/bold styles, hover to show delete button                    |
| **Annotation Import/Export** | Auto-load `.anno.json`, real-time save, per-track/per-page PNG/**JPG**/PDF A4 export (async with progress bar, cancel support) |
| **Annotation Manager**       | Dedicated dialog to batch browse, edit, delete, and create annotations                                |
| **Global Undo/Redo**         | Ctrl+Z / Ctrl+Y, max 50 steps                                                                         |
| **Favorites**                | Star-toggle any file from the list (hover star / right-click menu); dedicated favorites list above recent files (3 default, 6 expanded, scrollable) |
| **Difficulty Rating**        | Auto 0–10 star score for GTP files (length, BPM, techniques: bends/harmonics/tapping/vibrato/hammer-ons/pull-offs/slides); drum/piano/keyboard/bass tracks excluded; SQLite cache; tooltip on hover |
| **Custom Shortcuts**         | Per-action remapping in Settings → Shortcuts (click cell to capture, Esc/Backspace/Enter; conflict detection; reset all); max 3 keys; modifier-only disallowed |
| **Click-to-Play**            | Click anywhere on score to jump and start playback                                                    |
| **Page Navigation**          | Page input box for PDF/multi-image mode                                                               |
| **Mouse Wheel**              | Scroll with Ctrl (fast) / Shift (fine) modifiers                                                      |
| **Context Menu**             | Open file location (Windows/Linux compatible), add/remove favorite                                    |
| **Track Selection**          | Dropdown to switch tracks, instant re-render, per-track annotations                                   |
| **Dark/Light Theme**         | Modern dark/light UI with custom components + SVG icons (Lucide-style); custom JSON/Python theme loader |
| **Keyboard Shortcuts**       | Space play/pause, arrow keys, Ctrl+Z/Y undo/redo, ESC close                                           |
| **Multilingual UI**          | Chinese (Simplified) / English / Russian, one-click switch in settings                                |
| **About / Update Check**     | About dialog with version, ApolloTab credit, license, AI disclosure; GitHub Releases auto-check on launch (5s timeout, cancellable) |
| **Application Icon**         | Custom icon (icon.ico / icon.png) for window + taskbar                                                |
| **Cross-Platform Packaging** | PyInstaller packaging: Windows EXE, Linux DEB/ZIP, macOS APP (see [Packaging](#packaging--distribution)) |

## Quick Start

### Option 1: Run from Source (Requires Python)

**Requirements:** Python 3.8+, Windows / Linux / macOS

```bash
# Create virtual environment
python -m venv venv
# Activate virtual environment
.\venv\Scripts\activate   # Windows
source venv/bin/activate   # Linux/Mac

# Install dependencies (using Chinese mirror for faster download)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. Download SoundFont library (~140MB, required for GTP audio playback)
#    The program auto-searches SoundFont files in these locations:
#      - soundfont/ folder under project directory (recommended)
#      - ~/.fluidsynth/ in user home directory
#
#    Download from either source:
#      Official: https://ftp.osuosl.org/pub/musespan/SoundFonts/FluidR3_GM.sf2
#      Mirror:    https://github.com/FluidSynth/fluidsynth/wiki/SoundFont
#
#    Place in soundfont/ directory:
#      TAB Score Viewer/
#      ├── soundfont/
#      │   └── FluidR3_GM.sf2     <-- SoundFont file goes here
#      ├── TAB Score Viewer.py
#      └── ...

# Run
python "TAB Score Viewer.py"
```

### Option 2: Run EXE Directly (No Python Required)

> If you don't want to install Python, you can use the pre-packaged EXE directly.

```bash
# Build from source (requires dependencies installed first, see Option 1 steps 1-4)
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
pyinstaller "TAB Score Viewer.spec"

# Double-click TAB Score Viewer.exe to run
```

### Option 3: Linux DEB Package (Recommended)

> Pre-packaged `.deb` with auto dependency resolution, system-wide `tabsv` command.

```bash
# Install from .deb file (auto-resolves dependencies)
sudo dpkg -i tab-score-viewer_2.0.7_*.deb
sudo apt-get install -f  # Fix any missing deps

# Run (global command)
tabsv
```

> **Build your own DEB**: See [Packaging & Distribution](#packaging--distribution) for full instructions using `build_deb.sh`.

### Option 4: Linux ZIP Archive (Portable)

> Extract and run, but requires manual dependency installation.

```bash
# 1. Install system dependencies first
sudo apt-get install libfluidsynth3 libsndfile1 libpulse0 libasound2 \
    libqt5widgets5 libqt5gui5 libqt5core5a libc6

# 2. Extract and run
unzip tab-score-viewer-linux.zip
cd "TAB Score Viewer"
./"TAB Score Viewer"
```

> **Note**: For other distros (Fedora/Arch), see dependency commands in [Packaging & Distribution](#packaging--distribution).

### Option 5: macOS DMG Package (Recommended for macOS)

> Pre-packaged `.dmg` disk image with drag-and-drop installation. The DMG includes both the `.app` bundle and an `/Applications` shortcut for convenient installation.

```bash
# Build from source (requires dependencies installed first, see Option 1 steps 1-4)

# 1. Run preparation script (collects FluidSynth dylibs and fixes @rpath)
bash prepare_macos_build.sh

# 2. Build with macOS-specific spec file
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
pyinstaller "TAB Score Viewer_macOS.spec"

# 3. Generate DMG disk image
bash build_dmg.sh

# Output: dist/TAB Score Viewer_2.0.7.dmg
```

> **Installation**: Double-click the `.dmg` → drag `TAB Score Viewer.app` into the `Applications` folder.

### Usage

1. Launch the program, click "Select Folder" button to choose your guitar tab directory
2. File list shows all supported formats (PNG/JPG/WEBP/PDF/GP3-GP5/GPX), plus a separate **Favorites** list above the recent files; hover any entry to reveal a star button (or right-click → Add/Remove favorite). GTP files automatically show a 0–10 star **difficulty rating** as a tooltip on hover.
3. Double-click a file to open the score viewer:
   - Single image: Display and play directly
   - PDF: Render pages as images and concatenate
   - Multiple images: Sort by filename and display continuously
   - GTP files: Parse and render as tablature via ApolloTab engine, with audio, track switching, playhead cursor
4. Use toolbar and control panel for playback, speed adjustment, annotation, etc.
5. **Settings → Shortcuts** lets you remap any key binding. **Settings → About** checks for new releases.

## Shortcuts

Default bindings (all of them can be remapped in **Settings → Shortcuts**):

| Key       | Action           |
| --------- | ---------------- |
| `Space`   | Play / Pause     |
| `↑` / `↓` | Scroll up / down |
| `←` / `→` | Slower / Faster  |
| `Ctrl+Z`  | Undo annotation  |
| `Ctrl+Y`  | Redo annotation  |
| `ESC`     | Close window     |

> See [Custom Shortcuts](#custom-shortcuts) below for remapping rules and capture editor behavior.

## Mouse Operations

| Operation                | Function                        |
| ------------------------ | ------------------------------- |
| Scroll wheel             | Scroll score (default 30px/step) |
| `Ctrl + Scroll wheel`    | Fast scroll (100px/step)        |
| `Shift + Scroll wheel`   | Fine scroll (10px/step)         |
| Click on score           | Jump to position & start playing |
| Double-click blank area  | Create text annotation          |
| Double-click annotation  | Edit that annotation            |
| Progress bar drag        | Jump to playback position       |
| `Ctrl + click progress`  | Set loop point A                |
| `Shift + click progress` | Set loop point B                |

## Custom Shortcuts

Open **Settings → Shortcuts** to remap any action. The dialog lists 11 actions in a table (action on the left, binding on the right).

- **Capture mode**: click a cell to enter (highlighted yellow). Press your key combo to bind.
  - `Esc` cancels · `Backspace` clears (binds an empty string = permanently disables the action) · `Enter` confirms the held combo.
- **Rules**:
  - At least 1 non-modifier key is required.
  - Modifier keys (`Ctrl` / `Shift` / `Alt` / `Meta` / `CapsLock` / `Tab`) cannot be the only key in a binding; they must be combined with at least one regular key.
  - Maximum 3 keys per binding.
- **Conflict detection**: if the new combo is already used by another action, you'll be prompted to **Replace / Clear / Cancel**.
- **Cross-platform**: `Option` is treated as `Alt`; `Command` / `Win` / `Super` are all mapped to `Meta` so saved bindings stay portable. macOS automatically swaps the display names of `Ctrl` and `Cmd` so they match the physical key you pressed.
- **Reset All**: a single button restores all actions to their default bindings.
- **Persistence**: custom bindings are stored in `config/settings.json` under `custom_shortcuts`.

## Project Structure

```
TAB Score Viewer/
├── TAB Score Viewer.py      # Main program (SelectionWindow / DisplayWindow entry)
├── constants.py             # Shared constants (paths, default settings, key maps)
├── models.py                # Dataclasses for annotations, settings, file items
├── theme.py                 # ThemeManager (dark/light + custom JSON/Python themes)
├── i18n.py                  # I18n singleton for zh_CN / en_US / ru_RU translations
├── fonts.py                 # UI font selection helpers
├── config.py                # settings.json load/save with defaults
├── workers.py               # QRunnable workers (file load, rendering, etc.)
├── difficulty_scoring.py    # GTP difficulty rating engine + SQLite cache
├── shortcuts.py             # ShortcutAction / ShortcutManager (v2.5.0, cross-platform)
├── shortcuts_dialog.py      # ShortcutCustomizeDialog + capture editor (v2.5.0)
├── settings_dialog.py       # Settings window (general + theme + shortcuts tabs)
├── annotation_dialogs.py    # Annotation create / edit / manager dialogs
├── about_dialog.py          # About window with version, credit, update check button
├── update_checker.py        # Async GitHub Releases check (5s timeout)
├── TAB Score Viewer.spec    # PyInstaller packaging config (onedir mode, Windows)
├── TAB Score Viewer_linux.spec  # PyInstaller packaging config - Linux
├── TAB Score Viewer_macOS.spec  # PyInstaller packaging config - macOS
├── build_dmg.sh             # macOS DMG packaging script
├── prepare_macos_build.sh   # macOS: collect dylibs and fix @rpath
├── runtime_hook_macos.py    # macOS runtime hook: preload dylibs
├── icons/                   # SVG icon files (Lucide-style toolbar icons)
│   ├── annotate.svg         # Pencil/edit icon
│   ├── export.svg           # Download arrow icon
│   ├── chart.svg            # Trending line icon
│   ├── play.svg             # Play triangle icon
│   ├── stop.svg             # Stop square icon
│   ├── volume.svg           # Speaker icon
│   ├── star.svg             # Hollow star (favorite off)
│   ├── star-filled.svg      # Filled star (favorite on)
│   └── ...                  # (15 total icons)
├── icon.png                 # App icon source (PNG, 2048x2048)
├── icon.ico                 # App icon (ICO multi-size)
├── icon.icns                # App icon (macOS multi-size)
├── README.md                # Project documentation (this file)
├── requirements.txt         # Python dependencies
├── LICENSE                  # License file (MPL 2.0)
├── themes/                  # Custom theme drop-in directory (JSON / .py)
│   └── example_custom.json
├── locales/                 # Translation files
│   ├── zh_CN.json           # Simplified Chinese
│   ├── en_US.json           # English
│   └── ru_RU.json           # Russian
├── config/
│   └── settings.json        # User settings (auto-generated at runtime; stores custom_shortcuts, favorite_files, etc.)
├── data/
│   ├── annotations/         # Annotation data storage (JSON format, legacy compat)
│   └── difficulty_cache.db  # SQLite cache for GTP difficulty scores (v2.4.0)
├── libfluidsynth-3.dll      # FluidSynth dynamic lib (LGPL 2.1)
├── SDL3.dll                 # SDL3 dynamic lib (FluidSynth dependency)
├── sndfile.dll              # libsndfile dynamic lib (FluidSynth dependency)
├── soundfont/               # SoundFont directory (GTP audio required)
│   └── FluidR3_GM.sf2      # FluidSynth GM soundfont (~140MB, download required)
├── readme/                  # Project docs
│   ├── 功能更新.md           # Changelog
│   ├── 开发文档.md           # Development doc
│   └── 实施文档.md           # Deployment doc
└── venv/                    # Python virtual env (not in version control)
```

## Tech Stack

| Category       | Technology                                           | Description                                                            |
| -------------- | ---------------------------------------------------- | ---------------------------------------------------------------------- |
| **GUI**        | PyQt5 >= 5.15                                        | Qt for Python framework                                                |
| **PDF**        | PyMuPDF >= 1.23                                      | PDF parsing and rendering                                              |
| **Image**      | Pillow >= 10.0                                       | PNG/JPG/WEBP decoding                                                  |
| **GTP Engine** | [ApolloTab](https://github.com/Zhuwenqian/ApolloTab) | Guitar Pro parsing, TAB rendering, audio playback (standalone library) |
| **Audio**      | pyfluidsynth >= 1.4.0                                | FluidSynth MIDI synthesis (via ApolloTab)                              |
| **Packaging**  | PyInstaller                                          | Python to Windows EXE / Linux DEB+ZIP / macOS APP                      |

**Architecture Patterns**: MVC, Observer (signals), Factory (Workers), Command (undo/redo), Singleton (I18n), Facade (GTPPlayer), Async (QThreadPool)

## About ApolloTab Engine

GTP features are powered by the **[ApolloTab](https://github.com/Zhuwenqian/ApolloTab)** library — a standalone Python engine for parsing, rendering, and playing Guitar Pro tablature files.

```bash
# Install standalone
pip install ApolloTab

# Use as a library
from ApolloTab import parse_gtp, render_gtp, SynthEngine
song = parse_gtp("my_song.gp5")
pages = render_gtp("my_song.gp5", track_index=0)
```

See [ApolloTab on GitHub](https://github.com/Zhuwenqian/ApolloTab) for details.

## Packaging & Distribution

Supports **Windows** (EXE), **Linux** (DEB / ZIP), and **macOS** (APP) packaging.

### Windows (EXE)

> No Python environment required.

```bash
# Build from source (requires dependencies installed first, see Option 1 steps 1-4)
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
pyinstaller "TAB Score Viewer.spec"

# Double-click TAB Score Viewer.exe to run
```

### macOS (APP Bundle)

> Native `.app` bundle with full GUI support.

**Prerequisites:**

```bash
# Install build tools (if not already installed)
xcode-select --install                    # Xcode Command Line Tools
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Preparation (required once before building):**

```bash
# Collect FluidSynth dylibs and fix @rpath dependency paths
bash prepare_macos_build.sh
```

> This script copies FluidSynth and its dependent dylibs to `_dylibs/`, then rewrites their dependency paths using `install_name_tool` so that dyld can resolve them via `@rpath` at runtime.

**Build:**

```bash
# Build with macOS-specific spec file (includes runtime_hook_macos.py)
pyinstaller "TAB Score Viewer_macOS.spec"

# The .app bundle will be generated at:
#   dist/TAB Score Viewer.app

# (Optional) Generate DMG disk image for distribution:
bash build_dmg.sh
# Output: dist/TAB Score Viewer_2.0.7.dmg
```

**Build Components:**

| File | Purpose |
|------|---------|
| `prepare_macos_build.sh` | Collects FluidSynth dylibs, fixes @rpath |
| `TAB Score Viewer_macOS.spec` | macOS-specific PyInstaller config (uses _dylibs/) |
| `runtime_hook_macos.py` | Runtime hook: sets DYLD_LIBRARY_PATH, preloads dylibs |
| `build_dmg.sh` | Packages .app into compressed DMG with /Applications shortcut |

**Run:**

```bash
# Option A: Double-click TAB Score Viewer.app in Finder
# Option B: Run from terminal
open "dist/TAB Score Viewer.app"

# If installed via DMG: open from /Applications
open "/Applications/TAB Score Viewer.app"
```

**System Dependencies (required for GTP audio playback):**

```bash
# Install FluidSynth via Homebrew
brew install fluidsynth libsndfile

# Or via MacPorts
sudo port install fluidsynth libsndfile
```

> **Note**: Qt5 (PyQt5 dependency) is bundled with the Python package, no system-wide Qt installation required. The SoundFont file (`soundfont/FluidR3_GM.sf2`) is still needed for GTP audio — see [Quick Start](#quick-start) for download instructions.

**macOS-Specific Notes:**
- The `.app` bundle includes all dependencies (Python runtime, PyQt5, libraries, locales, icons)
- `runtime_hook_macos.py` runs before the main script, setting `DYLD_LIBRARY_PATH` and preloading all dylibs with `RTLD_GLOBAL` to ensure `pyfluidsynth` can find them
- macOS Gatekeeper may block unsigned apps: go to **System Settings → Privacy & Security** and click "Open Anyway"
- For distribution, sign the app with `codesign` or notarize via Apple Developer account
- First launch may be slow due to macOS quarantine check; run `xattr -rd com.apple.quarantine "TAB Score Viewer.app"` to bypass

### Linux (DEB Package - Recommended)

> Automatic dependency resolution, system-wide installation with `tabsv` command.

```bash
# 1. Install build dependencies (if not already installed)
sudo apt-get install dpkg-dev fakeroot   # Debian/Ubuntu
# or: sudo dnf install rpm-build fakeroot  # Fedora/RHEL

# 2. Run the build script (handles PyInstaller + DEB packaging)
chmod +x build_deb.sh && ./build_deb.sh

# 3. Install the generated .deb package
sudo dpkg -i tab-score-viewer_2.0.7_*.deb
sudo apt-get install -f  # Fix any missing dependencies

# 4. Run (global command, no path needed)
tabsv
```

**DEB Package Contents:**

| Path | Description |
|------|-------------|
| `/opt/tab-score-viewer/` | Application executable + `_internal/` libs |
| `/usr/bin/tabsv` | Launcher script (auto-added to PATH) |
| `/usr/share/applications/tab-score-viewer.desktop` | Desktop shortcut (appears in app menu) |
| `/usr/share/icons/hicolor/256x256/apps/tab-score-viewer.png` | Application icon |

**System Dependencies (auto-installed by apt):**
- `libfluidsynth3` - FluidSynth audio synthesis library
- `libsndfile1` - Audio file format support
- `libpulse0` / `libasound2` - Audio output (PulseAudio / ALSA)
- `libqt5widgets5`, `libqt5gui5`, `libqt5core5a` - Qt5 GUI framework

### Linux (ZIP Archive)

> Portable, but requires manual dependency installation.

```bash
# 1. Build PyInstaller package first
pyinstaller "TAB Score Viewer_linux.spec"

# 2. Create ZIP archive
cd dist
zip -r "../tab-score-viewer-linux.zip" "TAB Score Viewer"
cd ..

# 3. Extract and run
unzip tab-score-viewer-linux.zip
cd "TAB Score Viewer"
./"TAB Score Viewer"   # Note: quote needed due to space in filename
```

**Required Dependencies (install manually):**

```bash
# Ubuntu/Debian:
sudo apt-get install libfluidsynth3 libsndfile1 libpulse0 libasound2 \
    libqt5widgets5 libqt5gui5 libqt5core5a libc6

# Fedora/RHEL:
sudo dnf install fluidsynth-libs libsndfile pulseaudio-libs alsa-lib \
    qt5-qtbase-gui qt5-qtbase qt5-qtbase

# Arch Linux:
sudo pacman -S fluidsynth libsndfile pulseaudio alsa-lib qt5-base

# Optional: SoundFont for GTP audio playback
sudo apt-get install fluid-soundfont-gm    # Ubuntu/Debian
```

### Spec Config (`TAB Score Viewer.spec` / `TAB Score Viewer_linux.spec`)

| Setting     | Value                          | Description                            |
| ----------- | ------------------------------ | --------------------------------------- |
| Mode        | onedir (directory)             | Not single-file, faster startup         |
| Icon        | icon.ico                       | exe/app + window/taskbar icon           |
| Console     | False                          | No command line window (GUI app)        |
| UPX compress| True                           | Reduce size (requires UPX installed)    |
| Data files  | locales/, DLLs, icons/, soundfont/, icon.ico | Translations/audio libs/icons/SoundFont/icon |
| Hidden imports | ApolloTab.* etc.           | Dynamically imported modules declared   |

> **Note**: macOS uses its own `TAB Score Viewer_macOS.spec` (paired with `runtime_hook_macos.py` for dylib loading), not the Windows `.spec` file. Run `bash prepare_macos_build.sh` before building to collect and fix dylibs. Linux uses `TAB Score Viewer_linux.spec` for platform-specific configuration.

## Third-Party Components

### FluidSynth

Used via ApolloTab engine for MIDI audio synthesis.

- **License**: [LGPL 2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
- **Repository**: <https://github.com/FluidSynth/fluidSynth>
- **Usage**: Precompiled DLLs in project root (`libfluidsynth-3.dll`, `SDL3.dll`, `sndfile.dll`)
- **SoundFont**: `soundfont/FluidR3_GM.sf2` (GM instrument samples, ~140MB, download required)

> FluidSynth is an open-source MIDI synthesizer based on SoundFont technology, supporting high-quality real-time audio generation.

### ApolloTab

- **License**: [LGPL 2.1](https://github.com/Zhuwenqian/ApolloTab/blob/main/LICENSE)
- **Repository**: <https://github.com/Zhuwenqian/ApolloTab>
- **Purpose**: Core GTP file parsing, tablature rendering, audio playback engine

## License

This project is licensed under [MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/).

## Author

**Zhu Wenqian** — A 14-year-old boy from China

Both TAB Score Viewer and the [ApolloTab](https://github.com/Zhuwenqian/ApolloTab) engine are developed by the same author.

### Contact

| Method   | Info                                                    |
| -------- | ------------------------------------------------------- |
| Email    | <zhuwenqianchina@outlook.com> / <3784385007@qq.com>     |
| QQ       | 3784385007                                              |
| Bilibili | [Visit Profile](https://space.bilibili.com/1299073087?) |

### AI Assistance Disclosure

The code in this project is **AI-assisted**. The author is responsible for architecture design, feature planning, code review, and integration. AI tools significantly improved development efficiency, but all core design decisions were made by a human.

---

# 中文

<p align="center">
  <img src="renderedlight (1).png" alt="TAB Score Viewer 浅色主题截图" width="45%" />
  <img src="renderedlight (2).png" alt="TAB Score Viewer 深色主题截图" width="45%" />
</p>

## 功能特性

| 功能            | 说明                                                                   |
| ------------- | -------------------------------------------------------------------- |
| **多格式支持**     | PNG、JPG、JPEG、WEBP 图片格式；PDF 文档；GP3/GP4/GP5/GPX 吉他谱文件                  |
| **GTP解析与渲染**  | 基于 ApolloTab 引擎完整解析 Guitar Pro 文件，六线谱渲染引擎（含18种技巧符号），支持音轨切换           |
| **音频播放**      | FluidSynth 合成引擎，SoundFont 音色，支持全轨并轨/单轨播放/关闭音频三种模式，推弦(Pitch Bend)渐变效果 |
| **播放光标**      | 红色竖线跟随播放进度移动，当前小节高亮显示                                                |
| **自动滚动播放**    | 30fps固定帧率平滑滚动，时间驱动模式（与音乐节奏同步，密集音符区自动加快）                              |
| **速度控制**      | 图片/PDF模式：1-500ms可调；GTP模式：由BPM自动驱动，隐藏手动控制                             |
| **速度曲线编辑器**   | 贝塞尔曲线可视化编辑，预设模板（渐快/渐慢/先慢后快等），适用于变速练习（图片/PDF模式）                       |
| **循环播放**      | 不循环 / 全局循环 / A-B 区域循环三种模式                                            |
| **文本标注系统**    | 双击谱面任意位置添加演奏技巧说明，支持颜色、字体大小、粗体等样式，悬停显示删除按钮                            |
| **标注自动导入/导出** | 自动加载同名 `.anno.json` 文件，实时保存，支持分轨/分页 PNG/**JPG**/PDF A4导出（含标注，异步导出+进度条+可取消）                |
| **标注全局撤销重做**  | Ctrl+Z 撤销 / Ctrl+Y 重做，最大50步深度                                        |
| **标注管理器**     | 独立对话框批量浏览、编辑、删除与新建标注                                                 |
| **收藏功能**      | 文件项悬停星标 / 右键菜单切换收藏，最近文件列表上方独立展示收藏列表（默认3行，展开6行，可滚动）                       |
| **难度评分**      | GTP 文件自动 0–10 星难度评分（时长、BPM、推弦/揉弦/泛音/击勾弦/滑音/震音/点弦等综合算法），自动排除鼓/钢琴/键盘/贝斯音轨，SQLite 缓存，鼠标悬停显示 tooltip |
| **快捷键自定义**    | 设置 → 快捷键 一栏以表格展示11个操作，单元格点击进入捕获模式（Esc 取消/Backspace 清空/Enter 确认），冲突检测弹「替换/清空/取消」，最多 3 键，不允许纯修饰键 |
| **点击跳转播放**    | 单击谱面任意位置自动跳转并开始播放                                                    |
| **页码导航**      | PDF / 多图片模式底部显示页码输入框，直接跳转指定页面                                        |
| **鼠标滚轮**      | 滚轮滚动谱面，Ctrl 加速 / Shift 精细控制                                          |
| **右键菜单**      | 打开文件所在位置（Windows/Linux 兼容）、添加/移除收藏                                    |
| **GTP音轨选择**   | 下拉菜单切换音轨，即时重渲染，分轨独立标注                                                |
| **深色/浅色主题**  | 现代化深色/浅色 UI，自定义组件风格 + SVG 图标(Lucide风格)，支持自定义 JSON / Python 主题         |
| **键盘快捷键**     | 空格播放/暂停、方向键调速/Ctrl+Z撤销/Ctrl+Y重做/ESC关闭                                   |
| **多语言界面**     | 支持中文(简体) / 英文 / 俄文 三语切换，翻译文件位于 locales/ 目录，设置中一键切换                     |
| **关于 / 自动更新** | 关于窗口显示版本、ApolloTab 致谢、许可证、AI 辅助声明；启动时静默调用 GitHub Releases API 检查更新（5s 超时，可取消） |
| **应用图标**      | 自定义图标(icon.ico / icon.icns)，窗口图标 + 任务栏图标统一显示                            |
| **跨平台打包**     | 支持 PyInstaller 打包：Windows EXE / Linux DEB+ZIP / macOS APP（详见[打包发布说明](#打包发布说明)） |

## 快速开始

### 方式一：从源码运行（需要 Python 环境）

#### 环境要求

- Python 3.8+
- Windows / Linux / macOS

#### 安装步骤

```bash
# 1. 克隆或下载项目
cd "e:\Projects\TAB Score Viewer"

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. 安装依赖（使用国内镜像源）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 下载 SoundFont 音色库（GTP 音频播放必需，约 140MB）
# 程序会在以下位置自动搜索音色库文件:
#   - 项目目录下的 soundfont/ 文件夹（推荐）
#   - 用户主目录 ~/.fluidsynth/
#
# 下载地址（任选其一）:
#   官方源: https://ftp.osuosl.org/pub/musespan/SoundFonts/FluidR3_GM.sf2
#   镜像源: https://github.com/FluidSynth/fluidsynth/wiki/SoundFont
#
# 下载后放到项目的 soundfont/ 目录下，目录结构如下:
#   TAB Score Viewer/
#   ├── soundfont/
#   │   └── FluidR3_GM.sf2          ← 音色库文件放这里
#   ├── TAB Score Viewer.py
#   └── ...

# 6. 运行
python "TAB Score Viewer.py"
```

### 方式二：直接运行 EXE（无需 Python 环境）

> 如果您不想安装 Python 环境，可以直接使用打包好的 EXE 程序。

```bash
# 从源码自行打包（需要先安装依赖，见方式一第1-4步）
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
pyinstaller "TAB Score Viewer.spec"

# 双击运行 TAB Score Viewer.exe
```

### 方式三：Linux DEB 安装包（推荐）

> 预打包的 `.deb` 文件，自动解决依赖关系，安装后全局可用 `tabsv` 命令。

```bash
# 安装 .deb 包（自动处理依赖）
sudo dpkg -i tab-score-viewer_2.0.7_*.deb
sudo apt-get install -f  # 自动修复缺失的依赖

# 运行（全局命令，无需输入路径）
tabsv
```

> **自行构建 DEB 包**: 详见 [打包发布说明](#打包发布说明) 中 `build_deb.sh` 的使用方法。

### 方式四：Linux ZIP 压缩包（便携版）

> 解压即用，但需要手动安装系统依赖库。

```bash
# 1. 先安装系统依赖
sudo apt-get install libfluidsynth3 libsndfile1 libpulse0 libasound2 \
    libqt5widgets5 libqt5gui5 libqt5core5a libc6

# 2. 解压并运行
unzip tab-score-viewer-linux.zip
cd "TAB Score Viewer"
./"TAB Score Viewer"
```

> **注意**: Fedora/Arch 等其他发行版的依赖安装命令请参考 [打包发布说明](#打包发布说明)。

### 方式五：macOS DMG 安装包（macOS 推荐）

> 预打包的 `.dmg` 磁盘映像，拖拽安装。DMG 包含 `.app` 应用包和 `/Applications` 快捷方式，安装方便。

```bash
# 从源码自行打包（需要先安装依赖，见方式一第1-4步）

# 1. 运行准备脚本（收集 FluidSynth 动态库并修复 @rpath 路径）
bash prepare_macos_build.sh

# 2. 安装 PyInstaller 并使用 macOS 专用 spec 打包
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
pyinstaller "TAB Score Viewer_macOS.spec"

# 3. 生成 DMG 安装镜像
bash build_dmg.sh

# 输出: dist/TAB Score Viewer_2.0.7.dmg
```

> **安装方式**：双击 `.dmg` → 将 `TAB Score Viewer.app` 拖入 `Applications` 文件夹。

### 使用方法

1. 启动程序后，点击「选择文件夹」按钮选择存放吉他谱的目录
2. 文件列表会显示所有支持的格式文件（PNG/JPG/WEBP/PDF/GP3-GP5/GPX），最近文件列表上方还有独立的「收藏」列表；悬停文件项显示星标按钮（或右键菜单切换收藏）。GTP 文件会自动显示 0–10 星难度评分（鼠标悬停查看 tooltip）。
3. 双击文件打开谱面查看器：
   - 单张图片：直接显示并播放
   - PDF：逐页渲染为图片拼接显示
   - 多张图片：按文件名排序后拼接连续显示
   - GTP 文件：通过 ApolloTab 引擎完整解析渲染为六线谱图像，支持音频播放、音轨切换、播放光标
4. 使用工具栏和控制面板进行播放、调速、标注等操作
5. 「设置 → 快捷键」可重新映射任意按键；「关于」窗口可手动检查更新。

## 快捷键

默认绑定（所有快捷键均可在「设置 → 快捷键」中重新映射）：

| 快捷键      | 功能      |
| -------- | ------- |
| `空格`     | 播放 / 暂停 |
| `↑`      | 向上翻动谱面  |
| `↓`      | 向下翻动谱面  |
| `←`      | 减慢速度    |
| `→`      | 加快速度    |
| `Ctrl+Z` | 标注撤销    |
| `Ctrl+Y` | 标注重做    |
| `ESC`    | 关闭当前窗口  |

> 捕获规则、跨平台行为与冲突处理见下方「[快捷键自定义](#快捷键自定义)」。

## 鼠标操作

| 操作              | 功能             |
| --------------- | -------------- |
| 滚轮              | 滚动谱面（默认30px/步） |
| `Ctrl + 滚轮`     | 快速滚动（100px/步）  |
| `Shift + 滚轮`    | 精细滚动（10px/步）   |
| 单击谱面            | 跳转到点击位置并开始播放   |
| 双击空白处           | 新建文本标注         |
| 双击已有标注          | 编辑该标注          |
| 进度条拖动           | 跳转播放位置         |
| `Ctrl + 点击进度条`  | 设置循环 A 点       |
| `Shift + 点击进度条` | 设置循环 B 点       |

## 快捷键自定义

打开「设置 → 快捷键」即可重新绑定任意操作。表格中左侧是操作名，右侧是当前绑定。

- **捕获模式**：点击右侧单元格进入（黄底高亮），按目标组合键即可绑定。
  - `Esc` 取消 · `Backspace` 清空（空串 = 永久禁用该操作）· `Enter` 确认当前按住的状态。
- **绑定规则**：
  - 至少包含 1 个非修饰键。
  - 修饰键（`Ctrl` / `Shift` / `Alt` / `Meta` / `CapsLock` / `Tab`）不能单独成键，必须与至少 1 个普通按键组合。
  - 组合键最多 3 个键。
- **冲突检测**：新组合已被其他操作占用时，弹窗提示「替换 / 清空 / 取消」。
- **跨平台语义**：`Option` 等价于 `Alt`；`Command` / `Win` / `Super` 统一映射为 `Meta`，存盘后跨平台保持一致。macOS 上自动交换 `Ctrl` 与 `Cmd` 的显示名，与物理按键保持一致。
- **重置所有**：一键恢复所有操作到默认绑定。
- **持久化**：自定义绑定写入 `config/settings.json` 的 `custom_shortcuts` 字段。

## 项目结构

```
TAB Score Viewer/
├── TAB Score Viewer.py      # 主程序入口（SelectionWindow / DisplayWindow）
├── constants.py             # 共享常量（路径、默认设置、键映射）
├── models.py                # 标注/设置/文件项的 dataclass
├── theme.py                 # ThemeManager（深/浅色 + 自定义 JSON/Python 主题）
├── i18n.py                  # I18n 单例（zh_CN / en_US / ru_RU）
├── fonts.py                 # UI 字体选择工具
├── config.py                # settings.json 读写与默认值
├── workers.py               # QRunnable 异步任务（文件加载、渲染等）
├── difficulty_scoring.py    # GTP 难度评分引擎 + SQLite 缓存
├── shortcuts.py             # ShortcutAction / ShortcutManager（v2.5.0，跨平台）
├── shortcuts_dialog.py      # 快捷键自定义对话框 + 捕获编辑器（v2.5.0）
├── settings_dialog.py       # 设置窗口（通用 / 主题 / 快捷键 Tab）
├── annotation_dialogs.py    # 标注创建 / 编辑 / 批量管理 对话框
├── about_dialog.py          # 关于窗口（版本、致谢、许可证、检查更新按钮）
├── update_checker.py        # 异步 GitHub Releases 更新检查（5s 超时）
├── TAB Score Viewer.spec    # PyInstaller 打包配置 - Windows 版
├── TAB Score Viewer_linux.spec  # PyInstaller 打包配置 - Linux 版
├── TAB Score Viewer_macOS.spec  # PyInstaller 打包配置 - macOS 版
├── build_deb.sh             # DEB 包自动化构建脚本（含启动脚本+桌面快捷方式）
├── build_dmg.sh             # macOS DMG 打包脚本
├── prepare_macos_build.sh   # macOS 准备脚本：收集动态库并修复 @rpath
├── runtime_hook_macos.py    # macOS 运行时钩子：预加载动态库
├── icons/                   # SVG 图标目录（Lucide 风格工具栏图标）
│   ├── annotate.svg         # 铅笔/编辑图标
│   ├── export.svg           # 下载箭头图标
│   ├── chart.svg            # 趋势线图表图标
│   ├── play.svg             # 播放三角形图标
│   ├── stop.svg             # 停止方形图标
│   ├── volume.svg           # 扬声器图标
│   ├── star.svg             # 空心星（未收藏）
│   ├── star-filled.svg      # 实心星（已收藏）
│   └── ...                  # （共15个图标）
├── icon.png                 # 应用图标源文件 (PNG, 2048x2048)
├── icon.ico                 # 应用图标 (ICO多尺寸: 16/32/48/64/128/256)
├── icon.icns                # 应用图标 (macOS 多尺寸)
├── README.md                 # 项目说明文档（本文件）
├── requirements.txt          # Python 依赖列表
├── LICENSE                   # 许可证文件 (MPL 2.0)
├── themes/                  # 自定义主题投放目录（JSON / .py）
│   └── example_custom.json
├── locales/                  # 多语言翻译文件目录
│   ├── zh_CN.json            # 简体中文翻译
│   ├── en_US.json            # 英文翻译
│   └── ru_RU.json            # 俄文翻译
├── config/
│   └── settings.json         # 用户设置（运行时自动生成；含 custom_shortcuts / favorite_files 等）
├── data/
│   ├── annotations/          # 旧版标注数据存储（JSON格式，兼容保留）
│   └── difficulty_cache.db   # GTP 难度评分 SQLite 缓存（v2.4.0）
├── libfluidsynth-3.dll       # FluidSynth 动态库 (LGPL 2.1)
├── SDL3.dll                  # SDL3 动态库 (FluidSynth 依赖)
├── sndfile.dll               # libsndfile 动态库 (FluidSynth 依赖)
├── soundfont/                # SoundFont 音色库目录（GTP音频播放必需）
│   └── FluidR3_GM.sf2       # FluidSynth GM音色库 (~140MB, 需单独下载)
├── readme/                   # 项目文档
│   ├── 功能更新.md           # 功能更新记录
│   ├── 开发文档.md           # 开发技术文档
│   └── 实施文档.md           # 实施部署文档
└── venv/                     # Python 虚拟环境（不纳入版本控制）
```

## 技术栈

| 类别          | 技术                                                   | 说明                                        |
| ----------- | ---------------------------------------------------- | ----------------------------------------- |
| **GUI框架**   | PyQt5 >= 5.15                                        | Qt for Python，窗口/控件/信号槽/绘图                |
| **PDF处理**   | PyMuPDF >= 1.23                                      | PDF 解析与页面渲染                               |
| **图片处理**    | Pillow >= 10.0                                       | PNG/JPG/WEBP 等图片格式解码                      |
| **GTP引擎**   | [ApolloTab](https://github.com/Zhuwenqian/ApolloTab) | Guitar Pro 文件解析 + 六线谱渲染 + 音频播放（独立库，可单独使用） |
| **GTP底层解析** | pyguitarpro >= 0.11                                  | Guitar Pro 原始文件解析（ApolloTab 依赖）           |
| **音频合成**    | pyfluidsynth >= 1.4.0                                | FluidSynth MIDI 合成引擎（ApolloTab 依赖）        |
| **打包工具**    | PyInstaller                                          | Python → Windows EXE 打包                   |

### 架构模式

- **MVC 分离**: SelectionWindow(视图/控制) + DisplayWidget(视图) + 数据模型(dataclass)
- **观察者模式**: PyQt5 信号槽机制实现组件间通信
- **工厂模式**: Worker 类统一封装异步任务
- **命令模式**: 撤销/重做通过快照栈实现
- **单例模式**: I18n 国际化管理器全局唯一实例
- **外观模式**: GTPPlayer 封装 ApolloTab 引擎复杂操作
- **异步处理**: QThreadPool + QRunnable 多线程加载

## 关于 ApolloTab 引擎

本项目 GTP（Guitar Pro）功能基于 **[ApolloTab](https://github.com/Zhuwenqian/ApolloTab)** 引擎构建。ApolloTab 是一个独立的 Python 库，提供：

- **文件解析**: 完整支持 GP3/GP4/GP5/GPX 格式
- **六线谱渲染**: QPainter 高质量绘制，18 种演奏技巧符号
- **音频播放**: FluidSynth MIDI 合成，推弦渐变效果
- **高度可配置**: 渲染参数全部可调（线宽/间距/颜色/字体）

```bash
# 单独安装 ApolloTab
pip install ApolloTab

# 作为独立库使用
from ApolloTab import parse_gtp, render_gtp, SynthEngine
song = parse_gtp("my_song.gp5")
pages = render_gtp("my_song.gp5", track_index=0)
```

详见 [ApolloTab GitHub](https://github.com/Zhuwenqian/ApolloTab)。

## 打包发布说明

支持 **Windows** (EXE)、**Linux** (DEB / ZIP) 和 **macOS** (APP) 三种平台的打包发布。

### Windows（EXE 安装包）

> 无需 Python 环境，直接运行。

```bash
# 从源码打包（需要先安装依赖，见方式一第1-4步）
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
pyinstaller "TAB Score Viewer.spec"

# 双击运行 TAB Score Viewer.exe
```

### macOS（APP 安装包）

> 原生 `.app` 应用包，完整 GUI 支持。

**前置条件：**

```bash
# 安装构建工具（如果尚未安装）
xcode-select --install                    # Xcode 命令行工具
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**构建：**

```bash
# 使用 macOS 专用 spec 文件打包（含 runtime_hook_macos.py）
pyinstaller "TAB Score Viewer_macOS.spec"

# 生成的 .app 包位于：
#   dist/TAB Score Viewer.app

# （可选）生成 DMG 安装镜像以便分发：
bash build_dmg.sh
# 输出: dist/TAB Score Viewer_2.0.7.dmg
```

**构建组件说明：**

| 文件 | 作用 |
|------|------|
| `prepare_macos_build.sh` | 收集 FluidSynth 动态库并修复 @rpath 依赖路径 |
| `TAB Score Viewer_macOS.spec` | macOS 专用 PyInstaller 配置（使用 _dylibs/ 目录） |
| `runtime_hook_macos.py` | 运行时钩子：设置 DYLD_LIBRARY_PATH，预加载所有 dylib |
| `build_dmg.sh` | 将 .app 打包为压缩 DMG 镜像，含 /Applications 快捷方式 |

**运行：**

```bash
# 方式 A：在 Finder 中双击 TAB Score Viewer.app
# 方式 B：从终端运行
open "dist/TAB Score Viewer.app"

# 如果通过 DMG 安装：从 /Applications 启动
open "/Applications/TAB Score Viewer.app"
```

**系统依赖（GTP 音频播放需要）：**

```bash
# 通过 Homebrew 安装 FluidSynth
brew install fluidsynth libsndfile

# 或通过 MacPorts
sudo port install fluidsynth libsndfile
```

> **注意**：Qt5（PyQt5 依赖）随 Python 包一起安装，无需系统级 Qt 安装。GTP 音频仍需 SoundFont 文件（`soundfont/FluidR3_GM.sf2`）——详见[快速开始](#快速开始)中的下载说明。

**macOS 特别说明：**
- `.app` 包包含所有依赖（Python 运行时、PyQt5、动态库、翻译文件、图标等）
- `runtime_hook_macos.py` 在主脚本之前执行，设置 `DYLD_LIBRARY_PATH` 并以 `RTLD_GLOBAL` 模式预加载所有 dylib，确保 `pyfluidsynth` 能正常加载 FluidSynth
- macOS Gatekeeper 可能阻止未签名的应用：前往 **系统设置 → 隐私与安全性**，点击「仍然打开」
- 如需分发，请使用 `codesign` 签名或通过 Apple Developer 账户公证
- 首次启动可能因 macOS 隔离检查而较慢；可运行 `xattr -rd com.apple.quarantine "TAB Score Viewer.app"` 绕过

### Linux（DEB 安装包 - 推荐）

> 自动解决依赖关系，系统级安装，全局可用 `tabsv` 命令启动。

```bash
# 1. 安装构建工具（如果尚未安装）
sudo apt-get install dpkg-dev fakeroot   # Debian/Ubuntu
# 或: sudo dnf install rpm-build fakeroot  # Fedora/RHEL

# 2. 执行构建脚本（自动完成 PyInstaller 打包 + DEB 打包）
chmod +x build_deb.sh && ./build_deb.sh

# 3. 安装生成的 .deb 包
sudo dpkg -i tab-score-viewer_2.0.7_*.deb
sudo apt-get install -f  # 自动修复缺失的依赖

# 4. 运行（全局命令，无需输入完整路径）
tabsv
```

**DEB 包安装后的目录结构：**

| 路径 | 说明 |
|------|------|
| `/opt/tab-score-viewer/` | 应用程序可执行文件 + `_internal/` 依赖库 |
| `/usr/bin/tabsv` | 启动脚本（自动添加到 PATH，可直接输入 `tabsv` 运行） |
| `/usr/share/applications/tab-score-viewer.desktop` | 桌面快捷方式（出现在应用菜单中） |
| `/usr/share/icons/hicolor/256x256/apps/tab-score-viewer.png` | 应用图标 |

**系统依赖（apt 会自动安装）：**
- `libfluidsynth3` - FluidSynth 音频合成库
- `libsndfile1` - 音频文件格式支持
- `libpulse0` / `libasound2` - 音频输出（PulseAudio / ALSA）
- `libqt5widgets5`, `libqt5gui5`, `libqt5core5a` - Qt5 图形界面框架

### Linux（ZIP 压缩包 - 便携版）

> 免安装，解压即用，但需要手动安装依赖库。

```bash
# 1. 先执行 PyInstaller 打包
pyinstaller "TAB Score Viewer_linux.spec"

# 2. 创建 ZIP 压缩包
cd dist
zip -r "../tab-score-viewer-linux.zip" "TAB Score Viewer"
cd ..

# 3. 解压并运行
unzip tab-score-viewer-linux.zip
cd "TAB Score Viewer"
./"TAB Score Viewer"   # 注意：文件名含空格，需要用引号包裹
```

**ZIP 方式需要手动安装的依赖：**

```bash
# Ubuntu/Debian:
sudo apt-get install libfluidsynth3 libsndfile1 libpulse0 libasound2 \
    libqt5widgets5 libqt5gui5 libqt5core5a libc6

# Fedora/RHEL:
sudo dnf install fluidsynth-libs libsndfile pulseaudio-libs alsa-lib \
    qt5-qtbase-gui qt5-qtbase qt5-qtbase

# Arch Linux:
sudo pacman -S fluidsynth libsndfile pulseaudio alsa-lib qt5-base

# 可选：GTP 音频播放需要的 SoundFont 音色库
sudo apt-get install fluid-soundfont-gm    # Ubuntu/Debian
```

### spec 配置说明 (`TAB Score Viewer.spec`)

| 配置项   | 值                        | 说明                  |
| ----- | ------------------------ | ------------------- |
| 模式    | onedir (目录)              | 非单文件，启动更快           |
| 图标    | icon.ico                 | exe/app 图标 + 窗口/任务栏图标 |
| 控制台   | False                    | 不显示命令行窗口（GUI应用）     |
| UPX压缩 | True                     | 减小体积（需安装UPX）        |
| 包含数据  | locales/, DLLs, icons/, soundfont/, icon.ico | 翻译/音频库/图标/音色库/图标         |
| 隐藏导入  | ApolloTab.\* 等           | 动态导入模块显式声明          |

> **注意**：macOS 使用独立的 `TAB Score Viewer_macOS.spec` 文件（配合 `runtime_hook_macos.py` 运行时钩子处理动态库加载），而非 Windows 的 spec 文件。构建前需先运行 `bash prepare_macos_build.sh` 收集并修复动态库。Linux 构建使用独立的 `TAB Score Viewer_linux.spec` 进行平台特定配置。

## 第三方组件许可证

### FluidSynth

本项目使用 [FluidSynth](https://github.com/FluidSynth/fluidSynth) 作为音频合成引擎（通过 ApolloTab 引擎调用）。

- **许可证**: [LGPL 2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
- **仓库地址**: <https://github.com/FluidSynth/fluidSynth>
- **使用方式**: 预编译的 DLL 文件位于项目根目录（`libfluidsynth-3.dll`、`SDL3.dll`、`sndfile.dll`）
- **用途**: 将 MIDI 事件合成音频输出，用于 GTP 吉他谱的音频播放功能（含推弦渐变效果）
- **SoundFont**: `soundfont/FluidR3_GM.sf2`（GM 音色样本，约140MB，需单独下载）

> FluidSynth 是一个开源的 MIDI 合成器，基于 SoundFont 技术，支持高质量的实时音频生成。

### ApolloTab

- **许可证**: [MPL 2.0](https://github.com/Zhuwenqian/ApolloTab/blob/main/LICENSE)
- **仓库地址**: <https://github.com/Zhuwenqian/ApolloTab>
- **用途**: GTP 文件解析、六线谱渲染、音频播放核心引擎

## 许可证

本项目采用 [MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/) 许可证。

## 作者

**Zhu Wenqian** — 一个14岁的中国男孩

TAB Score Viewer 与 [ApolloTab](https://github.com/Zhuwenqian/ApolloTab) 引擎均为同一作者开发。

### 联系方式

| 方式       | 信息                                                  |
| -------- | --------------------------------------------------- |
| Email    | <zhuwenqianchina@outlook.com> / <3784385007@qq.com> |
| QQ       | 3784385007                                          |
| Bilibili | [访问主页](https://space.bilibili.com/1299073087?)      |

### AI 辅助声明

本项目代码由 **AI辅助生成**，作者负责架构设计、功能规划、代码审查与整合。AI 工具大幅提升了开发效率，但所有核心设计决策均由人工完成。
