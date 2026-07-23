# Tasks - 难度评分功能 (Difficulty Scoring) 实施

## Task Overview
实现 GTP 文件自动难度评分：在后台静默解析当前目录的 GTP 文件，输出 0-10 评分（写入 SQLite 缓存），在文件列表项末尾以星号形式展示，鼠标悬停展示评分明细。

---

- [x] Task 1: 创建 `data/` 目录与 SQLite 缓存机制
  - [x] SubTask 1.1: 在项目根目录创建 `data/` 目录（如不存在）
  - [x] SubTask 1.2: 在 `difficulty_scoring.py` 中实现 `_init_cache_db()` 懒加载建表逻辑
  - [x] SubTask 1.3: 实现 `lookup_difficulty(path)` SQLite 读取（命中 + mtime 校验）
  - [x] SubTask 1.4: 实现 `_write_cache(path, result)` 写入逻辑（含异常静默处理）
  - **验证**: ✅ 首次调用 `lookup_difficulty` 后 `data/difficulty_cache.db` 自动创建 (16KB)；二次调用 < 1ms 返回

- [x] Task 2: 实现 ApolloTab 解析与技巧检测
  - [x] SubTask 2.1: 在 `difficulty_scoring.py` 中实现 `_parse_and_score(gtp_path) -> DifficultyResult`
  - [x] SubTask 2.2: 实现 `_is_excluded_track(track) -> bool` (MIDI program 0-23 / 32-79 + 名称正则)
  - [x] SubTask 2.3: 实现 `_detect_techniques(note) -> dict` (10 种技巧判定)
  - [x] SubTask 2.4: 实现 `_calculate_score(techniques, bpm, duration, track_count) -> tuple[float, dict]`
  - [x] SubTask 2.5: 异常处理（文件不存在、解析失败、API 不可用）
  - **验证**: ✅ `harmonics.gp` → 5 个泛音；`hammer.gp` → 10 个击弦；`notes.gp` → 0 个技巧

- [x] Task 3: 实现评分计算函数
  - [x] SubTask 3.1: 实现 `compute_difficulty(path) -> DifficultyResult` (查缓存 + 解析 + 写回)
  - [x] SubTask 3.2: 单元自检：用已知曲目（`harmonics.gp` / `hammer.gp`）验证评分 > 5
  - [x] SubTask 3.3: 边界测试：`notes.gp` 无技巧 → 3.5 分 (base 2.0 + bpm 1.5 = 3.5) ✓
  - **验证**: ✅ 评分公式输出符合预期 (空谱 3.5，含 5 泛音 7.3，含 10 击弦 5.5)

- [x] Task 4: 添加三语翻译键
  - [x] SubTask 4.1: 在 `locales/zh_CN.json` 的 `settings_window` 节点新增 8 个键 (含 label/title/calculating/tracks/bpm/duration/techniques/factors)
  - [x] SubTask 4.2: 在 `locales/en_US.json` 添加对应英文翻译
  - [x] SubTask 4.3: 在 `locales/ru_RU.json` 添加对应俄文翻译
  - **验证**: ✅ 三个 JSON 文件 `json.load()` 合法

- [x] Task 5: 实现 `LoadDifficultyWorker`
  - [x] SubTask 5.1: 在 `difficulty_scoring.py` 中实现 `LoadDifficultyWorkerSignals(QObject)`
  - [x] SubTask 5.2: 实现 `LoadDifficultyWorker(QRunnable)` (含 `cancel()` 与 `run()`)
  - [x] SubTask 5.3: 取消机制：检查 `self._cancelled` 提前结束循环
  - [x] SubTask 5.4: 文件过滤：只处理 `gp*` 后缀（`.gp` / `.gp3` / `.gp4` / `.gp5` / `.gpx` / `.gtp` / `.gp7` / `.gp8`）
  - **验证**: ✅ Worker 在 5 个文件上发射 5 次 `one_done` + 1 次 `all_done`（集成测试通过）

- [x] Task 6: SelectionWindow 集成
  - [x] SubTask 6.1: 在 `__init__` 中新增 `self._difficulty_worker` / `self._difficulty_results` / `self._DIFF_STAR_RE`
  - [x] SubTask 6.2: 实现 `_start_difficulty_scoring(folder)` 启动 Worker
  - [x] SubTask 6.3: 实现 `_on_difficulty_one_done(path, result)` 槽
  - [x] SubTask 6.4: 实现 `_on_difficulty_all_done()` 清理引用
  - [x] SubTask 6.5: 实现 `_apply_difficulty_to_item(item, result)` 更新行文本与 tooltip
  - [x] SubTask 6.6: 实现 `_build_difficulty_tooltip(result)` 多语言 tooltip 字符串
  - [x] SubTask 6.7: 在 `_on_files_loaded` 末尾追加 `_start_difficulty_scoring(self.current_directory)`
  - **验证**: ✅ py_compile 通过；6 个新方法 + 1 个 import + 1 个 __init__ 属性 + 1 个触发点

- [x] Task 7: 行文本格式与正则清理
  - [x] SubTask 7.1: 写一个正则 `r'\s*[☆★]\s*\d+(?:\.\d+)?/10\s*$'` 移除旧星号
  - [x] SubTask 7.2: 评分 ≥ 5 用 `★` 实心，< 5 用 `☆` 空心
  - [x] SubTask 7.3: 解析失败 / track_count = 0 不显示星号
  - **验证**: ✅ 集成测试显示 `notes.gp` → `☆ 3.5/10`；`harmonics.gp` → `★ 7.3/10`；`hammer.gp` → `★ 5.5/10`

- [x] Task 8: 集成测试与冒烟
  - [x] SubTask 8.1: `python -m py_compile "TAB Score Viewer.py"` + `difficulty_scoring.py` → 全部通过
  - [x] SubTask 8.2: 12 条 Test Case 静态分析全部通过（解析、缓存、错误处理、过滤、Worker 集成）
  - [x] SubTask 8.3: 5 文件集成测试通过 (notes=3.5 / harmonics=7.3 / hammer=5.5 / compressed=3.5 / multi-track=3.5)
  - **验证**: ✅ 列表项正确显示星号 + tooltip 已构建

- [x] Task 9: 更新项目文档
  - [x] SubTask 9.1: 在 `readme/功能更新.md` 追加 v2.4.0 记录
  - [x] SubTask 9.2: 在主程序文件头注释中新增第 24 项「难度评分」
  - **验证**: ✅ 文档内容准确反映实现

---

## Task Dependencies
- [Task 2] depends on [Task 1] (解析结果需要写缓存)
- [Task 3] depends on [Task 1, Task 2] (评分函数依赖缓存 + 解析)
- [Task 5] depends on [Task 3] (Worker 调用 compute_difficulty)
- [Task 6] depends on [Task 4, Task 5] (Worker + 翻译)
- [Task 7] depends on [Task 6] (行文本更新是 SelectionWindow 一部分)
- [Task 8] depends on [Task 1-7] (所有实现任务)
- [Task 9] depends on [Task 8] (测试通过后更新文档)

## Parallel Execution Plan
**Phase 1 (并行)**: Task 1 + Task 4 (数据缓存 + 翻译键互不依赖)
**Phase 2 (串行)**: Task 2 → Task 3 (解析 → 评分)
**Phase 3 (并行)**: Task 5 + Task 6 (Worker 实现 + SelectionWindow 集成)
**Phase 4 (串行)**: Task 7 (行文本正则清理)
**Phase 5 (串行)**: Task 8 → Task 9 (测试 → 文档)

## Implementation Notes
- 使用 `ApolloTab.parser.parse_score()` 而非 `GTPParser().parse()` (智能调度 GP3-5/GP7/GP8)
- ApolloTab 的 `GTPNote.techniques` 是 `List[TechniqueType]`，通过 enum.name 和 .value 双重匹配保证兼容
- 多语言技术名称在 `_build_difficulty_tooltip` 中硬编码（zh/en/ru），未走 i18n 字典（音乐术语相对稳定）
- _build_difficulty_tooltip 使用 I18n.current_language() 动态选择
- 已知问题：`bends.gp` 因 ApolloTab GP7 解析器 `BendData.bend_style` 字段名不匹配导致 TypeError；已在 _parse_and_score 的 try/except 中捕获并缓存为 score=NULL
