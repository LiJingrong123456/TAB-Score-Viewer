# -*- coding: utf-8 -*-
"""
============================================================
文件名: note.py
功能描述: 音符(Note)数据模型 - 存储单个音符的完整信息
         包括音高(MIDI)、所在弦、品格数、时值、力度、技巧等

创建日期: 2026-06-06
依赖: Python 3.8+ dataclasses
设计原则: 可扩展 - 通过 techniques 列表支持任意数量技巧标记
============================================================
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from ..utils.constants import TechniqueType, NoteDuration


@dataclass
class GTPNote:
    """
    单个音符的数据模型
    
    属性说明:
      midi_pitch:    MIDI音高值 (0-127), 40=E2(6弦空弦), 64=E4(1弦空弦)
      string:        弦号 (0-5), 0=1弦(最细/高音E), 5=6弦(最粗/低音E)
      fret:          品格数 (0-30), 0=空弦
      velocity:      力度/击弦强度 (0-127), 影响播放音量
      duration:      时值类型 (NoteDuration枚举)
      is_dotted:     是否附点音符 (附点时值 = 原时值 × 1.5)
      techniques:    演奏技巧列表 (可扩展, 支持叠加多个技巧)
      is_ghost:      是否幽灵音(建议弹奏但不强调)
      is_rest:       是否休止符
    """

    midi_pitch: int = 0              # MIDI音高值
    string: int = 0                  # 弦号 (0-5)
    fret: int = 0                    # 品格数
    velocity: int = 95               # 力度 (0-127, 默认95=mf中强)
    duration: NoteDuration = NoteDuration.QUARTER  # 时值
    is_dotted: bool = False          # 是否附点
    techniques: List[TechniqueType] = field(default_factory=list)  # 技巧列表
    is_ghost: bool = False           # 幽灵音标记
    is_rest: bool = False            # 休止符标记

    def get_display_fret(self) -> str:
        """
        获取用于显示的品格文本
        返回: 品格数字字符串，幽灵音用括号包裹
        """
        if self.is_ghost:
            return f"({self.fret})"
        return str(self.fret)

    def has_technique(self, tech_type: TechniqueType) -> bool:
        """检查是否包含指定技巧"""
        return tech_type in self.techniques

    def add_technique(self, tech_type: TechniqueType) -> None:
        """添加技巧（自动去重）"""
        if tech_type not in self.techniques:
            self.techniques.append(tech_type)
