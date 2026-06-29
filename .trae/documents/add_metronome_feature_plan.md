# 吉他谱查看器节拍器功能实施计划

## 1. Summary

为 `TAB Score Viewer` 添加节拍器（Metronome）功能：
- 在 GTP 模式下，节拍器自动跟随歌曲 BPM 与拍号；
- 在图片/PDF 模式下，节拍器使用用户手动输入的 BPM 与拍号（默认 120、4/4）；
- UI 提供「启用开关」「音量滑块」，图片/PDF 模式下额外显示 BPM/拍号输入；
- 底层直接修改 `venv/Lib/site-packages/ApolloTab`（用户确认该库为自有库）。

## 2. Current State Analysis

### 2.1 主程序 `TAB Score Viewer.py`
- 播放主窗口：`DisplayWindow`（行 3198 ~ 6158）。
- 右侧控制面板：`_create_control_panel()`（行 3567 ~ 3648），已有「播放控制」「播放速度」「快捷键帮助」「GTP 音轨音量」四个分组。
- 音频交互：通过 `DisplayWindow.gtp_player: Optional[GTPPlayer]` 调用 ApolloTab 高层 API（`play/stop/seek/set_master_volume` 等）。
- 当前**没有任何节拍器代码或占位**。

### 2.2 ApolloTab 库
- `ApolloTab/audio/midi_converter.py`：`MidiConverter` 将 `GTPSong` 转为 `List[MidiEvent]`，已支持反复展开、音色事件、鼓组通道 9。
- `ApolloTab/audio/synth_engine.py`：`SynthEngine` 基于 FluidSynth 按事件时间线播放，支持 `note_on/off/cc/program_change`。
- `ApolloTab/player.py`：`GTPPlayer` 高层封装，通过 `rebuild_audio_events()` 把 `MidiConverter` 生成的事件加载到 `SynthEngine`。
- 当前**没有现成节拍器实现**。

## 3. Proposed Changes

### 3.1 新增 ApolloTab 模块：`ApolloTab/audio/metronome.py`

**What**：新建文件，封装节拍器配置与事件生成逻辑。

**Why**：职责单一，便于在主程序和 ApolloTab 内部复用；不污染 `MidiConverter` 的核心转换逻辑。

**How**：
- 定义 `MetronomeConfig` 数据类：
  - `enabled: bool`
  - `volume: float`（0.0 ~ 1.0）
  - `accent_pitch: int = 77`（GM 木鱼/High Woodblock，重拍）
  - `normal_pitch: int = 76`（GM 木鱼/Low Woodblock，普通拍）
  - `accent_velocity: int = 127`
  - `normal_velocity: int = 100`
  - `channel: int = 15`（避开旋律通道 0-8/10-15 与鼓通道 9）
- 定义 `MetronomeGenerator` 类：
  - `generate_for_song(song, track_index, config, ticks_per_beat=480)`：
    1. 取 `song.tempo` 为 BPM；
    2. 按 `expand_measure_indices()` 展开反复记号；
    3. 遍历每个小节，读取 `measure.time_signature`（`(numerator, denominator)`）；
    4. 每小节第一拍生成重拍 `note_on`/`note_off`，其余拍生成普通拍；
    5. 在事件列表开头插入通道 15 的 Bank Select（CC#0=1, CC#32=0）+ Program Change=0，启用 GM 鼓组；
    6. 返回 `List[MidiEvent]`。
  - `generate_simple(bpm, numerator, denominator, total_ticks, ticks_per_beat, config)`：
    1. 用于图片/PDF 模式，无 `GTPSong` 时生成固定 BPM/拍号的节拍器事件；
    2. 总时长 `total_ticks` 由调用方根据播放总时长或一个足够大的值（如 10 分钟）传入；
    3. 返回 `List[MidiEvent]`。
- 每个点击声持续 50 ms 对应的 tick 数后发送 `note_off`。

### 3.2 修改 `ApolloTab/audio/midi_converter.py`

**What**：让 `convert()` 与 `convert_all_tracks()` 支持混入节拍器事件。

**Why**：节拍器需要与乐曲事件在同一时间线上精确同步，由 `SynthEngine` 统一播放。

**How**：
- 在两个方法签名末尾增加可选参数：`metronome_config: Optional[MetronomeConfig] = None`。
- 若 `config is not None and config.enabled`：
  1. 调用 `MetronomeGenerator.generate_for_song(...)` 得到节拍器事件；
  2. 将节拍器事件 extend 到乐曲事件列表；
  3. 保持最终按 `(time, type_priority)` 排序（`control_change`/`program_change` 优先于 `note_on`）。
- 在 `convert_all_tracks()` 中，节拍器仍使用通道 15，不占用旋律/鼓轨通道。

### 3.3 修改 `ApolloTab/player.py`

**What**：在 `GTPPlayer` 中增加节拍器状态、配置接口，以及非 GTP 模式下的纯节拍器播放能力。

**Why**：主程序只需调用 `GTPPlayer.set_metronome()` 即可控制；图片/PDF 模式无 `GTPSong`，需要独立的节拍器播放入口。

**How**：
- 在 `__init__` 中新增：
  - `self._metronome_enabled: bool = False`
  - `self._metronome_volume: float = 0.7`
  - `self._metronome_config: MetronomeConfig = MetronomeConfig()`
- 新增方法：
  - `set_metronome(enabled: bool, volume: float) -> None`：
    1. 更新 `_metronome_enabled`、`_metronome_volume`；
    2. 更新 `_metronome_config.enabled` 与 `_metronome_config.volume`（通过线性映射把 0.0~1.0 转成 MIDI velocity）；
    3. 若当前已加载歌曲且音频模式不是 `MODE_OFF`，调用 `rebuild_audio_events()` 重建事件。
  - `play_metronome_only(bpm: int = 120, numerator: int = 4, denominator: int = 4, duration_minutes: int = 10) -> None`：
    1. 使用 `MetronomeGenerator.generate_simple()` 生成足够长的节拍器事件；
    2. 调用 `_synth_engine.load_events()` 加载；
    3. 调用 `_synth_engine.play()`。
- 修改 `rebuild_audio_events()`：
  1. 在调用 `convert()` / `convert_all_tracks()` 时传入 `metronome_config=self._metronome_config`；
  2. 其余逻辑保持不变。
- 修改 `set_master_volume()`：保持总音量控制不变，节拍器音量已通过 velocity 缩放。

### 3.4 修改 `ApolloTab/audio/__init__.py` 与 `ApolloTab/__init__.py`

**What**：导出新增的节拍器类，方便主程序直接使用。

**How**：
- `ApolloTab/audio/__init__.py` 增加 `from .metronome import MetronomeConfig, MetronomeGenerator`。
- `ApolloTab/__init__.py` 增加 `from .audio import MetronomeConfig, MetronomeGenerator`。

### 3.5 修改主程序 `TAB Score Viewer.py`

**What**：新增节拍器 UI 控件、状态保存、事件回调，并在播放控制中同步节拍器。

**Why**：把用户操作透传到 ApolloTab；保证 GTP/图片两种模式都能启用。

**How**：
- 在 `DisplayWindow.__init__()`（行 3210 附近）新增：
  - `self._metronome_enabled: bool = False`
  - `self._metronome_volume: float = 0.7`
  - `self._metronome_bpm: int = 120`
  - `self._metronome_numerator: int = 4`
  - `self._metronome_denominator: int = 4`
- 在 `_create_control_panel()`（行 3567 附近）新增「节拍器」分组 `metronome_group_box`：
  - `metronome_enable_check: QCheckBox`，文本使用 `I18n.t("control_panel.metronome_enable")`；
  - `metronome_volume_slider: QSlider(Qt.Horizontal)`，范围 0~100，默认值 70；
  - `metronome_bpm_spin: QSpinBox`，范围 20~300，默认值 120，标签 `I18n.t("control_panel.metronome_bpm")`；
  - `metronome_beat_spin: QSpinBox`，范围 1~16，默认值 4，标签 `I18n.t("control_panel.metronome_beat")`（拍号分子，分母固定为 4，因为绝大多数吉他谱为 X/4 拍）；
  - BPM/拍号输入仅在非 GTP 模式下可见；
  - 布局放在「播放控制」分组之后、「播放速度」分组之前；
  - 默认可见（所有模式都显示，但内部控件按需显隐）。
- 新增回调：
  - `_on_metronome_enabled_changed(state: int)`：
    1. 更新 `self._metronome_enabled`；
    2. 若 `gtp_player` 存在，调用 `gtp_player.set_metronome(self._metronome_enabled, self._metronome_volume)`；
    3. 若当前正在播放且处于图片/PDF 模式，按需启动/停止纯节拍器播放。
  - `_on_metronome_volume_changed(value: int)`：
    1. 更新 `self._metronome_volume = value / 100.0`；
    2. 同步到 `gtp_player.set_metronome(...)`。
  - `_on_metronome_bpm_changed(value: int)`：
    1. 更新 `self._metronome_bpm`；
    2. 若当前处于图片/PDF 模式且正在播放，先停止再重新调用 `gtp_player.play_metronome_only(...)` 以应用新 BPM。
  - `_on_metronome_beat_changed(value: int)`：
    1. 更新 `self._metronome_numerator`；
    2. 若当前处于图片/PDF 模式且正在播放，重新生成节拍器事件并播放。
- 修改 `_init_audio_engine()`：
  1. 无论当前是 GTP 还是图片/PDF 模式，都确保创建 `GTPPlayer` 并调用 `init_audio()`；
  2. 初始化后立即调用 `gtp_player.set_metronome(self._metronome_enabled, self._metronome_volume)`。
- 修改 `start_playback()`：
  - 图片/PDF 模式下，若 `_metronome_enabled` 为 True，调用 `gtp_player.play_metronome_only(self._metronome_bpm, self._metronome_numerator, self._metronome_denominator)` 启动节拍器；
  - GTP 模式下保持现有逻辑，`gtp_player.play()` 会自动播放已混入的节拍器事件。
- 修改 `stop_playback()`：
  - 统一调用 `gtp_player.stop()`，可同时停止乐曲与节拍器。
- 修改 `_on_content_loaded()`：
  - 节拍器分组始终显示，不随模式隐藏；
  - 根据当前是否为 GTP 模式，控制 `metronome_bpm_spin` 与 `metronome_beat_spin` 的可见性：GTP 模式隐藏，图片/PDF 模式显示；
  - 仅控制「播放速度」「GTP 音轨音量」等原有分组的显隐。

### 3.6 修改翻译文件

**What**：在 `locales/zh_CN.json`、`locales/en_US.json`、`locales/ru_RU.json` 中添加节拍器相关键。

**How**：在 `control_panel` 节点下新增：
```json
"metronome_group": "节拍器",
"metronome_enable": "启用节拍器",
"metronome_volume": "音量",
"metronome_bpm": "BPM:",
"metronome_beat": "拍号:"
```
英文/俄文同步添加对应翻译。

### 3.7 更新文档

**What**：按用户规则更新 `readme/功能更新.md` 与 `readme/实施文档.md`。

**How**：
- `readme/功能更新.md`：新增条目，说明新增节拍器功能、支持模式、UI 控制、底层改动文件。
- `readme/实施文档.md`：补充节拍器模块设计、通道选择、事件生成逻辑、与播放控制的集成方式。
- 若文档中已有音频/播放相关章节，直接追加；若无，新建「节拍器」小节。

## 4. Assumptions & Decisions

1. **ApolloTab 直接修改**：用户确认 `ApolloTab` 为自有库，允许直接修改 `venv/Lib/site-packages/ApolloTab` 下文件；不单独复制到项目目录。
2. **UI 控制粒度**：不添加音色选择。GTP 模式自动读取歌曲 BPM/拍号；图片/PDF 模式在 UI 中显示 BPM 输入框（20~300）与拍号分子输入框（1~16，分母固定为 4），默认 120/4/4。
3. **节拍器通道**：使用 MIDI 通道 15，避开鼓通道 9（避免与 GP 文件鼓轨冲突），避开旋律通道 0-8/10-14。
4. **节拍器音色**：固定使用 GM 木鱼音色（重拍 77 High Woodblock，普通拍 76 Low Woodblock），通过 Bank Select + Program Change 在通道 15 启用 GM 鼓组。
5. **音量映射**：UI 音量 0~100 线性映射到 MIDI velocity 0~127；重拍 velocity 始终略高于普通拍。
6. **图片/PDF 模式时长**：`play_metronome_only()` 默认生成 10 分钟事件，足够覆盖一般练习；停止播放时由 `gtp_player.stop()` 中断。
7. **事件生成时机**：GTP 模式下在 `rebuild_audio_events()` 中混入节拍器事件，天然支持 play/pause/seek/A-B 循环；图片/PDF 模式下单独生成纯节拍器事件。

## 5. Verification Steps

### 5.1 单元/集成验证
1. 加载任意 `.gp3/.gp4/.gp5/.gp7/.gp8` 文件，启用节拍器，点击播放：
   - 能听到规律点击声；
   - 每小节第一拍音高明显更高；
   - 调节音量滑块，点击声响度变化；
   - 暂停/继续/拖动进度条后，点击声与谱面拍点保持对齐。
2. 加载 JPG/PNG/PDF 谱面，启用节拍器，点击播放：
   - 默认听到 120 BPM、4/4 拍的点击声；
   - 修改 BPM 输入（如 90、160），点击声速度随之变化；
   - 修改拍号输入（如 3、6），重拍位置随之变化；
   - 音量滑块有效；
   - 停止播放后点击声立即停止。
3. 反复记号测试：加载带反复记号的 GTP 文件，确认反复展开后每小节第一拍仍为重拍。
4. A-B 循环测试：设置 A/B 循环，播放到达 B 点后循环回 A 点，节拍器同步循环。
5. 多轨 GTP 测试：切换全轨/单轨音频模式，节拍器始终存在且不干扰原鼓轨。

### 5.2 回归验证
1. 关闭节拍器时，GTP 播放行为与修改前完全一致。
2. 音量、速度、A-B 循环、音轨音量等原有功能不受影响。
3. 界面布局在 240~280px 右侧面板宽度内不被撑爆。
4. 打包/运行时 `ApolloTab` 修改项随 venv 存在；若重新创建 venv 需重新应用修改。

## 6. 涉及文件清单

| 文件 | 操作 | 说明 |
|---|---|---|
| `venv/Lib/site-packages/ApolloTab/audio/metronome.py` | 新增 | 节拍器配置与事件生成 |
| `venv/Lib/site-packages/ApolloTab/audio/midi_converter.py` | 修改 | 混入节拍器事件 |
| `venv/Lib/site-packages/ApolloTab/player.py` | 修改 | 节拍器状态与纯节拍器播放 |
| `venv/Lib/site-packages/ApolloTab/audio/__init__.py` | 修改 | 导出 MetronomeConfig/MetronomeGenerator |
| `venv/Lib/site-packages/ApolloTab/__init__.py` | 修改 | 导出 MetronomeConfig/MetronomeGenerator |
| `TAB Score Viewer.py` | 修改 | UI、状态、播放同步 |
| `locales/zh_CN.json` | 修改 | 中文翻译 |
| `locales/en_US.json` | 修改 | 英文翻译 |
| `locales/ru_RU.json` | 修改 | 俄文翻译 |
| `readme/功能更新.md` | 修改 | 功能更新记录 |
| `readme/实施文档.md` | 修改 | 实施文档补充 |
