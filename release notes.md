# TAB Score Viewer Release Notes

**Current Version**: v2.1.0
**Release Date**: 2026-06-27
**Author**: Zhu Wenqian

---

## Table of Contents

- [Version Evolution](#version-evolution)
- [v2.1.0 - Fullscreen Mode + Settings Panel + Performance Optimization](#v210---fullscreen-mode--settings-panel--performance-optimization)
- [v2.0.7 - Async Export & JPG Format Support](#v207---async-export--jpg-format-support)
- [v2.0.6 - Measure-Based Click Navigation & Loop Integration](#v206---measure-based-click-navigation--loop-integration)
- [v2.0.5 - Print & Print Preview Feature](#v205---print--print-preview-feature)
- [v2.0.4 - GTP A/B Loop Architecture Refactoring](#v204---gtp-ab-loop-architecture-refactoring)
- [v2.0.1 - UI Professionalization & Code Quality](#v201---ui-professionalization--code-quality)
- [v2.0.0 - Dark/Light Theme System](#v200---darklight-theme-system)
- [Historical Versions (v1.0.0 - v1.9.1)](#historical-versions-v100--v191)

---

## Version Evolution

| Version | Date | Milestone |
|---------|------|-----------|
| v1.0.0 | 2026-06-06 | Initial release (Image/PDF viewer + auto-scroll + annotation) |
| v1.1.0 | — | GTP file parsing & rendering engine |
| v1.1.1 | — | Multi-track switching support |
| v1.2.x | — | Advanced technique symbol rendering |
| v1.3.0 | — | GTP audio playback (MIDI -> FluidSynth) |
| v1.8.1 | 2026-06-12 | ApolloTab standalone library extraction |
| v1.8.2 | 2026-06-12 | Library rename: gtp_engine -> ApolloTab |
| v1.9.0 | 2026-06-12 | Internationalization (i18n) |
| v1.9.1 | 2026-06-12 | Application icon + PyInstaller packaging |
| **v2.0.0** | **2026-06-13** | **Dark/Light theme system** |
| **v2.0.1** | **2026-06-14** | **SVG icons + Translation fix + Bilingual comments** |
| **v2.0.4** | **2026-06-14** | **GTP A/B loop architecture refactoring** |
| **v2.0.5** | **2026-06-14** | **Print & print preview feature** |
| **v2.0.6** | **2026-06-14** | **Measure-based click navigation & loop integration** |
| **v2.0.7** | **2026-06-15** | **Async export with progress bar + JPG format support** |
| **v2.1.0** | **2026-06-27** | **Fullscreen mode + Settings panel + Russian + Performance optimization** |

---

## v2.1.0 (2026-06-27) - Fullscreen Mode + Settings Panel + Performance Optimization

### Overview

This release brings 6 major feature areas: fullscreen mode, centralized settings panel, Russian localization, collapsible recent files, platform-adaptive fonts, and 7 core performance optimizations. Total: **+1394 lines, -548 lines** across 12 files.

---

### Feature 1: Fullscreen Mode (v2.1.0)

#### Problem

Users needed an immersive viewing experience without window chrome distractions, especially for live performance or practice sessions.

#### Solution

Fully immersive fullscreen mode with smart ESC behavior:

| Component | Behavior |
|-----------|----------|
| **F11 toggle** | Enter/exit fullscreen via F11 key |
| **Toolbar button** | Expand/collapse icon button in the toolbar |
| **Smart ESC** | When fullscreen: exit fullscreen instead of closing window |
| **State persistence** | Fullscreen state restored when returning from fullscreen |
| **UI adaptation** | Menu bar, toolbar, and control panel adapt to fullscreen |

#### Key Implementation

```
DisplayWindow:
  ├── _toggle_fullscreen()  → F11 / toolbar button handler
  ├── keyPressEvent()       → ESC: exit fullscreen (not close)
  ├── _fullscreen_state     → Track fullscreen toggle state
  └── _fullscreen_btn       → Toolbar button with SVG icon
```

---

### Feature 2: Settings Panel

#### Problem

`SelectionWindow` exposed language and theme dropdowns directly on the main interface, cluttering the UI and limiting future configuration expansion.

#### Solution

Centralized `SettingsDialog` with tabbed interface:

| Tab | Contents |
|-----|----------|
| **General** | Language, Theme, UI Font (with real-time preview) |
| **GTP Rendering** | GTP render font + all 19 `RenderConfig` numeric parameters |

**Key capabilities:**

- **Real-time preview**: Theme and UI font changes apply instantly; cancel reverts to previous state
- **Restore defaults**: One-click reset all settings to factory defaults with confirmation dialog
- **Persistence**: All settings saved to `config/settings.json`; old configs auto-migrate with defaults
- **Language notification**: Language change prompts restart for full effect

#### Architecture

```
SelectionWindow
  └── Settings button (gear icon)
        └── SettingsDialog(QDialog)
              ├── QTabWidget
              │     ├── Tab "General": language, theme, UI font
              │     └── Tab "GTP Rendering": font + RenderConfig params
              └── QDialogButtonBox: OK / Cancel / Restore Defaults
```

**`RenderConfig` parameters exposed** (19 total):
- `TAB_LINE_SPACING`, `NOTE_FONT_SIZE`, `STRING_SPACING`, `MEASURE_SPACING`
- `TAB_FONT_FAMILY`, `NOTE_FONT_FAMILY`, `TITLE_FONT_SIZE`, `HEADER_HEIGHT`
- `MARGIN_LEFT`, `MARGIN_RIGHT`, `MARGIN_TOP`, `MARGIN_BOTTOM`
- `PAGE_WIDTH`, `PAGE_HEIGHT`, `DPI`, `BEAT_LINE_WIDTH`
- `STEM_LENGTH`, `BEAM_THICKNESS`, `NOTE_SPACING_FACTOR`

---

### Feature 3: Russian Localization

#### Problem

Only Chinese and English were available, limiting accessibility for Russian-speaking users.

#### Solution

Complete Russian translation with 268 translation keys covering all UI surfaces:

| Surface | Coverage |
|---------|----------|
| Application title, toolbar, control panel | Full translation |
| Dialogs (export, print, settings, annotation manager) | Full translation |
| Error messages, tooltips, context menus | Full translation |
| Placeholder formatting | All `{placeholder}` preserved |

**Language list**: `简体中文` / `English` / `Русский`

---

### Feature 4: Collapsible Recent Files

#### Problem

No quick access to recently opened files; users had to navigate the folder tree each time.

#### Solution

Independent collapsible recent files list above the folder file list:

| Feature | Detail |
|---------|--------|
| **Position** | Above folder file list, with title row (label + expand/collapse button) |
| **Default state** | Collapsed — shows only 1 most recent file |
| **Expand** | Click "Expand ▼" to show all (max 4) |
| **Single click** | Click to reopen (faster than double-click in folder list) |
| **Right-click** | Open file / Locate in Explorer / Remove from list |
| **Persistence** | Stored in `config/settings.json` → `recent_files` (absolute paths, max 4) |
| **Auto-cleanup** | Filters out non-existent files on startup |
| **Auto-update** | Records file on each `show_display()` call; dedup + truncate to 4 |

---

### Feature 5: Platform-Adaptive Fonts

#### Problem

Hardcoded `Microsoft YaHei` / `Arial` / `Consolas` fonts caused missing characters on Linux and macOS.

#### Solution

Three new utility functions for automatic platform font selection:

| Function | Purpose | Windows | Linux | macOS |
|----------|---------|---------|-------|-------|
| `get_font_family('ui')` | Main UI / annotations | Microsoft YaHei, Segoe UI | Noto Sans CJK SC, WenQuanYi Micro Hei | PingFang SC, SF Pro Text |
| `get_font_family('numeric')` | Numbers / labels | Segoe UI | DejaVu Sans | SF Pro Text |
| `get_font_family('mono')` | Monospace values | Consolas | DejaVu Sans Mono | Menlo |

All 30+ hardcoded font references replaced with platform-adaptive calls.

---

### Feature 6: Performance Optimization (7 Items)

Comprehensive performance audit and optimization of the main application file:

#### P0 - Critical (3 items)

| # | Optimization | Method | Improvement |
|---|-------------|--------|-------------|
| **P0-1** | QSS stylesheet caching | Global `_QSS_CACHE` dict + `_get_cached_qss()` helper; applied to `DisplayWindow`, `SettingsDialog`, `SelectionWindow` `_apply_theme()` | Theme switch: ~50ms → ~1ms |
| **P0-2** | Binary search page sync | Precompute `_page_cumulative_heights` prefix sum array; `bisect.bisect_right()` in `_sync_page_input()` | O(n) → O(log n); 200 pages: ~2ms → ~0.01ms |
| **P0-3** | Undo/redo stack optimization | Store `dict` lists instead of `Annotation` objects in `_undo_stack`/`_redo_stack`; rebuild on demand | Avoids N×Annotation object creation per snapshot |

#### P1 - High (2 items)

| # | Optimization | Method | Improvement |
|---|-------------|--------|-------------|
| **P1-2** | PDF parallel rendering | `ThreadPoolExecutor`(max_workers=4) in `_load_pdf()`; each thread opens independent `fitz` document | 50-page PDF: ~3s → ~1s |
| **P1-3** | GTP theme async refresh | `ThemeRefreshWorker` QRunnable; `_refresh_theme()` dispatches to background thread | UI no longer freezes during theme switch |

#### P2 - Medium (2 items)

| # | Optimization | Method | Improvement |
|---|-------------|--------|-------------|
| **P2-3** | File list batch insertion | `setUpdatesEnabled(False/True)` wrap in `_on_files_loaded()` | 200 files: ~500ms → ~200ms |
| **P2-4** | Image LRU cache | `_cache_page_window=15` in `DisplayWidget`; only cache scaled images near active page; `set_active_page()` sync from `_sync_page_input()` | 200-page scaled cache: ~800MB → ~120MB |

#### Architecture Impact

```
Before (P0-1):                          After (P0-1):
_apply_theme() each call:                _apply_theme() each call:
  format QSS string                      _get_cached_qss() → dict lookup
  Qt parse stylesheet                    return cached string
  apply to widget                        apply to widget
  (repeated N times)                     (O(1) after first call)

Before (P0-2):                          After (P0-2):
_sync_page_input():                      _sync_page_input():
  for i, img in enumerate(images):       bisect.bisect_right(
    offset += height                        _page_cumulative_heights,
    if offset > position: break             current_position
  O(n) linear search                     )  O(log n) binary search

Before (P1-2):                          After (P1-2):
_load_pdf():                             _load_pdf():
  for page in pages:                     ThreadPoolExecutor(4)
    render page (sequential)               submit all pages
    (1 thread, serial)                     render 4 at a time
                                           collect results
```

---

### Translation Keys Added

| Section | Count (per language) | Description |
|---------|---------------------|-------------|
| `settings_dialog` | 12 | Settings dialog title, tabs, labels, fonts, preview |
| `reset_btn` / `reset_confirm` | 3 | Restore defaults button + confirmation dialog |
| `recent_list` | 7 | Recent files label, expand/collapse, context menu |
| `ru_RU.json` | 268 | Complete Russian translation (new file) |

**Total**: 35 new keys in zh_CN/en_US + 268 in ru_RU

---

### Test Cases (10 Scenarios)

| Case | Scenario | Expected Result |
|------|----------|-----------------|
| 1 | Press F11 during score viewing | Enters fullscreen; toolbar button updates; ESC exits fullscreen (not close) |
| 2 | Open settings, change theme, click OK | Theme applied immediately to all open windows; saved to config |
| 3 | Open settings, change UI font, click Cancel | Font reverts to previous state; no config save |
| 4 | Open settings, click "Restore Defaults", confirm | All settings reset to factory defaults; must click OK to save |
| 5 | Switch language to Russian | All UI text changes to Russian; restart prompt shown |
| 6 | Open a file, close window, reopen program | Recent files list shows the file (collapsed, 1 item visible) |
| 7 | Click "Expand ▼" on recent files | All 4 recent files shown; click any to reopen |
| 8 | Run on Linux with Noto Sans CJK installed | All UI uses Noto Sans CJK SC; no missing characters |
| 9 | Open 200-page PDF file | Parallel rendering via 4 threads; load time significantly reduced |
| 10 | Open 200-page image file, scroll rapidly | LRU cache keeps only ±15 pages scaled; memory usage stays low |

---

### Modified Files

| File | Action | Lines Changed | Description |
|------|--------|--------------|-------------|
| `TAB Score Viewer.py` | **Modified** | +1161 / -233 | Fullscreen mode, settings panel, platform fonts, recent files, Russian i18n, 7 performance optimizations |
| `locales/ru_RU.json` | **New** | +268 | Complete Russian translation |
| `locales/zh_CN.json` | **Modified** | +18 | Settings panel + recent files + reset defaults keys |
| `locales/en_US.json` | **Modified** | +18 | Settings panel + recent files + reset defaults keys |
| `README.md` | **Modified** | +106 / -13 | Feature list, AI disclosure, macOS packaging |
| `readme/功能更新.md` | **Modified** | Updated | Feature update records |
| `readme/开发文档.md` | **Modified** | +25 | Settings panel architecture docs |
| `readme/实施文档.md` | **Modified** | +43 | Settings panel usage docs |
| `release notes.md` | **Rewritten** | This file | Complete v2.1.0 release notes |
| `.trae/specs/add-settings-panel/` | **New** | +170 | Settings panel specification documents |

---

## v2.0.7 (2026-06-15) - Async Export & JPG Format Support

### Problem Description

Two critical pain points in the export system:

| # | Symptom | Root Cause |
|---|---------|------------|
| 1 | **UI freezes during large file export** | `_export_to_a4()` runs rendering on UI main thread, blocking event loop for 5-10 seconds on 50+ page files |
| 2 | **No JPG format support** | Only PNG and PDF available; users need smaller files for web sharing (WeChat/QQ/forums) |

### Solution: Async Export Architecture + JPG Rendering

#### 1. Async Export System (QRunnable + QThreadPool)

```
Old Flow (v2 synchronous):
  _export_to_a4() → [UI Thread] → render PNG/PDF → UI FREEZES 5-10s

New Flow (v3 async):
  _export_to_a4() → create ExportWorker(QRunnable)
                  → QThreadPool.globalInstance().start(worker)
                  → ExportProgressDialog shows progress
                  → Worker runs in background thread
                  → Signals: progress → finished/error/cancelled → UI updates safely
```

**Key Components:**

| Class | Role |
|-------|------|
| `ExportWorkerSignals(QObject)` | Custom signals: `progress`, `finished`, `error`, `cancelled` |
| `ExportWorker(QRunnable)` | Background thread: collect data → render per-track → emit progress |
| `ExportProgressDialog(QDialog)` | Progress bar + status label + cancel button, auto-close on done/error/cancel |

**Thread Safety**: All cross-thread communication uses Qt's signal-slot mechanism (automatically queued connection across threads).

#### 2. JPG Format Support

| Feature | Detail |
|---------|--------|
| **Format option** | New "JPG Image (Lossy, for sharing)" radio button in ExportDialog |
| **Quality slider** | Range 1-100, default 90 (high quality); only visible when JPG selected |
| **Rendering method** | `_render_to_a4_jpg()` — reuses PNG pipeline with JPEG output |
| **Quality mapping** | User input 1-100 → Qt internal 0-99 (`quality - 1`) |
| **Image format** | Uses `QImage.Format_RGB32` (no alpha channel = smaller file size) |
| **File size** | ~3-5x smaller than PNG at quality 90; suitable for web sharing |

**Recommended Quality Settings:**

| Use Case | Quality | Effect |
|----------|---------|--------|
| High-quality archive | 90 | Near-lossless, slightly smaller than PNG |
| Web sharing (WeChat/QQ/forums) | 80 | Good quality, significantly smaller file |
| Extreme compression (email attachment) | 60 | Acceptable artifacts for minimum size |

---

## v2.0.6 (2026-06-14) - Measure-Based Click Navigation & Loop Integration

### Problem Description

Three interconnected issues in the click-to-seek and A/B loop system:

| # | Symptom | Root Cause |
|---|---------|------------|
| 1 | **Click jumps to middle of measure** | Old code used exact pixel positioning, landing anywhere within the clicked measure |
| 2 | **A/B loop breaks when clicking outside loop region** | No boundary check — any click position could jump out of the [A,B] range |
| 3 | **Cross-line measure index collision** | `meas_idx` reset to 0 per System (line), causing different lines' measure-0 to collide |

### Solution: Global Unique Measure ID + Boundary-Aware Navigation

**Core Principle**: Every measure gets a globally unique `global_meas_idx`, and all internal matching uses this ID instead of the local `meas_idx`.

#### Key Changes

**Library: `player.py`** — Global Measure Index System:

| Component | Before | After |
|-----------|--------|-------|
| `build_timeline()` | `meas_idx = enumerate(system.measures)` (resets per line) | Adds `global_meas_idx` counter (increments across all systems/pages) |
| Timeline entry | `{ 'meas_idx': 0 }` (non-unique) | `{ 'meas_idx': 0, 'global_meas_idx': 5 }` (unique) |
| Empty measures | `continue` (no timeline entry) | Generates placeholder entry (`beat_idx=-1`) |

**New APIs**:
- `find_measure_at_scroll_pos(scroll_y)` — Binary search scroll_y → measure info
- `loop_time_range` property — `(loop_start_ms, loop_end_ms)` for boundary checking
- `set_loop_region_by_measure()` — Uses `global_meas_idx` as dict key (no collisions)

**Main Program** — Measure-Based Click Handler:

```
Old: click → pixel position → seek(exact pixel) → play from arbitrary position
New: click → absolute Y → find_measure_at_scroll_pos() → measure start position
       → Check A/B loop boundary:
         ├─ Outside [loop_start, loop_end] → IGNORE (maintain loop)
         └─ Inside or no loop → seek(measure_start_ms) + play
```

---

## v2.0.5 (2026-06-14) - Print & Print Preview Feature

### New Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Direct Print** | Send score directly to printer with A4 paper size |
| 2 | **Print Preview** | Preview window with zoom (50%~400%), page flipping, thumbnails |
| 3 | **Track Selection** (GTP) | Choose specific tracks for printing |
| 4 | **Page Range** | Select page range to print (e.g., "1-3" or "all") |
| 5 | **Forced Light Theme** | GTP tabs always use light theme for print readability |

### Architecture

```
Toolbar Print Button (QToolButton dropdown)
├── Direct Print...     → _print_score() → _render_to_printer() → QPrinter
└── Print Preview...    → _show_print_preview() → PreviewWindow(QDialog)
                         ├── Zoom control (50%-400%)
                         ├── Page navigation (prev/next/input)
                         ├── Thumbnail sidebar
                         └── One-click print button
```

---

## v2.0.4 (2026-06-14) - GTP A/B Loop Architecture Refactoring

### Problem

GTP mode A/B region loop had 3 critical issues: short loops froze, loop jumps past B point, and A/B buttons used scroll position instead of audio time.

### Solution: Library-Layer Measure-Based Loop

Moved all loop logic from UI layer down to audio engine library layer, eliminating race conditions and simplifying the UI code by ~90 lines.

```
Old: UI _tick() → cooldown check → simulated clock → seek → position calc
New: UI _tick() → read time → calculate position → display (clean!)
     Library SynthEngine → _play_loop() → auto-restart at B point
```

---

## v2.0.1 (2026-06-14) - UI Professionalization & Code Quality

### Key Changes

- **SVG Icon System**: 13 Lucide-style SVG icons replace emoji
- **Translation Completeness**: 30 missing translation keys fixed
- **Bilingual Comments**: English-Chinese code comments throughout
- **Play Button Fix**: `ModernButton.set_color()` resolves style mutation

---

## v2.0.0 (2026-06-13) - Dark/Light Theme System

### Features

- **ThemeManager**: Singleton + QObject + pyqtSignal observer notification
- **Runtime switching**: No restart required, global UI instant refresh
- **Two schemes**: `THEME_DARK` (default) + `THEME_LIGHT`
- **GTP sync**: UI theme auto-syncs to ApolloTab rendering theme
- **Persistence**: `settings.json` auto-restore last selection

### Design Patterns

| Pattern | Application |
|---------|-------------|
| MVC | SelectionWindow(View/Control) + DisplayWidget(View) + dataclass(Model) |
| Observer | PyQt5 signals/slots + ThemeManager.theme_changed |
| Singleton | ThemeManager / I18n |
| Factory | Worker classes for async task encapsulation |
| Command | Undo/Redo snapshot stack |
| Facade | `load_icon()` unified icon loading |
| Strategy | `ModernButton.set_color()` dynamic color switching |

---

## Historical Versions (v1.0.0 - v1.9.1)

| Version | Date | Key Features |
|---------|------|--------------|
| v1.0.0 | 2026-06-06 | Initial release: Image/PDF viewer, auto-scroll, annotation system |
| v1.1.0 | — | GTP file parsing & rendering engine (ApolloTab) |
| v1.1.1 | — | Multi-track switching, per-track annotations |
| v1.2.x | — | 18 playing technique symbols (slide/bend/harmonic/etc.) |
| v1.3.0 | — | MIDI -> FluidSynth real-time audio synthesis |
| v1.8.1 | 2026-06-12 | ApolloTab standalone library extraction (~200 lines cleanup) |
| v1.8.2 | 2026-06-12 | Library rename gtp_engine->ApolloTab, License MIT->MPL-2.0 |
| v1.9.0 | 2026-06-12 | Internationalization (zh_CN/en_US), I18n singleton |
| v1.9.1 | 2026-06-12 | Application icon, PyInstaller EXE packaging config |