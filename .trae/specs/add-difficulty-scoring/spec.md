# 难度评分功能 (Difficulty Scoring) Spec

## Why
当前 `SelectionWindow` 展示的文件列表仅显示文件名，无法让用户在打开前快速判断某首曲目的演奏难度（影响曲目选择、练习优先级排序）。通过静默解析 GTP 文件中的音轨音符与技巧标记，输出 0-10 星的难度评分（写入 SQLite 缓存），并在文件名右侧显示，鼠标悬停展示评分明细（BPM / 时长 / 各技巧计数），帮助用户快速评估曲目难度。

> **重要**：本功能只针对**吉他类音轨**（含电吉他/木吉他/贝斯以外的低音乐器视情况）。鼓组、钢琴、键盘、贝斯均**不计入**评分，因为这些乐器的演奏技巧与吉他难度体系不可比。

## What Changes
- 新增 **难度评分模块** `difficulty_scoring.py`，导出两个核心函数：
  - `compute_difficulty(gtp_path) -> DifficultyResult` — 解析单文件，返回结构化结果（含缓存写入）
  - `lookup_difficulty(gtp_path) -> Optional[DifficultyResult]` — 仅查缓存，不解析
- 新增 **SQLite 缓存** `data/difficulty_cache.db`，表结构 `difficulty_cache(path PRIMARY KEY, mtime INTEGER, score REAL, factors_json TEXT, computed_at INTEGER)`。
- 新增 **Worker 线程** `LoadDifficultyWorker(QRunnable)`：在文件列表加载完成后，**后台**遍历当前目录所有 **GTP 类文件**（后缀为 `.gp` / `.gp3` / `.gp4` / `.gp5` / `.gp6` / `.gpx` / `.gtp` / `.gp7` / `.gp8` 等以 `gp` 开头的扩展名），静默解析，不阻塞 UI，逐个写入数据库后通过信号回写主线程的 file_list 项。
- 修改 `SelectionWindow`：
  - `_on_files_loaded` 完成后，启动 `LoadDifficultyWorker` 异步计算（仅匹配 `gp*` 后缀的文件）。
  - 每条 GTP 文件项的文本从 `name` 改为 `name  ★ N/10`（5 颗星及以上用实心 ★，低于 5 颗用空心 ☆）。
  - 鼠标悬停时通过 `setToolTip` 显示明细：包含 BPM、总时长、轨道数、各技巧计数（Bend/Harmonic/Vibrato/Tap/Hammer/Pull/Slide/Trill/Whammy/Tremolo）、最终评分与公式因子。
- 新增 **三语翻译键**（位于 `settings_window` 节点）：
  - `difficulty_label` / `difficulty_tooltip` / `difficulty_calculating`
- 关键交互：
  - 难度评分 **不影响** 打开/收藏/右键菜单等现有功能
  - 数据库读取异常 → 静默忽略（不影响列表显示）
  - 文件 mtime 变化 → 重新计算（缓存键含 mtime）
  - 解析失败 → 缓存 `score = NULL`，不显示星号
  - **鼓 / 钢 / 键盘 / 贝斯**等非吉他音轨不计入评分（仅评吉他家族）

## Impact
- Affected specs: 无（新功能）
- Affected code:
  - `difficulty_scoring.py` - **新增**
  - `data/difficulty_cache.db` - **新增**（首次运行时自动创建）
  - `TAB Score Viewer.py` - 新增 `LoadDifficultyWorker`、修改 `_on_files_loaded` 启动后台评分、修改行文本渲染
  - `locales/zh_CN.json` / `en_US.json` / `ru_RU.json` - 各 +3 键
  - `readme/功能更新.md` - 追加更新记录
- 不影响：收藏、节拍器、最近文件、播放、导出、主题、设置面板

## ADDED Requirements

### Requirement: 难度计算函数
The system SHALL provide a pure function `compute_difficulty(gtp_path)` that parses a GTP file and returns a structured `DifficultyResult` dataclass.

#### Scenario: 解析成功
- **WHEN** 调用 `compute_difficulty(valid_gtp_path)`
- **THEN** 返回包含以下字段的 `DifficultyResult`：
  - `score: float` — 最终 0-10 评分（保留 1 位小数）
  - `bpm: int` — 主 BPM
  - `duration_sec: float` — 总时长（秒）
  - `track_count: int` — 有效（非鼓/钢/键盘）音轨数
  - `techniques: dict[str, int]` — 各类技巧计数（见下）
  - `factors: dict[str, float]` — 评分因子（见下）
  - `error: Optional[str]` — 解析失败原因（成功时为 None）

#### Scenario: 解析失败
- **WHEN** 调用 `compute_difficulty(corrupted_or_unsupported_path)`
- **THEN** 返回 `DifficultyResult(score=0, error="<reason>")` 且不抛异常
- **AND** 缓存记录写入 `score = NULL`（表示已知但失败）

### Requirement: SQLite 缓存机制
The system SHALL cache difficulty scores in a SQLite database for fast subsequent lookups.

#### Scenario: 数据库位置与初始化
- **WHEN** 首次调用 `compute_difficulty` 或 `lookup_difficulty`
- **THEN** 自动创建 `data/difficulty_cache.db`（目录不存在则一并创建）
- **AND** 创建表 `difficulty_cache`：
  ```sql
  CREATE TABLE IF NOT EXISTS difficulty_cache (
      path TEXT PRIMARY KEY,
      mtime INTEGER NOT NULL,
      score REAL,
      factors_json TEXT NOT NULL,
      computed_at INTEGER NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_dc_mtime ON difficulty_cache(mtime);
  ```

#### Scenario: 缓存命中（mtime 未变）
- **WHEN** `lookup_difficulty(path)` 命中数据库
- **AND** 数据库中 mtime 与文件当前 mtime 一致
- **THEN** 直接返回缓存结果，不重新解析
- **AND** 耗时 < 5ms

#### Scenario: 缓存失效（mtime 变化）
- **WHEN** 文件 mtime 与数据库中记录不一致
- **THEN** 触发重新计算并更新缓存

#### Scenario: 缓存写入失败
- **WHEN** SQLite 写入异常（磁盘满、权限错误等）
- **THEN** 静默忽略，不影响主程序功能
- **AND** 下次调用仍按"未命中"逻辑重新计算

### Requirement: 评分公式
The system SHALL compute the difficulty score using a weighted multi-factor formula.

#### Scenario: 公式定义
最终评分（0-10）= `min(10, max(0, base + tech_bonus + bpm_bonus + dur_bonus))`

| 因子 | 计算方式 | 权重 |
|------|----------|------|
| **base** | 固定 2.0 | 基础分（确保空谱也有分） |
| **tech_bonus** | `sum(tech_count × weight) / (track_count + 1)` | 技术密度（每轨道平均） |
| **bpm_bonus** | `min(2.0, bpm / 80)` | BPM 因子（< 80 BPM 不加分） |
| **dur_bonus** | `min(1.5, duration_sec / 600)` | 时长因子（10 分钟满分） |

技术权重表（每出现一次）：

| 技巧 | 权重 | 难度级别 |
|------|------|----------|
| Bend（推弦） | 1.5 | 较难 |
| Harmonic（泛音，含自然/人工/品丝/颤音泛音） | 1.5 | 较难 |
| Tapping（点弦，含左/右手 tap） | 2.0 | 较难 |
| Vibrato（颤音，含 Slight/Wide） | 0.8 | 较难 |
| Whammy Bar（摇杆/颤音臂） | 1.5 | 较难 |
| Trill（击弦颤音） | 1.2 | 较难 |
| Tremolo Picking（震音拨弦） | 1.5 | 较难 |
| Slide（滑弦，in/out 任一存在） | 0.4 | 较易 |
| Hammer（击弦） | 0.4 | 较易 |
| Pull（勾弦） | 0.4 | 较易 |

> **设计要点**：技术按"较难 / 较易"两类加权，bends / harmonics / tapping 单独拉高权重，Hammer/Pull/Slide 权重较低。bpm_bonus 用 80 BPM 起步，dur_bonus 10 分钟封顶，保证分数不会无界增长。

#### Scenario: 评分边界
- **WHEN** 一首空谱（无任何技术）BPM=120, duration=120s
- **THEN** `score = base(2.0) + tech(0) + bpm(1.5) + dur(0.2) = 3.7` → `★ 3.7/10`
- **WHEN** 一首高难度曲子（BPM=200, duration=480s, 大量 bend + harmonic + tap）
- **THEN** `score` 趋近 10 但不超过 10

### Requirement: 音轨过滤
The system SHALL exclude drum, piano, keyboard, and bass tracks from difficulty calculation.

#### Scenario: 排除规则
- **WHEN** 遍历 `song.tracks`
- **THEN** 跳过满足以下**任一**条件的音轨：
  1. `track.playbackInfo.program` 属于 `0-7`（Piano 类）→ 跳过
  2. `track.playbackInfo.program` 属于 `8-15`（Chromatic Percussion）→ 跳过
  3. `track.playbackInfo.program` 属于 `16-23`（Organ）→ 跳过
  4. `track.playbackInfo.program` 属于 `32-39`（Bass 类，含 Electric Bass / Synth Bass / Acoustic Bass 等）→ 跳过
  5. track 名称正则匹配 `(?i)(drum|percussion|kit|skins|bass|fretless|upright|stand\s*up)` → 跳过
  6. track 名称正则匹配 `(?i)(piano|keyboard|keys|organ|glockenspiel|marimba|celesta|celeste|synth|pad|strings|brass|reed|pipe|choir|voice|vocal)` → 跳过
- **AND** 任一音轨的 MIDI Channel 标记 `isPercussion == True` → 跳过该音轨
- **AND** 取所有剩余音轨的评分算术平均
- **AND** 若所有音轨都被过滤（无吉他家族音轨），`track_count = 0` 并 `score = 0`，**不显示星号**
- **AND** 仅保留 **吉他家族**音轨（含 MIDI program 24-31 Electric/Acoustic Guitar 及其他弦乐器如 Banjo/Mandolin/Sitar/Ukelele 等可在吉他谱中合理出现且演奏难度可比的乐器）

#### Scenario: Bass 排除
- **WHEN** `track.playbackInfo.program == 33`（Electric Bass Fingered）**或** track 名称含 "Bass"
- **THEN** **跳过**该音轨（不计入评分）
- **AND** 即使有 2 轨吉他和 1 轨贝斯，仅按 2 轨吉他平均

#### Scenario: Drum 排除
- **WHEN** `track.playbackInfo.channel.isPercussion == True`（GM 标准通道 10）
- **OR** track 名称含 "Drum"/"Percussion"/"Kit"
- **THEN** **跳过**该音轨

#### Scenario: 吉他家族保留
- **WHEN** track 名称含 "Guitar" / "Acoustic" / "Electric" / "Banjo" / "Mandolin" / "Sitar" / "Ukelele" 等
- **OR** `track.playbackInfo.program` 属于 `24-31`（Guitar 类）
- **THEN** 包含在评分中

### Requirement: 技巧检测方法
The system SHALL detect each technique by inspecting `alphaTab.model.Note` properties.

#### Scenario: Note 属性映射表
| 技巧 | alphaTab 字段 | 判定条件 |
|------|----------------|----------|
| Bend | `note.bends` | `len(note.bends) > 0` |
| Harmonic | `note.harmonicType` | `note.harmonicType != HarmonicType.None` |
| Tapping | `note.isLeftHandTapped == True` 或 `note.isRightHandTapped == True` | 任一为 True |
| Vibrato | `note.vibrato != VibratoType.None` | 包含 Slight/Wide |
| Whammy Bar | `note.whammyBar != WhammyBarType.None` | 包含 Dive/hold/release |
| Trill | `note.trillValue != -1` | 有效颤音音程 |
| Tremolo Picking | `note.tremoloPicking != TremoloPickingType.None` | 含 1/2/1/4/1/8 |
| Slide | `note.slideInType != SlideInType.None` 或 `note.slideOutType != SlideOutType.None` | 任一存在 |
| Hammer | `note.hammerOnOrigin != NoteOrigin.None` | 左手指法 = hammer |
| Pull | `note.pullOffOrigin != NoteOrigin.None` | 左手指法 = pull |

### Requirement: 后台评分 Worker
The system SHALL compute difficulty scores in a background thread to keep UI responsive.

#### Scenario: 触发时机
- **WHEN** `_on_files_loaded(result)` 完成
- **AND** `result` 中包含至少 1 个 GTP 文件
- **THEN** 启动 `LoadDifficultyWorker(folder, file_list)` 异步任务
- **AND** Worker 遍历 `folder` 下所有 `.gp*` 文件，调用 `compute_difficulty`
- **AND** 每完成一个文件，发射 `one_done(path, result)` 信号

#### Scenario: 静默性
- **WHEN** Worker 正在解析
- **THEN** 不显示任何进度条/弹窗/状态栏文字
- **AND** 异常文件不报错（仅缓存 NULL score）
- **AND** 解析过程中用户切换目录 → Worker 提前结束循环

#### Scenario: 回写 UI
- **WHEN** `one_done(path, result)` 信号被发射
- **THEN** 主线程在 `file_list` 中查找匹配 path 的 `QListWidgetItem`
- **AND** 追加 `  ★ N/10`（或 `  ☆ N/10` 当 N < 5）到 item 文本
- **AND** 调用 `setToolTip(<详细明细>)`

### Requirement: 行文本与 Tooltip
The system SHALL display difficulty visually in the file list and provide rich tooltips on hover.

#### Scenario: 行文本格式
- **WHEN** 文件评分 = 6.2
- **THEN** item 文本 = `<filename>  ★ 6.2/10`
- **WHEN** 文件评分 = 3.0（< 5 阈值）
- **THEN** item 文本 = `<filename>  ☆ 3.0/10`
- **WHEN** 解析失败 / 缓存 score = NULL
- **THEN** item 文本 = `<filename>`（不追加星号）
- **WHEN** 文件不是 GTP 后缀
- **THEN** item 文本不变（不显示评分）

#### Scenario: Tooltip 内容
- **WHEN** 鼠标悬停在带星号的 item 上
- **THEN** tooltip 显示多行文本（中/英/俄翻译）：

  ```
  难度评分: ★ 6.2/10
  ───────────────
  有效音轨: 2
  BPM: 128
  时长: 4:23
  ───────────────
  技术统计:
  • Bend (推弦): 12
  • Harmonic (泛音): 5
  • Tapping (点弦): 0
  • Vibrato (颤音): 8
  • Whammy (摇杆): 3
  • Trill (击弦颤音): 0
  • Tremolo (震音): 2
  • Slide (滑弦): 18
  • Hammer (击弦): 24
  • Pull (勾弦): 20
  ───────────────
  评分因子:
  base=2.0 tech=+1.8 bpm=+1.6 dur=+0.4
  ```

### Requirement: 国际化
The system SHALL provide trilingual support (zh_CN / en_US / ru_RU) for new UI strings.

#### Scenario: 必填键
- `difficulty_label` - 难度评分: / Difficulty: / Сложность:
- `difficulty_tooltip_title` - 评分明细 / Score Breakdown / Детали оценки
- `difficulty_calculating` - 计算中... / Calculating... / Расчёт...

## MODIFIED Requirements

### Requirement: SelectionWindow._on_files_loaded
在 `self.file_list.setUpdatesEnabled(True)` 之后追加：
```python
# 异步难度评分（GTP 文件）
if self.current_directory:
    self._start_difficulty_scoring(self.current_directory)
```

### Requirement: SelectionWindow.__init__
新增属性：
```python
self._difficulty_worker = None  # 当前 Worker 引用（用于停止）
self._difficulty_results: Dict[str, DifficultyResult] = {}  # 缓存结果
```

### Requirement: SelectionWindow (新增方法)
- `_start_difficulty_scoring(folder: str)` - 启动 LoadDifficultyWorker
- `_on_difficulty_one_done(path: str, result: DifficultyResult)` - 处理单个文件结果
- `_on_difficulty_all_done()` - Worker 完成（可清理引用）
- `_apply_difficulty_to_item(item, result)` - 更新行文本与 tooltip

## REMOVED Requirements
None (pure additive)

## Technical Implementation Details

### difficulty_scoring.py 模块结构

```python
# difficulty_scoring.py
"""
TAB Score Viewer - Difficulty Scoring Module
难度评分模块 - 解析 GTP 文件并生成 0-10 评分
"""
from __future__ import annotations
import json
import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, List

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal

# alphaTab 模型导入
from alphaTab.model import (
    Note, Track, Score, Song,
    VibratoType, WhammyBarType, HarmonicType, TremoloPickingType,
    SlideInType, SlideOutType, NoteOrigin,
)

# ============== DataClass ==============

@dataclass
class DifficultyResult:
    score: float                    # 0-10
    bpm: int
    duration_sec: float
    track_count: int
    techniques: Dict[str, int]
    factors: Dict[str, float]
    error: Optional[str] = None
    cached: bool = False

# ============== Constants ==============

CACHE_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data', 'difficulty_cache.db'
)

# 排除的 MIDI program 范围（GM 标准）
#   0-7   Piano (Grand/Brilliant/Electric/Clavinet 等)
#   8-15  Chromatic Percussion (Celesta/Marimba/Glockenspiel 等)
#   16-23 Organ (Hammond/Church/Reed 等)
#   24-31 Guitar (Acoustic/Electric/Jazz/Overdriven/Distortion/Harmonics/Clean/Muted) — 保留
#   32-39 Bass (Electric/Synth/Acoustic/Fretless/Slap/Pop) — 排除
#   40-79 含 Orchestral/Strings/Brass/Reed/Pipe/Lead/Pad 等合成/管弦 — 排除
EXCLUDED_PROGRAMS = set(range(0, 24)) | set(range(32, 80))
EXCLUDED_TRACK_NAME_RE = r'(?i)(drum|percussion|kit|skins|bass|fretless|upright|stand\s*up|piano|keyboard|keys|organ|glockenspiel|marimba|celesta|celeste|synth|pad|strings|brass|reed|pipe|choir|voice|vocal)'

# 技术权重（按用户定义：较难 1.5+，较易 0.4）
TECH_WEIGHTS = {
    'bend':     1.5,
    'harmonic': 1.5,
    'tapping':  2.0,
    'vibrato':  0.8,
    'whammy':   1.5,
    'trill':    1.2,
    'tremolo':  1.5,
    'slide':    0.4,
    'hammer':   0.4,
    'pull':     0.4,
}

# ============== Public API ==============

def compute_difficulty(gtp_path: str) -> DifficultyResult:
    """解析 GTP 文件并计算难度，同时写入缓存"""
    # 1. 查缓存
    cached = lookup_difficulty(gtp_path)
    if cached is not None:
        return cached
    # 2. 解析
    try:
        result = _parse_and_score(gtp_path)
    except Exception as e:
        result = DifficultyResult(score=0.0, bpm=0, duration_sec=0.0,
                                  track_count=0, techniques={}, factors={},
                                  error=str(e))
    # 3. 写缓存
    _write_cache(gtp_path, result)
    return result

def lookup_difficulty(gtp_path: str) -> Optional[DifficultyResult]:
    """查缓存 (mtime 一致则命中)"""
    # ... 读 SQLite ...

# ============== Internal ==============

def _parse_and_score(gtp_path: str) -> DifficultyResult:
    """实际解析逻辑"""
    # 1. 用 alphaTab Api 加载
    # 2. 遍历所有 track，按排除规则过滤
    # 3. 遍历 note，统计各技巧
    # 4. 算评分
    # 5. 返回 DifficultyResult

def _write_cache(gtp_path: str, result: DifficultyResult) -> None:
    """写入 SQLite 缓存"""

# ============== Worker ==============

class LoadDifficultyWorkerSignals(QObject):
    one_done = pyqtSignal(str, object)  # path, DifficultyResult
    all_done = pyqtSignal()

class LoadDifficultyWorker(QRunnable):
    """后台遍历目录，计算所有 GTP 文件难度"""
    def __init__(self, folder: str, gtp_files: List[str]):
        super().__init__()
        self.folder = folder
        self.gtp_files = gtp_files
        self.signals = LoadDifficultyWorkerSignals()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        for path in self.gtp_files:
            if self._cancelled:
                break
            result = compute_difficulty(path)
            self.signals.one_done.emit(path, result)
        self.signals.all_done.emit()
```

### alphaTab 解析关键代码（伪代码）

```python
def _parse_and_score(gtp_path: str) -> DifficultyResult:
    from alphaTab import AlphaTabApi, Settings
    settings = Settings()
    # 禁用任何需要 GPU/网络/音频的功能
    settings.core.scriptFile = None
    api = AlphaTabApi(_DummyView(), settings)
    api.load(gtp_path)
    # 等待加载完成 - alphaTab 是异步的，需要 event loop
    # 替代：直接用 alphaTab 内部的 GP7/GP3 解析器

    # 更实际的方案：使用 alphaTab.importer.GpifImporter 或 Gp7Importer
    # 但 alphaTab Python 端可能不直接暴露这些，需要测试

    # 替代方案：直接解析 GPIF XML (GP7/8 是 zip 包)
    # 详见 readme/alphaTab GP7-GP8解析分析报告.md
    ...
```

> **重要技术说明**：alphaTab 的 Python 包 `alphaTab` 提供了 `AlphaTabApi` 但其内部 `score.tracks[].staves[].bars[].voices[].beats[].notes[]` 模型可访问。实际方案：**在 `__init__` 之前构造 `Settings()`，让 `Api.score` 同步加载**（alphaTab 的 `load()` 是同步的，但需要 `MockView` 避免 GUI 依赖）。

### Worker 触发逻辑

```python
def _start_difficulty_scoring(self, folder: str) -> None:
    """启动后台难度评分"""
    # 取消旧 Worker
    if self._difficulty_worker is not None:
        self._difficulty_worker.cancel()

    # 收集当前目录的 GTP 文件
    gtp_files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f))
        and os.path.splitext(f)[1].lower() in SUPPORTED_GTP_EXTENSIONS
    ]
    if not gtp_files:
        return

    worker = LoadDifficultyWorker(folder, gtp_files)
    worker.signals.one_done.connect(self._on_difficulty_one_done)
    worker.signals.all_done.connect(self._on_difficulty_all_done)
    self._difficulty_worker = worker
    QThreadPool.globalInstance().start(worker)
```

### 行文本更新逻辑

```python
def _apply_difficulty_to_item(self, item: QListWidgetItem, result: DifficultyResult) -> None:
    """更新行的文本和 tooltip"""
    if result.error or result.track_count == 0:
        return  # 不显示
    text = item.text()
    # 移除旧星号（如果存在）
    import re
    text = re.sub(r'\s*[☆★]\s*\d+(?:\.\d+)?/10\s*$', '', text)
    # 添加新星号
    star = '★' if result.score >= 5.0 else '☆'
    item.setText(f"{text}  {star} {result.score:.1f}/10")
    # Tooltip
    item.setToolTip(self._build_difficulty_tooltip(result))

def _build_difficulty_tooltip(self, result: DifficultyResult) -> str:
    """构建多语言 tooltip"""
    return I18n.t("settings_window.difficulty_tooltip", ...)
```

## Test Cases

| Case | 场景 | 预期结果 |
|------|------|----------|
| 1 | 首次打开目录，目录含 5 个 GTP | 5 个 item 全部追加 `  ☆ N/10` 或 `  ★ N/10` |
| 2 | 重启程序，目录不变 | item 立即显示评分（< 100ms 内全部就绪） |
| 3 | 关闭数据库权限（chmod 000） | 不报错，列表正常显示但不带星号 |
| 4 | 修改 GTP 文件后重新打开 | mtime 变化触发重算，分数更新 |
| 5 | 一个 0 字节的 .gp 文件 | item 文本不追加星号（解析失败） |
| 6 | 一首含 50 个 bends 的曲子 | score > 7，item 显示 `  ★ N/10` |
| 7 | 一首纯钢琴 GTP（program=0） | item 不显示评分（所有 track 被过滤） |
| 8 | 多轨 GTP（吉他 + 鼓 + 贝斯） | 仅吉他被评分，鼓 + 贝斯均跳过 |
| 9 | Worker 解析中切换目录 | Worker.cancel() 生效，停止发射信号 |
| 10 | 切换语言 | tooltip 文字切换为对应语言 |
| 11 | 鼠标悬停 item | 显示完整明细 tooltip（多行） |
| 12 | 数据库被外部删除 | 重新创建，不影响功能 |
| 13 | 含 `.gp` / `.gp3` / `.gp4` / `.gp5` / `.gpx` / `.gtp` / `.gp7` / `.gp8` 的混合目录 | 所有 gp* 文件均被评分 |
| 14 | 纯贝斯 GTP（无吉他音轨） | 不显示星号（贝斯被排除，track_count=0） |
| 15 | 含人声 + 鼓的 GTP（无吉他） | 不显示星号（人声/鼓被排除） |
