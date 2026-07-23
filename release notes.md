# TAB Score Viewer Release Notes

**Current Version**: v2.5.2
**Release Date**: 2026-07-23
**Author**: Zhu Wenqian

***

## Table of Contents

- [Version Evolution](#version-evolution)
- [v2.5.2 - Mac Modifier Key Fix (4 Passes)](#v252---mac-modifier-key-fix-4-passes)
- [v2.5.1 - Mac Shortcut Recognition Fix](#v251---mac-shortcut-recognition-fix)
- [v2.5.0 - Custom Shortcuts Panel](#v250---custom-shortcuts-panel)
- [v2.4.2 - UI Polish](#v242---ui-polish)
- [v2.4.1 - Theme Switch Fix](#v241---theme-switch-fix)
- [v2.4.0 - GTP Difficulty Rating](#v240---gtp-difficulty-rating)
- [v2.3.0 - Favorites](#v230---favorites)
- [v2.2.0 - About / Update / Annotation Manager / Refactor](#v220---about--update--annotation-manager--refactor)
- [v1.1.4 - Metronome Beats Denominator + Global Gain](#v114---metronome-beats-denominator--global-gain)
- [v1.1.3 - Metronome](#v113---metronome)
- [v1.1.1 - Fix GTP Playback Muffled Sound](#v111---fix-gtp-playback-muffled-sound)
- [v2.1.0 - Fullscreen + Settings + Performance](#v210---fullscreen--settings--performance)

***

## Version Evolution

| Version    | Date           | Milestone                                                                              |
| ---------- | -------------- | -------------------------------------------------------------------------------------- |
| v1.0.0     | 2026-06-06     | Initial release (Image/PDF viewer + auto-scroll + annotation)                          |
| v1.1.0     | —              | GTP file parsing & rendering engine                                                    |
| v1.1.1     | 2026-06-28     | Fix GTP playback muffled sound (Program Change 25 for melody tracks)                   |
| v1.1.3     | 2026-06-29     | Metronome (BPM 20-300, beat numerator 1-16, GM woodblock)                              |
| v1.1.4     | 2026-06-30     | Metronome beats denominator (1-32) + global gain 1.0x-5.0x                             |
| v1.2.x     | —              | Advanced technique symbol rendering                                                    |
| v1.3.0     | —              | GTP audio playback (MIDI → FluidSynth)                                                 |
| v1.8.1     | 2026-06-12     | ApolloTab standalone library extraction                                                |
| v1.8.2     | 2026-06-12     | Library rename: gtp\_engine → ApolloTab                                                |
| v1.9.0     | 2026-06-12     | Internationalization (i18n)                                                            |
| v1.9.1     | 2026-06-12     | Application icon + PyInstaller packaging                                               |
| **v2.0.0** | **2026-06-13** | **Dark/Light theme system**                                                            |
| **v2.0.1** | **2026-06-14** | **SVG icons + Translation fix + Bilingual comments**                                   |
| **v2.0.4** | **2026-06-14** | **GTP A/B loop architecture refactoring**                                              |
| **v2.0.5** | **2026-06-14** | **Print & print preview feature**                                                      |
| **v2.0.6** | **2026-06-14** | **Measure-based click navigation & loop integration**                                  |
| **v2.0.7** | **2026-06-15** | **Async export with progress bar + JPG format support**                                |
| **v2.1.0** | **2026-06-27** | **Fullscreen mode + Settings panel + Russian + Performance optimization**              |
| **v2.2.0** | **2026-07-22** | **About dialog + Update checker + Annotation manager + Code refactor + Custom themes** |
| **v2.3.0** | **2026-07-22** | **Favorites (star + right-click)**                                                     |
| **v2.4.0** | **2026-07-22** | **GTP difficulty rating (0-10 stars + SQLite cache)**                                  |
| **v2.4.1** | **2026-07-23** | **Theme switch not applying instantly (fix)**                                          |
| **v2.4.2** | **2026-07-23** | **UI polish: list readability, window sizing, GTP mode cleanup**                       |
| **v2.5.0** | **2026-07-23** | **Custom shortcuts panel (Settings → Shortcuts)**                                      |
| **v2.5.1** | **2026-07-23** | **Mac shortcut recognition fix (MetaModifier → Cmd/Win/Super)**                        |
| **v2.5.2** | **2026-07-23** | **Mac modifier key fix (4 passes)**                                                    |

***

## v2.5.2 (2026-07-23) - Mac Modifier Key Fix (4 Passes)

### Overview

macOS Qt reports `event.modifiers()` as the global modifier state — pressing any one modifier key returns **all 4 flags** set, which poisoned the shortcut capture flow. v2.5.2 went through four rounds of fix to make single-modifier presses silent, swap Ctrl/Cmd display semantics on macOS, track held modifiers in user code, and finally bypass `event.modifiers()` entirely by recognizing modifier keys at the `keyPressEvent` entry point.

### Pass 1 — Single Modifier Press

**Problem**: Pressing Control alone on Mac popped "max 3 keys"; auto-repeat made it loop forever.

**Root cause**: Qt's `event.modifiers()` returns the global modifier state on macOS, so a single `Ctrl` press produced `Ctrl+Shift+Alt+Cmd` (4 keys) in `event_to_sequence`. Auto-repeat wasn't filtered.

**Fix**:

- Added `_MODIFIER_KEY_MAP` to `shortcuts.py`; `event_to_sequence` now returns just the pressed modifier when `event.key()` is a modifier.
- `shortcuts_dialog.py::keyPressEvent` filters `event.isAutoRepeat()`.

### Pass 2 — Mac Ctrl/Cmd Semantics Swap

**Problem**: Physical `^` (Control) showed as "Cmd"; physical `⌘` (Command) showed as "Ctrl".

**Root cause**: Qt swaps `Qt.Key_Control` and `Qt.Key_Meta` on macOS — `Key_Control` = physical ⌘, `Key_Meta` = physical ^. Display names must be reversed to match the physical key.

**Fix**:

- `_build_modifier_key_map` Mac branch swaps `Key_Control → "Cmd"`, `Key_Meta → "Ctrl"`.
- `event_to_sequence` Mac `mod_pairs` swap.
- `_MODIFIER_SORT_KEY` remains `Ctrl(0) → Shift(1) → Alt(2) → Cmd/Meta/Win/Super(3) → CapsLock(4) → Tab(5)`.
- Moved `_IS_MAC` above `_MODIFIER_SORT_KEY` declaration.

### Pass 3 — Modifier Tracking with `_held_modifiers`

**Problem**: After the first two fixes, any single modifier press on Mac immediately popped "must contain ≥1 non-modifier key" and stole focus via `QMessageBox`, leaving no chance to press a real key.

**Root cause**:

1. `keyPressEvent` immediately showed the error and `event.accept()`'d, exiting capture mode.
2. Mac's bugged `event.modifiers()` reported all 4 flags even before a real key was pressed.
3. Early return in `event_to_sequence` for modifier presses dropped the previously held modifiers.

**Fix**:

- New `_held_modifiers: Set[str]` in `ShortcutCaptureEditor`:
  - Modifier-only press → **append** to `_held_modifiers` (not replace), no error dialog, stay in capture.
  - Non-modifier press → compose sequence from `_held_modifiers` + the new key, validate.
  - Completely bypasses the macOS modifier-press bug (no reliance on `event.modifiers()`).
- New `keyReleaseEvent` removes the modifier from `_held_modifiers` when released — supports "press ⌘, release ⌘, press Z" → `"Z"`.
- New `_show_held_progress()` shows what's currently held (e.g. `"Cmd + Shift + ..."`).
- `_enter_capture_mode` / `focusOutEvent` / `cancel_capture` / `Esc` / `Backspace` / `Enter` paths all clear `_held_modifiers` to prevent state leaks.

### Pass 4 — Recognize Modifiers at `keyPressEvent` Entry

**Problem**: A few Mac configurations still triggered the "≥1 non-modifier key" error on a single modifier press.

**Root cause**:

- The fix relied on `event_to_sequence` knowing about modifiers; if PyQt5's `_L/_R` modifier key constants were missing, the lookup missed.
- The `key=0/Key_unknown` branch relied on `event.modifiers() & all_mod_flags != 0`, which is 0 on some Mac setups.

**Fix** — **promote modifier recognition to** **`keyPressEvent`** **entry, no longer depend on** **`event_to_sequence`**:

1. **Highest priority**: if `event.key() in _MODIFIER_KEY_MAP` → treat as modifier, append to `_held_modifiers`, **do not call** **`event_to_sequence`**.
2. **Compat for** **`key=0/Key_unknown`**: if `event.modifiers() & all_mod_flags != 0` → heuristic map (ControlModifier→Cmd, MetaModifier→Ctrl, AltModifier→Alt, ShiftModifier→Shift).
3. Removed dead `if not non_mods:` branch.
4. Simplified error path: `parse_sequence` failure can only be `max 3 keys` — no need to differentiate further.

**Result**: On any Mac platform/keyboard layout, a single modifier press silently enters `_held_modifiers`; no error dialog. The non-modifier key press then composes the final sequence.

### Acceptance (13 Scenarios, all passing)

| #  | Scenario              | Result                                              |
| -- | --------------------- | --------------------------------------------------- |
| 1  | Mac ⌘ (`Key_Control`) | tracked to `_held`, shows "Cmd + ..."               |
| 2  | Mac ⌘ (`Key_unknown`) | tracked to `_held`, shows "Cmd + ..."               |
| 3  | Mac ^ (`Key_Meta`)    | tracked to `_held`, shows "Ctrl + ..."              |
| 4  | Mac ⌥ (`Key_Alt`)     | tracked to `_held`, shows "Alt + ..."               |
| 5  | Mac ⇧ (`Key_Shift`)   | tracked to `_held`, shows "Shift + ..."             |
| 6  | Mac ⌘+Z               | accepts "Cmd+Z"                                     |
| 7  | Mac ⌘+⇧+Z             | accepts "Shift+Cmd+Z" (sort key)                    |
| 8  | Mac ⌘+⇧+⌥+Z           | "max 3 keys" error                                  |
| 9  | Mac ⌘ → release ⌘ → Z | "Z" (modifier removed)                              |
| 10 | Mac hold ⌃            | one error, then silent (auto-repeat filtered)       |
| 11 | Win/Linux Ctrl        | "modifier only" error after Z not pressed           |
| 12 | Win/Linux Ctrl+Z      | accepts "Ctrl+Z"                                    |
| 13 | Cross-platform sort   | Ctrl(0) → Shift(1) → Alt(2) → Cmd/Meta/Win/Super(3) |

### Modified Files

- `shortcuts.py`:
  - New `_IS_MAC`; `_MODIFIER_KEY_MAP` (with L/R key overrides); Mac branch swap; three iterations of `event_to_sequence` (early return + `Key_unknown` branch + `KeyboardModifiers` int cast).
- `shortcuts_dialog.py`:
  - `keyPressEvent` adds `_held_modifiers` tracking; modifier-only does not raise; no reliance on `event.modifiers()` bug; reordered validation.
  - New `keyReleaseEvent` for modifier release.
  - New `_show_held_progress`.
  - `_enter_capture_mode` / `focusOutEvent` / `cancel_capture` / `Esc` / `Backspace` / `Enter` paths clear `_held_modifiers`.

### Tests

- `/tmp/test_mac_modifier.py` (7 cases) — all pass
- `/tmp/test_dialog_check.py` (5 cases) — all pass
- `/tmp/test_modifier_tracking.py` (12 cases) — all pass
- `/tmp/test_e2e.py` — existing e2e tests still pass
- `/tmp/test_v252_fourth_pass.py` (9 cases) — all pass

***

## v2.5.1 (2026-07-23) - Mac Shortcut Recognition Fix

**Problem**: `event_to_sequence` hard-coded `Qt.MetaModifier` → `"Meta"`, but on macOS Meta should display as `Cmd`; on Windows as `Win`; on Linux as `Super`.

**Fix**:

- New `_detect_meta_display_name()` returns the right name based on `sys.platform` (`darwin`→`Cmd`, `win`→`Win`, linux→`Super`).
- `_MODIFIER_CANONICAL` gains Cmd→Meta; `_META_ALIASES` no longer treats `Option` as Meta (Option = Alt).
- `_qt_key_enum_name` falls back to a static `_QT_KEY_FALLBACK` map (A-Z, 0-9) for PyQt5 builds where `Qt.Key(int).name` is unavailable.

***

## v2.5.0 (2026-07-23) - Custom Shortcuts Panel

### Overview

Settings window gains a **Shortcuts** tab. All 11 hotkey actions are now user-remappable through a capture-mode table editor. Bindings persist across sessions and override the built-in defaults at the event-dispatch level.

### New Modules

- `shortcuts.py` (\~440 lines): `ShortcutAction` + singleton `ShortcutManager`. Defines the 11 actions, their default sequences, validation, and a `lookup(event) → callback` dispatch.
- `shortcuts_dialog.py` (\~700 lines): `ShortcutCaptureEditor` (yellow-highlighted cell with key-capture state machine) + `ShortcutCustomizeDialog` (table with conflict detection + reset-all).

### Rules

| Rule                     | Detail                                                                                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| Modifier-only disallowed | `Ctrl/Shift/Alt(Option)/Meta(Cmd/Win/Super)/CapsLock/Tab` alone are rejected; must be combined with ≥1 non-modifier key. |
| At least 1 non-modifier  | Required.                                                                                                                |
| Max 3 keys               | Enforced in both `parse_sequence` and the dialog's `_validate`.                                                          |
| Empty string             | Permanently disables the action.                                                                                         |

### UI Flow

- Click the right-side cell of any row to enter capture mode (yellow background, blue border).
- `Esc` cancels · `Backspace` clears (binds empty string) · `Enter` confirms the currently held combo.
- Conflict: if the new sequence is already bound to another action, the dialog prompts **Replace / Clear / Cancel**.
- **Reset All** button restores all 11 actions to their defaults.

### Cross-Platform Normalization

- `Option` → `Alt`
- `Command` / `Win` / `Super` → `Meta`
- Stored sequence is platform-portable; on Mac the Ctrl/Cmd **display names** are swapped to match the physical key (handled in v2.5.2).

### Persistence & Dispatch

- `config/settings.json` gains a `custom_shortcuts` field.
- `DisplayWindow.keyPressEvent` first calls `ShortcutManager.lookup`; on hit, it invokes the bound callback via reflection and **the default key is no longer handled**, so user bindings take precedence over built-in ones.

### Translation Keys

- `settings_dialog`: 13 new keys
- `shortcuts` node: 11 new keys
- All three locales (`zh_CN` / `en_US` / `ru_RU`)

***

## v2.4.2 (2026-07-23) - UI Polish

| Change                                       | Reason                                                                                                                                             |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Removed `opacity: 0.15` on hover             | In Qt, `opacity` applies to the whole item including the text — caused hover text to disappear. Replaced with `bg_secondary` background highlight. |
| Settings dialog height `520 → 470`           | Less empty space at the bottom.                                                                                                                    |
| Viewer window height `850 → 800`             | Smaller footprint, still fits controls.                                                                                                            |
| Hide **Shortcuts Help** group in GTP mode    | Not relevant for GTP playback.                                                                                                                     |
| GTP render settings wrapped in `QScrollArea` | 19 numeric parameters overflow on small screens.                                                                                                   |

***

## v2.4.1 (2026-07-23) - Theme Switch Fix

**Problem**: Theme changes made in Settings didn't propagate to `SelectionWindow` instantly.

**Root cause**: `settings_dialog._get_selection_window_cls` used `importlib` to re-import the class, which created a **new class object** — `isinstance` against the live `SelectionWindow` instance always returned `False`.

**Fix**:

- `_get_selection_window_cls` now prefers `sys.modules.get('__main__').SelectionWindow` for class identity consistency.
- Both `SettingsDialog` and `SelectionWindow` set `objectName` and each connects its own slot to `ThemeManager.theme_changed`.

***

## v2.4.0 (2026-07-22) - GTP Difficulty Rating

### Overview

Every GTP file in the current folder is automatically scored 0–10 stars based on length, BPM, and technique density. Scores display at the end of each file row (visible on hover) and are cached in SQLite to avoid re-parsing on every launch.

### New Module: `difficulty_scoring.py`

| Component                      | Purpose                                                         |
| ------------------------------ | --------------------------------------------------------------- |
| `DifficultyResult` (dataclass) | `score: float`, `stars: int`, `factors: dict`                   |
| `compute_difficulty(path)`     | Pure parser, returns `DifficultyResult`                         |
| `lookup_difficulty(path)`      | Cache lookup; re-runs and stores if mtime changed or cache miss |
| `data/difficulty_cache.db`     | SQLite cache, keyed by absolute path + mtime                    |

### Scoring Factors

| Factor                       | Weight     | Direction             |
| ---------------------------- | ---------- | --------------------- |
| Song length (measures × BPM) | base       | longer → harder       |
| BPM                          | multiplier | faster → harder       |
| Bends (推弦)                   | +0.4 each  | harder                |
| Harmonics (泛音)               | +0.3 each  | harder                |
| Tapping (点弦)                 | +0.5 each  | harder                |
| Vibrato (揉弦)                 | +0.2 each  | harder                |
| Hammer-ons / Pull-offs (击勾弦) | +0.1 each  | easier (compensation) |
| Slides (滑音)                  | +0.15 each | harder                |

### Track Filtering

Drum, piano, keyboard, and bass tracks are **excluded** automatically; the score is the average across the remaining tracks.

### Background Loading

- `LoadDifficultyWorker` (QRunnable) parses one file at a time off the UI thread.
- `LoadDifficultyWorkerSignals` emits per-file `one_done(path, result)` and final `all_done()`.
- `SelectionWindow._on_files_loaded` triggers the worker pool.
- `_apply_difficulty_to_item` updates the QListWidgetItem with a `⭐ 7.5/10` suffix and a tooltip listing the contributing factors.
- Errors (e.g. the known ApolloTab GP7 `BendData.bend_style` mismatch) are cached as `NULL` and retried on the next launch.

### UI

- File list shows `⭐ 7.5/10` at the end of each row (after the file name).
- Hover tooltip: `"难度: 7.5/10 ⭐⭐⭐⭐⭐⭐⭐☆☆\n时长: 124 拍\nBPM: 140\n推弦 ×12  揉弦 ×8  ..."` style breakdown.

### Translation

8 new keys per locale (label, factors, error states).

### Tests

Verified against 5 test files:

| File                 | Expected behavior                            | Result                  |
| -------------------- | -------------------------------------------- | ----------------------- |
| `notes.gp`           | low score, mostly easy techniques            | ✓                       |
| `harmonics.gp`       | high score, many harmonics                   | ✓                       |
| `hammer.gp`          | medium-low score (H/P are "easier")          | ✓                       |
| `compressed.gp`      | medium score                                 | ✓                       |
| `multi-track-all.gp` | filtered (drum/bass excluded)                | ✓                       |
| `bends.gp`           | parser error → NULL cached, retried next run | ✓ (known ApolloTab bug) |

***

## v2.3.0 (2026-07-22) - Favorites

### Overview

Quick-access list above the recent files for files the user wants to keep at their fingertips. Toggle via hover star button or right-click menu; persists across sessions.

### Behavior

| Feature              | Detail                                                                              |
| -------------------- | ----------------------------------------------------------------------------------- |
| List position        | Above the recent files list, with its own title row                                 |
| Default state        | 3 items visible                                                                     |
| Expanded state       | Up to 6 items + scrollbar                                                           |
| Toggle — hover       | Hover any file row → star button appears on the right (hollow star = not favorited) |
| Toggle — right-click | Right-click any file → "Add to favorites" / "Remove from favorites"                 |
| Icon — favorited     | Filled star (`icons/star-filled.svg`)                                               |
| Icon — not favorited | Hollow star (`icons/star.svg`)                                                      |
| Max entries          | 100 (oldest evicted)                                                                |
| Persistence          | `config/settings.json::favorite_files` (absolute paths)                             |
| Cross-list sync      | Toggling in one list reflects in the other immediately                              |

### New Icons

- `icons/star.svg` — hollow star
- `icons/star-filled.svg` — filled star

### Modified Files

- `TAB Score Viewer.py` — 9 new methods + list UI changes
- `locales/{zh_CN,en_US,ru_RU}.json` — context-menu labels, favorite-list title

***

## v2.2.0 (2026-07-22) - About / Update / Annotation Manager / Refactor

### New Modules

| File                                                  | Purpose                                                                                                                        |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `update_checker.py`                                   | Async GitHub Releases check (`QRunnable` + 5s timeout), silent on launch, manual from About window                             |
| `about_dialog.py`                                     | Version / ApolloTab credit / license / author / AI disclosure + "Check for Updates" button                                     |
| `annotation_dialogs.py`                               | `AnnotationCreateDialog` / `AnnotationEditDialog` / `AnnotationManagerDialog` (unified theme color source from `ThemeManager`) |
| `theme.py`                                            | New `get_app_icon` / `load_icon` (PyInstaller `_internal/` compat) + `_get_cached_qss`                                         |
| `constants.py` / `models.py` / `i18n.py` / `fonts.py` | **Refactor** — extracted from `TAB Score Viewer.py` to flat modules alongside the main file (per project convention)           |

### Code Structure Refactor

`TAB Score Viewer.py` was split into flat modules (no subpackages), per the project rule "all extracted modules must sit alongside the main file, not in `tab_score_viewer/` subdirectory". The previous `tab_score_viewer/` subpackage was removed. `_APP_BASE_DIR` fixed to `os.path.dirname(os.path.abspath(__file__))`.

### Custom Theme Loader

- `themes/` directory scanned on launch; `.json` and `.py` themes auto-registered.
- UI + GTP render colors switch together.
- Missing color keys fall back to dark theme defaults.
- Built-in `dark` / `light` are protected from being overridden.
- `SettingsDialog` theme dropdown auto-includes custom themes.
- `ThemeConfig.register_theme` / `unregister_theme` exposed.

### Modified Files

- `TAB Score Viewer.py` — slimmed by \~400 lines
- 4 new flat modules + 1 refactor of `theme.py`
- `locales/{zh_CN,en_US,ru_RU}.json` — about / update / annotation manager keys
- `config.py` — new `favorite_files` / `custom_shortcuts` / `recent_files` keys (defaults)

***

## v2.1.0.3 (2026-06-30) - Metronome Beats Denominator + Global Gain

| Change           | Detail                                                                          |
| ---------------- | ------------------------------------------------------------------------------- |
| Beat denominator | Time signature now displays as a fraction — denominator 1-32 (was hard-coded 4) |
| Global gain      | New slider 1.0×-5.0× (default 1.5×) affects both metronome and player           |
| Accent dynamics  | Strong beat velocity 100, weak beat 70 (GM percussion)                          |
| GTP mode gain    | Gain slider stays visible in GTP mode                                           |

***

## v2.1.0.2 (2026-06-29) - Metronome

### Overview

Click track synchronized to the song's BPM and time signature, available in both GTP and image/PDF modes.

### Behavior

| Mode        | BPM                  | Time signature             | Source            |
| ----------- | -------------------- | -------------------------- | ----------------- |
| GTP         | follows song         | follows song               | parsed from track |
| Image / PDF | 20-300 (default 120) | numerator 1-16 (default 4) | manual            |

### Implementation

- GM woodblock sounds: strong beat = program 77, weak beat = program 76
- Exclusive MIDI channel 15 (no conflict with melody tracks)
- `ApolloTab/metronome.py` — new module

***

## v2.1.0.1 (2026-06-28) - Fix GTP Playback Muffled Sound

**Problem**: Melody tracks sounded muffled because the player was overriding the track's `instrument==0` (default) with `Program Change 27` (clean electric guitar).

**Fix**:

- New `DEFAULT_MELODY_INSTRUMENT = 25` (steel-string acoustic guitar).
- When `track.instrument == 0`, the player sends `Program Change 25`.
- Removed the unconditional `set_instrument(ch, 27)` in `player.py`.

***

## v2.1.0 (2026-06-27) - Fullscreen + Settings + Performance

### Overview

Six major feature areas: fullscreen mode, centralized settings panel, Russian localization, collapsible recent files, platform-adaptive fonts, and 7 core performance optimizations. **+1394 lines / -548 lines** across 12 files.

### 1. Fullscreen Mode

- `F11` toggle · toolbar button · smart `ESC` (exits fullscreen instead of closing window) · state restored when leaving fullscreen · menu/toolbar/panel adapt.

### 2. Settings Panel

Tabbed `SettingsDialog`:

- **General** — language, theme, UI font (real-time preview, cancel reverts)
- **GTP Rendering** — 19 `RenderConfig` numeric parameters
- **Restore defaults** with confirmation
- Persistence in `config/settings.json` with auto-migration

### 3. Russian Localization

`locales/ru_RU.json` with 268 keys covering all UI surfaces, dialogs, error messages, tooltips, context menus, and placeholders.

### 4. Collapsible Recent Files

- Above the folder file list, default 1 item, expand to 4
- Single-click to reopen · right-click: Open / Locate / Remove
- `config/settings.json::recent_files` (absolute paths, max 4, deduped)

### 5. Platform-Adaptive Fonts

Three helpers (`get_font_family('ui' / 'numeric' / 'mono')`) replace 30+ hardcoded font references:

| Helper    | Windows                   | Linux                                 | macOS                    |
| --------- | ------------------------- | ------------------------------------- | ------------------------ |
| `ui`      | Microsoft YaHei, Segoe UI | Noto Sans CJK SC, WenQuanYi Micro Hei | PingFang SC, SF Pro Text |
| `numeric` | Segoe UI                  | DejaVu Sans                           | SF Pro Text              |
| `mono`    | Consolas                  | DejaVu Sans Mono                      | Menlo                    |

### 6. Performance Optimization (7 Items)

#### P0 - Critical

| #    | Optimization            | Method                                             | Improvement                                 |
| ---- | ----------------------- | -------------------------------------------------- | ------------------------------------------- |
| P0-1 | QSS stylesheet caching  | `_QSS_CACHE` + `_get_cached_qss()`                 | Theme switch \~50ms → \~1ms                 |
| P0-2 | Binary search page sync | `_page_cumulative_heights` + `bisect.bisect_right` | O(n) → O(log n); 200 pages \~2ms → \~0.01ms |
| P0-3 | Undo/redo stack         | store `dict` lists, rebuild `Annotation` on demand | Avoids N×Annotation per snapshot            |

#### P1 - High

| #    | Optimization            | Method                              | Improvement                  |
| ---- | ----------------------- | ----------------------------------- | ---------------------------- |
| P1-2 | PDF parallel rendering  | `ThreadPoolExecutor(max_workers=4)` | 50-page PDF \~3s → \~1s      |
| P1-3 | GTP theme async refresh | `ThemeRefreshWorker` QRunnable      | No UI freeze on theme switch |

#### P2 - Medium

| #    | Optimization              | Method                          | Improvement                             |
| ---- | ------------------------- | ------------------------------- | --------------------------------------- |
| P2-3 | File list batch insertion | `setUpdatesEnabled(False/True)` | 200 files \~500ms → \~200ms             |
| P2-4 | Image LRU cache           | `_cache_page_window=15`         | 200-page scaled cache \~800MB → \~120MB |

### Modified Files (v2.1.0)

| File                              | Action    | Lines        | Description                                              |
| --------------------------------- | --------- | ------------ | -------------------------------------------------------- |
| `TAB Score Viewer.py`             | Modified  | +1161 / -233 | Fullscreen, settings, fonts, recent files, Russian, perf |
| `locales/ru_RU.json`              | New       | +268         | Russian                                                  |
| `locales/{zh_CN,en_US}.json`      | Modified  | +18 each     | Settings / recent files / reset                          |
| `README.md`                       | Modified  | +106 / -13   | Features, AI disclosure, macOS packaging                 |
| `readme/功能更新.md`                  | Modified  | —            | Changelog                                                |
| `readme/开发文档.md`                  | Modified  | +25          | Settings panel architecture                              |
| `readme/实施文档.md`                  | Modified  | +43          | Settings panel usage                                     |
| `release notes.md`                | Rewritten | —            | This file                                                |
| `.trae/specs/add-settings-panel/` | New       | +170         | Spec / tasks / checklist                                 |

***

## License

MPL 2.0 — see [LICENSE](LICENSE).

## Author

**Zhu Wenqian** — A 14-year-old developer from China. Both TAB Score Viewer and the [ApolloTab](https://github.com/Zhuwenqian/ApolloTab) engine are written by the same author.

### Contact

| Method   | Info                                                   |
| -------- | ------------------------------------------------------ |
| Email    | <zhuwenqianchina@outlook.com> / <3784385007@qq.com>    |
| QQ       | 3784385007                                             |
| Bilibili | [Visit Profile](https://space.bilibili.com/1299073087) |

### AI Assistance Disclosure

The code in this project is **AI-assisted**. The author is responsible for architecture design, feature planning, code review, and integration. AI tools significantly improved development efficiency, but all core design decisions were made by a human.
