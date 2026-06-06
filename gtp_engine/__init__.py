# -*- coding: utf-8 -*-
"""
============================================================
gtp_engine - Guitar Pro 文件渲染与播放引擎库
============================================================

功能概述:
  本库提供 Guitar Pro (.gp3/.gp4/.gp5/.gpx) 文件的完整解析与渲染能力，
  可作为独立库发布到 PyPI，也可集成到 TAB Score Viewer 主程序中。

核心模块:
  - parser:    GTP文件解析 (PyGuitarPro → 中介数据模型)
  - models:    数据模型定义 (Note/Beat/Measure/Track/Song)
  - renderer:  六线谱渲染引擎 (QPainter → QPixmap)
  - utils:     常量定义与辅助函数

快速开始:
    from gtp_engine.parser import parse_gtp
    from gtp_engine.renderer import render_gtp
    
    # 方式1: 分步操作
    song = parse_gtp("my_song.gp5")
    print(f"标题: {song.title}, 音轨: {song.track_count}")
    
    # 方式2: 一键渲染
    pages = render_gtp("my_song.gp5", track_index=0)
    
依赖库:
  - guitarpro >= 0.11   # Guitar Pro 文件解析（开源项目: pyguitarpro）
  - PyQt5 >= 5.15       # GUI渲染（用于生成QPixmap图像）

版本: v0.1.0 (MVP)
创建日期: 2026-06-06
============================================================
"""

from .parser import GTPParser, parse_gtp
from .models import GTPNote, GTPBeat, GTPMeasure, GTPTrack, GTPSong
from .renderer import TabRenderer, render_gtp, TabLayoutEngine
from .utils import (
    StandardTunings, NoteDuration, TechniqueType,
    RenderConfig, TECHNIQUE_ABBREVIATION, get_string_name
)

__version__ = "0.1.0"
__all__ = [
    # 解析器
    'GTPParser', 'parse_gtp',
    # 数据模型
    'GTPNote', 'GTPBeat', 'GTPMeasure', 'GTPTrack', 'GTPSong',
    # 渲染器
    'TabRenderer', 'render_gtp', 'TabLayoutEngine',
    # 工具
    'StandardTunings', 'NoteDuration', 'TechniqueType',
    'RenderConfig', 'TECHNIQUE_ABBREVIATION', 'get_string_name',
]
