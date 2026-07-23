# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Difficulty Scoring Module
难度评分模块 - 解析 GTP 文件并生成 0-10 评分

功能:
  1. 静默解析 GTP 文件（GP3-5 / GP6 / GP7 / GP8 / .gtp / .gp 等）
  2. 排除鼓 / 钢琴 / 键盘 / 贝斯 / 合成 / 管弦 等非吉他音轨
  3. 统计各类演奏技巧（Bend / Harmonic / Tapping / Vibrato / Slide / Hammer / Pull / Trill / Whammy / Tremolo）
  4. 按多因子公式计算 0-10 评分
  5. SQLite 缓存 (data/difficulty_cache.db)，按 mtime 自动失效
  6. 后台 Worker 遍历目录时静默执行

设计:
  - 评分仅反映**吉他家族**音轨的演奏难度
  - 数据库读取/写入异常静默忽略，不影响主程序
  - 文件 mtime 变化时自动重新计算
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal


# ============================================================
# 路径常量
# ============================================================

CACHE_DB_PATH: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data', 'difficulty_cache.db'
)


# ============================================================
# 音轨排除规则
# ============================================================

# 排除的 MIDI program 范围 (GM 标准)
#   0-7   Piano (Grand/Brilliant/Electric/Clavinet 等)
#   8-15  Chromatic Percussion (Celesta/Marimba/Glockenspiel 等)
#   16-23 Organ (Hammond/Church/Reed 等)
#   24-31 Guitar — 保留
#   32-39 Bass (Electric/Synth/Acoustic/Fretless/Slap/Pop) — 排除
#   40-79 Orchestral/Strings/Brass/Reed/Pipe/Lead/Pad — 排除
EXCLUDED_PROGRAMS = set(range(0, 24)) | set(range(32, 80))

# 排除的轨道名正则 (大小写不敏感)
EXCLUDED_TRACK_NAME_RE = re.compile(
    r'(drum|percussion|kit|skins|bass|fretless|upright|stand[\s_]*up|'
    r'piano|keyboard|keys|organ|glockenspiel|marimba|celesta|celeste|'
    r'synth|pad|strings|brass|reed|pipe|choir|voice|vocal)',
    re.IGNORECASE
)

# 吉他家族保留的轨道名 (大小写不敏感)
GUITAR_NAME_RE = re.compile(
    r'(guitar|acoustic|electric|jazz|classical|nylon|steel|bass\s*guitar|'
    r'banjo|mandolin|sitar|ukelele|ukulele|bouzouki|lute)',
    re.IGNORECASE
)


# ============================================================
# 技术权重表 (按用户定义：较难 1.5+，较易 0.4)
# ============================================================

TECH_WEIGHTS: Dict[str, float] = {
    'bend':     1.3,   # 推弦 (较难)
    'harmonic': 1.3,   # 泛音 (较难)
    'tapping':  1.8,   # 点弦 (较难)
    'vibrato':  0.8,   # 颤音 (较难)
    'whammy':   1.2,   # 摇杆 (较难)
    'trill':    1.2,   # 击弦颤音 (较难)
    'tremolo':  1.5,   # 震音拨弦 (较难)
    'slide':    0.3,   # 滑弦 (较易)
    'hammer':   0.3,   # 击弦 (较易)
    'pull':     0.3,   # 勾弦 (较易)
}


# ============================================================
# DataClass
# ============================================================

@dataclass
class DifficultyResult:
    """难度评分结果 (含缓存标记)"""
    score: float = 0.0
    bpm: int = 0
    duration_sec: float = 0.0
    track_count: int = 0
    techniques: Dict[str, int] = field(default_factory=dict)
    factors: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    cached: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'DifficultyResult':
        return cls(**d)


# ============================================================
# SQLite 缓存
# ============================================================

_DB_INITIALIZED: bool = False


def _ensure_data_dir() -> None:
    """确保 data/ 目录存在"""
    try:
        os.makedirs(os.path.dirname(CACHE_DB_PATH), exist_ok=True)
    except OSError:
        pass


def _init_cache_db() -> None:
    """懒加载建表 (首次调用时执行)"""
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return
    try:
        _ensure_data_dir()
        conn = sqlite3.connect(CACHE_DB_PATH)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS difficulty_cache ("
                "  path TEXT PRIMARY KEY,"
                "  mtime INTEGER NOT NULL,"
                "  score REAL,"
                "  factors_json TEXT NOT NULL,"
                "  computed_at INTEGER NOT NULL"
                ")"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_dc_mtime "
                "ON difficulty_cache(mtime)"
            )
            conn.commit()
            _DB_INITIALIZED = True
        finally:
            conn.close()
    except (sqlite3.Error, OSError):
        # 异常静默
        pass


def lookup_difficulty(gtp_path: str) -> Optional[DifficultyResult]:
    """
    仅查缓存 (mtime 一致则命中)，不解析

    返回:
      - DifficultyResult(cached=True) 当 mtime 一致且 score 有效
      - DifficultyResult(cached=True, error=...) 当 mtime 一致但上次解析失败
      - None 当缓存未命中或 mtime 不一致
    """
    try:
        if not os.path.isfile(gtp_path):
            return None
        stat = os.stat(gtp_path)
        current_mtime = int(stat.st_mtime)

        _init_cache_db()
        conn = sqlite3.connect(CACHE_DB_PATH)
        try:
            row = conn.execute(
                "SELECT mtime, score, factors_json "
                "FROM difficulty_cache WHERE path = ?",
                (gtp_path,)
            ).fetchone()
            if row is None:
                return None
            cached_mtime, score, factors_json = row
            if cached_mtime != current_mtime:
                return None
            data = json.loads(factors_json)
            result = DifficultyResult.from_dict(data)
            result.cached = True
            return result
        finally:
            conn.close()
    except (sqlite3.Error, OSError, ValueError, json.JSONDecodeError):
        return None


def _write_cache(gtp_path: str, result: DifficultyResult) -> None:
    """写入 SQLite 缓存 (异常静默)"""
    try:
        if not os.path.isfile(gtp_path):
            return
        stat = os.stat(gtp_path)
        mtime = int(stat.st_mtime)

        _init_cache_db()
        conn = sqlite3.connect(CACHE_DB_PATH)
        try:
            # 解析失败时 score 存 NULL
            score = result.score if not result.error else None
            conn.execute(
                "INSERT OR REPLACE INTO difficulty_cache "
                "(path, mtime, score, factors_json, computed_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    gtp_path,
                    mtime,
                    score,
                    json.dumps(result.to_dict(), ensure_ascii=False),
                    int(time.time())
                )
            )
            conn.commit()
        finally:
            conn.close()
    except (sqlite3.Error, OSError, ValueError):
        pass


# ============================================================
# 评分核心
# ============================================================

def _is_excluded_track(track) -> bool:
    """
    判断音轨是否应排除 (鼓/钢/键盘/贝斯/合成/管弦等)

    排除条件 (任一满足):
      1. track.is_percussion == True
      2. track.instrument 属于 EXCLUDED_PROGRAMS
      3. track.name 匹配 EXCLUDED_TRACK_NAME_RE
    """
    try:
        # 1. 打击乐标志
        if getattr(track, 'is_percussion', False):
            return True
        # 2. MIDI program 范围
        instrument = getattr(track, 'instrument', -1)
        if isinstance(instrument, int) and instrument in EXCLUDED_PROGRAMS:
            return True
        # 3. 名称正则
        name = getattr(track, 'name', '') or ''
        if name and EXCLUDED_TRACK_NAME_RE.search(name):
            return True
    except Exception:
        return True
    return False


def _is_guitar_track(track) -> bool:
    """
    判断音轨是否属于"吉他家族"（与排除规则互补）

    保留条件:
      - track.instrument 在 24-31 (Guitar 范围)
      - 或 track.name 匹配 GUITAR_NAME_RE
      - 或在排除规则外的可弹拨弦乐器 (默认非排除则视为吉他家族)
    """
    try:
        instrument = getattr(track, 'instrument', -1)
        if isinstance(instrument, int) and 24 <= instrument <= 31:
            return True
        name = getattr(track, 'name', '') or ''
        if name and GUITAR_NAME_RE.search(name):
            return True
    except Exception:
        pass
    return False


def _detect_techniques(note, tech_counter: Dict[str, int]) -> None:
    """
    统计单个 Note 的技巧到 tech_counter

    映射:
      - BEND        : note.techniques 含 BEND 或 note.bend 不为空
      - HARMONIC    : note.techniques 含 NATURAL/ARTIFICIAL/TAPPED/PINCH_HARMONIC
                      或 note.harmonic_type 不为空
      - TAPPING     : note.techniques 含 TAPPED_HARMONIC (ApolloTab 模型中点弦通过 TAPPED_HARMONIC 表达)
                      或 note.right_hand_finger 触发等
      - VIBRATO     : note.techniques 含 VIBRATO
      - TRILL       : note.techniques 含 TRILL 或 note.trill_value != 0
      - TREMOLO     : note.techniques 含 TREMOLO_PICKING
      - SLIDE       : note.techniques 含 SLIDE_UP/SLIDE_DOWN
                      或 note.slide_in_type 不为空 或 note.slide_out_type 不为空
      - HAMMER      : note.techniques 含 HAMMER_ON
      - PULL        : note.techniques 含 PULL_OFF
    """
    try:
        techniques = getattr(note, 'techniques', None) or []
        # 转为字符串列表以安全比较
        tech_strs = set()
        for t in techniques:
            try:
                tech_strs.add(str(t.value) if hasattr(t, 'value') else str(t))
            except Exception:
                pass
        tech_names = set()
        for t in techniques:
            try:
                tech_names.add(t.name)
            except Exception:
                pass

        # BEND
        if 'Bend' in tech_names or 'BEND' in tech_strs:
            tech_counter['bend'] += 1
        elif getattr(note, 'bend', None) is not None:
            tech_counter['bend'] += 1

        # HARMONIC
        harmonic_type = getattr(note, 'harmonic_type', None)
        if harmonic_type:
            tech_counter['harmonic'] += 1
        else:
            for hname in ('Natural Harmonic', 'Artificial Harmonic',
                          'Tapped Harmonic', 'Pinch Harmonic',
                          'NATURAL_HARMONIC', 'ARTIFICIAL_HARMONIC',
                          'TAPPED_HARMONIC', 'PINCH_HARMONIC'):
                if hname in tech_names or hname in tech_strs:
                    tech_counter['harmonic'] += 1
                    break

        # TAPPING (ApolloTab: Tapped Harmonic + Tapped note via is_hammer_pull_origin)
        if 'Tapped Harmonic' in tech_names or 'TAPPED_HARMONIC' in tech_strs:
            tech_counter['tapping'] += 1

        # VIBRATO
        if 'Vibrato' in tech_names or 'VIBRATO' in tech_strs:
            tech_counter['vibrato'] += 1

        # TRILL
        if 'Trill' in tech_names or 'TRILL' in tech_strs:
            tech_counter['trill'] += 1
        elif getattr(note, 'trill_value', 0) not in (0, -1, None):
            tech_counter['trill'] += 1

        # TREMOLO
        if 'Tremolo Picking' in tech_names or 'TREMOLO_PICKING' in tech_strs:
            tech_counter['tremolo'] += 1

        # SLIDE
        slide_in = getattr(note, 'slide_in_type', None)
        slide_out = getattr(note, 'slide_out_type', None)
        slide_in_set = any(s in tech_names for s in ('Slide Up', 'Slide Down')) or \
                       any(s in tech_strs for s in ('SLIDE_UP', 'SLIDE_DOWN'))
        if slide_in or slide_out or slide_in_set:
            tech_counter['slide'] += 1

        # HAMMER
        if 'Hammer On' in tech_names or 'HAMMER_ON' in tech_strs:
            tech_counter['hammer'] += 1
        elif getattr(note, 'is_hammer_pull_origin', False):
            # 简化: hammer/pull origin 默认按 hammer 计
            tech_counter['hammer'] += 1

        # PULL
        if 'Pull Off' in tech_names or 'PULL_OFF' in tech_strs:
            tech_counter['pull'] += 1

    except Exception:
        # 单 note 检测异常不影响整体
        pass


def _calculate_score(
    techniques: Dict[str, int],
    bpm: int,
    duration_sec: float,
    track_count: int
) -> tuple:
    """
    计算难度评分 (0-10)

    公式:
      base = 2.0
      tech_bonus = sum(tech_count × weight) / (track_count + 1)
      bpm_bonus = min(2.0, bpm / 80)
      dur_bonus = min(1.5, duration_sec / 600)
      score = clamp(base + tech_bonus + bpm_bonus + dur_bonus, 0, 10)
    """
    # 技术密度
    tech_sum = 0.0
    for tech_name, count in techniques.items():
        weight = TECH_WEIGHTS.get(tech_name, 0.0)
        tech_sum += count * weight
    tech_bonus = tech_sum / (track_count + 1)

    # BPM 因子 (< 80 BPM 不加分)
    bpm_value = max(0, bpm)
    bpm_bonus = min(2.0, bpm_value / 80.0)

    # 时长因子 (10 分钟封顶 1.5)
    dur_value = max(0.0, duration_sec)
    dur_bonus = min(1.5, dur_value / 600.0)

    # 基础分
    base = 2.0

    # 总分 (clamp 0-10)
    raw = base + tech_bonus + bpm_bonus + dur_bonus
    score = max(0.0, min(10.0, raw))

    factors = {
        'base': round(base, 2),
        'tech': round(tech_bonus, 2),
        'bpm': round(bpm_bonus, 2),
        'dur': round(dur_bonus, 2),
    }
    return round(score, 1), factors


def _parse_and_score(gtp_path: str) -> DifficultyResult:
    """
    实际解析逻辑 (核心)

    步骤:
      1. parse_score(path) → GTPSong (智能调度 GP3-5/GP7/GP8)
      2. 遍历 song.tracks，过滤鼓/钢/键盘/贝斯/合成/管弦
      3. 取吉他家族音轨，按轨道平均
      4. 遍历每个音轨的 measures.beats.notes，统计技巧
      5. 计算总时长 = 总拍数 × (60 / bpm)
      6. 计算 0-10 评分
    """
    # 延迟导入 (避免在不支持 ApolloTab 的环境崩溃)
    try:
        from ApolloTab.parser import parse_score
    except ImportError as e:
        return DifficultyResult(
            score=0.0, bpm=0, duration_sec=0.0, track_count=0,
            techniques={}, factors={},
            error=f"ApolloTab unavailable: {e}"
        )

    try:
        song = parse_score(gtp_path)
    except Exception as e:
        return DifficultyResult(
            score=0.0, bpm=0, duration_sec=0.0, track_count=0,
            techniques={}, factors={},
            error=f"Parse failed: {type(e).__name__}: {e}"
        )

    if song is None or not getattr(song, 'tracks', None):
        return DifficultyResult(
            score=0.0, bpm=0, duration_sec=0.0, track_count=0,
            techniques={}, factors={},
            error="Empty song"
        )

    bpm = int(getattr(song, 'tempo', 120) or 120)

    # 过滤吉他家族音轨
    guitar_tracks = [t for t in song.tracks if not _is_excluded_track(t)]
    if not guitar_tracks:
        return DifficultyResult(
            score=0.0, bpm=bpm, duration_sec=0.0, track_count=0,
            techniques={}, factors={},
            error="No guitar track"
        )

    # 累计所有吉他家族音轨的技巧
    tech_counter: Dict[str, int] = {k: 0 for k in TECH_WEIGHTS}
    total_beats = 0

    for track in guitar_tracks:
        measures = getattr(track, 'measures', None) or []
        for measure in measures:
            beats = getattr(measure, 'beats', None) or []
            total_beats += len(beats)
            for beat in beats:
                notes = getattr(beat, 'notes', None) or []
                for note in notes:
                    if getattr(note, 'is_rest', False):
                        continue
                    _detect_techniques(note, tech_counter)

    # 总时长 (秒) = 总拍数 × (60 / BPM)
    duration_sec = 0.0
    if bpm > 0 and total_beats > 0:
        duration_sec = total_beats * (60.0 / bpm)

    track_count = len(guitar_tracks)
    score, factors = _calculate_score(tech_counter, bpm, duration_sec, track_count)

    return DifficultyResult(
        score=score,
        bpm=bpm,
        duration_sec=round(duration_sec, 1),
        track_count=track_count,
        techniques=dict(tech_counter),
        factors=factors,
        error=None
    )


# ============================================================
# 公共 API
# ============================================================

def compute_difficulty(gtp_path: str) -> DifficultyResult:
    """
    解析 GTP 文件并计算难度，同时写入缓存

    流程: 查缓存 → 解析 → 写缓存 → 返回
    """
    # 1. 查缓存
    cached = lookup_difficulty(gtp_path)
    if cached is not None:
        return cached

    # 2. 解析
    result = _parse_and_score(gtp_path)

    # 3. 写缓存
    _write_cache(gtp_path, result)
    return result


# ============================================================
# 后台 Worker
# ============================================================

class LoadDifficultyWorkerSignals(QObject):
    """Worker 信号类"""
    one_done = pyqtSignal(str, object)  # path, DifficultyResult
    all_done = pyqtSignal()


class LoadDifficultyWorker(QRunnable):
    """
    后台遍历目录，计算所有 GTP 文件难度

    特点:
      - 继承 QRunnable，由 QThreadPool 调度
      - 每完成一个文件发射 one_done(path, result) 信号
      - 完成后发射 all_done() 信号
      - 支持 cancel() 中断循环
      - 异常静默（单文件失败不影响后续）
    """
    def __init__(self, gtp_files: List[str]):
        super().__init__()
        self.gtp_files = gtp_files
        self.signals = LoadDifficultyWorkerSignals()
        self._cancelled = False

    def cancel(self) -> None:
        """请求取消 — 下一轮循环检查后退出"""
        self._cancelled = True

    def run(self) -> None:
        for path in self.gtp_files:
            if self._cancelled:
                break
            try:
                result = compute_difficulty(path)
            except Exception:
                # 异常静默 (理论上 compute_difficulty 内部已处理)
                result = DifficultyResult(
                    score=0.0, bpm=0, duration_sec=0.0,
                    track_count=0, techniques={}, factors={},
                    error="Unhandled exception"
                )
            try:
                self.signals.one_done.emit(path, result)
            except Exception:
                pass
        try:
            self.signals.all_done.emit()
        except Exception:
            pass
