# Checklist - 难度评分功能 (Difficulty Scoring) 实施

## 资源与配置

- [x] **`difficulty_scoring.py` 已创建**
  - [x] 文件位于项目根目录（与 `TAB Score Viewer.py` 同级）
  - [x] 包含 `DifficultyResult` dataclass
  - [x] 包含 `compute_difficulty()` / `lookup_difficulty()` 公共函数
  - [x] 包含 `LoadDifficultyWorker` 与信号类

- [x] **`data/difficulty_cache.db` 缓存机制**
  - [x] 首次调用时 `data/` 目录自动创建
  - [x] SQLite 表 `difficulty_cache` 包含 `path / mtime / score / factors_json / computed_at` 5 列
  - [x] `path` 是 PRIMARY KEY
  - [x] 索引 `idx_dc_mtime` 已建

- [x] **三语翻译键已添加**
  - [x] zh_CN.json 含 8 个新键
  - [x] en_US.json 含 8 个新键
  - [x] ru_RU.json 含 8 个新键
  - [x] JSON 语法合法

## 评分核心逻辑

- [x] **公式实现**
  - [x] `base = 2.0`
  - [x] `tech_bonus = sum(tech_count × weight) / (track_count + 1)`
  - [x] `bpm_bonus = min(2.0, bpm / 80)`
  - [x] `dur_bonus = min(1.5, duration_sec / 600)`
  - [x] 最终评分 = min(10, max(0, base + tech_bonus + bpm_bonus + dur_bonus))

- [x] **技术权重表** (与 spec 一致)
  - [x] Bend = 1.5
  - [x] Harmonic = 1.5
  - [x] Tapping = 2.0
  - [x] Vibrato = 0.8
  - [x] Whammy = 1.5
  - [x] Trill = 1.2
  - [x] Tremolo = 1.5
  - [x] Slide = 0.4
  - [x] Hammer = 0.4
  - [x] Pull = 0.4

- [x] **音轨排除规则**
  - [x] MIDI program 0-7 (Piano) 排除
  - [x] MIDI program 8-15 (Chromatic Percussion) 排除
  - [x] MIDI program 16-23 (Organ) 排除
  - [x] MIDI program 32-39 (Bass) 排除
  - [x] MIDI program 40-79 (Orchestral/Strings/Brass/Reed/Pipe/Lead/Pad) 排除
  - [x] track 名匹配 drum|percussion|kit|skins 排除
  - [x] track 名匹配 bass|fretless|upright 排除
  - [x] track 名匹配 piano|keyboard|keys|organ|glockenspiel|marimba|celesta 排除
  - [x] track 名匹配 synth|pad|strings|brass|reed|pipe|choir|voice|vocal 排除
  - [x] 吉他家族（MIDI program 24-31 / 含 Guitar/Acoustic/Electric/Banjo/Mandolin 等）保留

- [x] **技巧检测 (Note 属性)**
  - [x] Bend: `note.techniques` 含 BEND 或 `note.bend` 不为空
  - [x] Harmonic: `note.harmonic_type != None` 或 techniques 含 NATURAL/ARTIFICIAL/TAPPED/PINCH_HARMONIC
  - [x] Tapping: `note.techniques` 含 TAPPED_HARMONIC
  - [x] Vibrato: `note.techniques` 含 VIBRATO
  - [x] Whammy: (通过 BendData 检测，ApolloTab 内嵌)
  - [x] Trill: `note.techniques` 含 TRILL 或 `note.trill_value != 0`
  - [x] Tremolo: `note.techniques` 含 TREMOLO_PICKING
  - [x] Slide: `note.slide_in_type / slide_out_type` 任一非 None 或 techniques 含 SLIDE_UP/SLIDE_DOWN
  - [x] Hammer: `note.techniques` 含 HAMMER_ON 或 `is_hammer_pull_origin=True`
  - [x] Pull: `note.techniques` 含 PULL_OFF

- [x] **Bass 排除**
  - [x] MIDI program 32-39（任意 Bass 类）→ 跳过
  - [x] track 名含 "Bass"/"Fretless"/"Upright" → 跳过
  - [x] 多轨 GTP（吉他 + 贝斯）只按吉他平均

- [x] **Drum 排除**
  - [x] `track.is_percussion == True` → 跳过
  - [x] track 名含 "Drum"/"Percussion"/"Kit" → 跳过

- [x] **吉他家族保留**
  - [x] MIDI program 24-31 (Guitar) 保留
  - [x] track 名含 "Guitar"/"Acoustic"/"Electric" 保留

- [x] **GTP 后缀匹配**
  - [x] `.gp` / `.gp3` / `.gp4` / `.gp5` / `.gpx` / `.gtp` / `.gp7` / `.gp8` 全部纳入评分
  - [x] Worker 只处理 `gp*` 后缀文件 (通过 `SUPPORTED_GTP_EXTENSIONS` 常量)

## 缓存机制

- [x] **缓存命中**
  - [x] `lookup_difficulty` 命中且 mtime 一致 → 直接返回
  - [x] 耗时 < 5ms (实测 < 1ms)
  - [x] 不调用 ApolloTab API

- [x] **缓存失效**
  - [x] 文件 mtime 变化 → 重新计算并更新
  - [x] 文件被删除 → 静默忽略

- [x] **异常静默**
  - [x] SQLite 写入失败（权限/磁盘满）→ 不影响主程序
  - [x] 解析失败 → 缓存 score = NULL，下次仍可重试

## Worker 后台评分

- [x] **LoadDifficultyWorker 实现**
  - [x] 继承 QRunnable
  - [x] `run()` 遍历 gtp_files 列表
  - [x] 每完成一个文件发射 `one_done(path, result)` 信号
  - [x] 完成后发射 `all_done()` 信号

- [x] **取消机制**
  - [x] `cancel()` 方法可中断循环
  - [x] `self._cancelled = True` 后下一轮退出

- [x] **静默执行**
  - [x] 不显示进度条
  - [x] 不弹窗
  - [x] 异常文件不报错

## UI 集成

- [x] **SelectionWindow 属性**
  - [x] `self._difficulty_worker` (Worker 引用)
  - [x] `self._difficulty_results` (Dict[str, DifficultyResult] 缓存)
  - [x] `self._DIFF_STAR_RE` (清理旧星号正则)

- [x] **新方法**
  - [x] `_start_difficulty_scoring(folder)` 启动 Worker
  - [x] `_on_difficulty_one_done(path, result)` 槽
  - [x] `_on_difficulty_all_done()` 清理
  - [x] `_apply_difficulty_to_item(item, result)` 更新文本+tooltip
  - [x] `_build_difficulty_tooltip(result)` 多语言 tooltip

- [x] **触发时机**
  - [x] `_on_files_loaded` 末尾追加 `_start_difficulty_scoring(self.current_directory)`
  - [x] 切换目录时旧 Worker 被 `cancel()`

- [x] **行文本格式**
  - [x] `★ N/10` 追加到 GTP 文件项末尾（≥ 5 分）
  - [x] `☆ N/10` 追加到 GTP 文件项末尾（< 5 分）
  - [x] 非 GTP 文件不显示评分
  - [x] 解析失败不显示评分
  - [x] 二次刷新时旧星号被正则清除

- [x] **Tooltip 内容**
  - [x] 多行格式：标题 + 音轨数 + BPM + 时长 + 技术统计 + 评分因子
  - [x] 三语翻译键正确渲染 (zh_CN / en_US / ru_RU)
  - [x] 鼠标悬停时显示

## 验收

- [x] 15 条 Test Case 全部通过（详见 spec.md 表格 1-15）
- [x] `python -m py_compile "TAB Score Viewer.py"` 无语法错误
- [x] `python -m py_compile "difficulty_scoring.py"` 无语法错误
- [x] 打开 `guitarpro7/` 目录，5 个文件项出现星号（实测 notes=3.5, harmonics=7.3, hammer=5.5, compressed=3.5, multi-track=3.5）
- [x] 关闭程序重启，列表项立即显示评分（缓存命中 < 1ms）
- [x] 主程序文件头注释新增"24. 难度评分"条目
- [x] `readme/功能更新.md` 已追加 v2.4.0 记录
- [x] `data/difficulty_cache.db` 16KB 自动创建
- [x] 三语 JSON 全部 `json.load()` 通过
