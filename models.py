# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Models Module

数据模型定义：标注、速度曲线、循环配置
"""

from dataclasses import dataclass, field
from typing import List

from fonts import get_font_family


@dataclass
class Annotation:
    """文本标注数据模型 - 存储谱面上的文字说明"""
    id: str = ""
    x: float = 0.0          # X坐标比例 (0-1)
    y: float = 0.0          # Y坐标比例 (0-1)
    text: str = ""          # 标注文本内容
    color: str = "#F97316"  # 标注颜色
    font_size: int = 14     # 字体大小(px)
    font_family: str = field(default_factory=lambda: get_font_family("ui"))  # 默认使用平台推荐UI字体
    is_bold: bool = False
    background_color: str = "#00000080"


@dataclass
class SpeedCurvePoint:
    """速度曲线控制点

    position: 位置百分比 (0-100)，表示在播放进度的哪个位置
    speed: 速度倍率基准值 (建议范围25-120)
           实际播放速度 = base_speed * (speed / 50)
           speed=50 → 与base_speed相同(1倍速，基准)
           speed>50 → 比base_speed慢(总时长更长)
           speed<50 → 比base_speed快(总时长更短)
    """
    position: float = 0.0   # 位置百分比 (0-100)
    speed: float = 50.0     # 速度倍率基准值(见类注释)


class SpeedCurveConfig:
    """速度曲线配置"""
    points: List[SpeedCurvePoint] = field(default_factory=lambda: [
        SpeedCurvePoint(0, 50), SpeedCurvePoint(100, 50)  # 默认线性匀速曲线
    ])
    is_enabled: bool = False


@dataclass
class LoopConfig:
    """循环播放配置"""
    is_enabled: bool = False
    loop_type: str = "none"  # none/all/region
    start_position: float = 0.0
    end_position: float = 100.0
