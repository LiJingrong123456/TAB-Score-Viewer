# -*- coding: utf-8 -*-
"""
============================================================
文件名: layout_engine.py
功能描述: 六线谱布局引擎 - 计算所有小节/拍/音符的屏幕坐标
         负责自动换行、分页、宽度分配等核心布局算法

原理:
  将音轨的所有小节按顺序排列，根据画布宽度自动换行。
  每行称为一个"System"（系统），包含若干个连续的小节。
  每个小节内的拍按时间比例分配水平空间。

依赖库:
  - 内部依赖: gtp_engine.models.*, gtp_engine.utils.constants

创建日期: 2026-06-06
============================================================
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from ..models.track import GTPTrack
from ..models.measure import GTPMeasure
from ..models.beat import GTPBeat
from ..utils.constants import RenderConfig


# ============================================================
# 布局数据结构
# ============================================================

@dataclass
class BeatLayout:
    """
    单个拍(Beat)的布局位置
    
    属性:
      beat:        原始拍数据
      x_center:    该拍的中心X坐标（音符绘制基准点）
      x_start:     该拍的起始X坐标
      x_end:       该拍的结束X坐标
    """
    beat: GTPBeat
    x_center: int = 0
    x_start: int = 0
    x_end: int = 0


@dataclass
class MeasureLayout:
    """
    单个小节的布局位置
    
    属性:
      measure:     原始小芽数据
      x_start:     小节左边界X坐标
      x_end:       小节右边界X坐标
      beats:       该小节内各拍的布局列表
    """
    measure: GTPMeasure
    x_start: int = 0
    x_end: int = 0
    beats: List[BeatLayout] = field(default_factory=list)


@dataclass
class SystemLayout:
    """
    一行六线谱(系统)的布局 - 可包含多个连续小节
    
    属性:
      y_top:          该行顶部Y坐标（信息区下方）
      y_bottom:       该行底部Y坐标（含符干符尾空间）
      y_tab_top:      六线谱区域顶部Y（第1弦线位置）
      y_tab_bottom:   六线谱区域底部Y（第6弦线位置）
      measures:       该行包含的小节布局列表
    """
    y_top: int = 0
    y_bottom: int = 0
    y_tab_top: int = 0
    y_tab_bottom: int = 0
    measures: List[MeasureLayout] = field(default_factory=list)


@dataclass
class PageLayout:
    """
    一页乐谱的布局 - 包含多行系统
    
    属性:
      page_number:    页码
      systems:        该页包含的系统(行)列表
      height:         该页总高度(px)
    """
    page_number: int = 0
    systems: List[SystemLayout] = field(default_factory=list)
    height: int = 0


# ============================================================
# 布局引擎主类
# ============================================================

class TabLayoutEngine:
    """
    六线谱布局引擎
    
    功能:
      1. 计算每个小节在每行中的水平位置
      2. 自动换行：当一行放不下更多小节时换到下一行
      3. 分页：当一页放不下更多行时分到下一页
      4. 为每个拍计算精确的X坐标
    
    用法:
        engine = TabLayoutEngine()
        pages = engine.layout(track, page_width=900, page_height=1200)
    """

    def __init__(self, config: Optional[RenderConfig] = None):
        """
        初始化布局引擎
        
        参数:
            config: 渲染配置，None时使用默认配置
        """
        self.cfg = config or RenderConfig()

    def layout(self, track: GTPTrack, 
               page_width: int = None, 
               page_height: int = None) -> List[PageLayout]:
        """
        对整条轨道进行完整布局计算
        
        参数:
            track:        要布局的音轨数据
            page_width:   每页宽度(px)，None则使用配置默认值
            page_height:  每页高度(px)，None则使用配置默认值
            
        返回:
            页面布局列表，每页包含多个系统(行)
        """
        pw = page_width or self.cfg.PAGE_WIDTH_PX
        ph = page_height or self.cfg.PAGE_HEIGHT_PX
        
        # 可用绘图区域（去除左右边距）
        usable_width = pw - self.cfg.PAGE_MARGIN_LEFT - self.cfg.PAGE_MARGIN_RIGHT
        
        # 第一步：将所有小节按行分组（自动换行）
        systems_raw = self._group_measures_into_systems(track.measures, usable_width)
        
        # 第二步：为每个系统分配精确坐标
        systems = self._assign_system_coordinates(
            systems_raw, 
            self.cfg.PAGE_MARGIN_LEFT,
            self.cfg.PAGE_MARGIN_TOP,
            usable_width
        )
        
        # 第三步：按页面高度分页
        pages = self._split_into_pages(systems, ph)
        
        return pages

    def _group_measures_into_systems(self, measures: List[GTPMeasure], 
                                      usable_width: int) -> List[List[GTPMeasure]]:
        """
        将小节分组到各行中（自动换行算法）
        
        算法: 贪心策略 - 尝试将每个小节放入当前行，
              如果当前行的剩余空间不够放下该小节的最小宽度，则换行。
        
        参数:
            measures:     所有小节列表
            usable_width: 可用绘图宽度
            
        返回:
            二维列表，每个内层列表代表一行的所有小节
        """
        if not measures:
            return [[]]
        
        rows: List[List[GTPMeasure]] = []
        current_row: List[GTPMeasure] = []
        current_width = 0
        
        # 每个小节的最小宽度 = 左右内边距 + 至少一个音符的空间
        min_measure_width = (
            self.cfg.MEASURE_PADDING_LEFT + 
            self.cfg.MEASURE_PADDING_RIGHT + 
            self.cfg.NOTE_MIN_SPACING
        )
        
        for measure in measures:
            # 估算该小节需要的宽度（基于拍的数量和平均间距）
            measure_width = self._estimate_measure_width(measure)
            
            # 检查是否需要换行
            if current_row and current_width + measure_width > usable_width:
                # 当前行已满，开始新行
                rows.append(current_row)
                current_row = [measure]
                current_width = measure_width
            else:
                # 放入当前行
                current_row.append(measure)
                current_width += measure_width
        
        # 处理最后一行
        if current_row:
            rows.append(current_row)
        
        return rows if rows else [[]]

    def _estimate_measure_width(self, measure: GTPMeasure) -> int:
        """
        估算一个小节的像素宽度
        
        算法: 基于拍数量 × 最小间距 + 左右边距
              多位数品格数字会额外占用空间
        """
        base_width = self.cfg.MEASURE_PADDING_LEFT + self.cfg.MEASURE_PADDING_RIGHT
        
        if not measure.beats:
            return base_width + self.cfg.NOTE_MIN_SPACING * 4  # 空小节给基本空间
        
        # 统计总拍数和额外字符数
        total_beats = len(measure.beats)
        extra_chars = 0
        for beat in measure.beats:
            for note in beat.notes:
                if note.fret >= 10:
                    extra_chars += 1  # 双位数品格额外占位
                if note.fret >= 100:
                    extra_chars += 1  # 三位数再额外占位
        
        width = base_width + total_beats * self.cfg.NOTE_MIN_SPACING
        width += extra_chars * self.cfg.NOTE_EXTRA_WIDTH_PER_CHAR
        
        return max(width, 60)  # 最小60px保证可读性

    def _assign_system_coordinates(self, rows: List[List[GTPMeasure]],
                                    start_x: int, start_y: int,
                                    usable_width: int) -> List[SystemLayout]:
        """
        为每个系统和其中的小节/拍分配精确坐标
        
        参数:
            rows:          按行分组的小节二维列表
            start_x:       起始X坐标
            start_y:       起始Y坐标（第一行顶部）
            usable_width:  可用宽度
            
        返回:
            SystemLayout 列表，每个元素包含完整的坐标信息
        """
        systems: List[SystemLayout] = []
        current_y = start_y
        
        # 六线谱高度 = (弦数-1) × 弦间距
        tab_height = (6 - 1) * self.cfg.TAB_LINE_SPACING
        # 一行总高度 = 六线谱高度 + 符干空间 + 行间距
        row_total_height = tab_height + self.cfg.STEM_HEIGHT + self.cfg.LINE_SPACING
        
        for row_idx, row_measures in enumerate(rows):
            # 创建系统布局
            system = SystemLayout()
            system.y_top = current_y
            system.y_tab_top = current_y + self.cfg.INFO_SECTION_HEIGHT
            system.y_tab_bottom = system.y_tab_top + tab_height
            system.y_bottom = system.y_tab_bottom + self.cfg.STEM_HEIGHT + 8
            
            current_x = start_x
            
            for measure in row_measures:
                # 创建小节布局
                m_layout = MeasureLayout(measure=measure)
                m_layout.x_start = current_x
                
                # 在小节内分配各拍的X坐标
                current_x = self._distribute_beats_in_measure(
                    measure, m_layout, 
                    current_x + self.cfg.MEASURE_PADDING_LEFT,
                    usable_width
                )
                
                m_layout.x_end = current_x + self.cfg.MEASURE_PADDING_RIGHT
                system.measures.append(m_layout)
                
                current_x = m_layout.x_end
            
            systems.append(system)
            current_y = system.y_bottom + self.cfg.SYSTEM_SPACING
        
        return systems

    def _distribute_beats_in_measure(self, measure: GTPMeasure,
                                      m_layout: MeasureLayout,
                                      start_x: int,
                                      usable_width: int) -> int:
        """
        在一个小节内均匀分布各拍的X坐标
        
        参数:
            measure:    小节数据
            m_layout:   小节布局对象（结果写入此处）
            start_x:    小节内第一个拍的起始X
            usable_width: 总可用宽度（用于参考）
            
        返回:
            最后一个拍的结束X坐标
        """
        if not measure.beats:
            return start_x + self.cfg.NOTE_MIN_SPACING
        
        # 计算该小节的可用内部宽度
        inner_width = self._estimate_measure_width(measure)
        inner_width -= (
            self.cfg.MEASURE_PADDING_LEFT + self.cfg.MEASURE_PADDING_RIGHT
        )
        
        # 基于时值比例分配宽度（时长越长的拍占越多空间）
        total_duration = sum(b.duration_value for b in measure.beats)
        if total_duration <= 0:
            total_duration = len(measure.beats)  # 回退: 均匀分配
        
        current_x = start_x
        for beat in measure.beats:
            # 该拍占用的宽度比例
            ratio = beat.duration_value / total_duration
            beat_width = max(int(inner_width * ratio), self.cfg.NOTE_MIN_SPACING)
            
            bl = BeatLayout(beat=beat)
            bl.x_center = current_x + beat_width // 2
            bl.x_start = current_x
            bl.x_end = current_x + beat_width
            m_layout.beats.append(bl)
            
            current_x += beat_width
        
        return current_x

    def _split_into_pages(self, systems: List[SystemLayout],
                           page_height: int) -> List[PageLayout]:
        """
        将系统列表按页面高度分页
        
        参数:
            systems:     所有系统的布局列表
            page_height: 每页可用高度
            
        返回:
            PageLayout 列表
        """
        if not systems:
            return []
        
        pages: List[PageLayout] = []
        current_page = PageLayout(page_number=len(pages) + 1)
        
        # 第一页顶部留出边距
        used_height = self.cfg.PAGE_MARGIN_TOP
        
        for system in systems:
            system_height = system.y_bottom - system.y_top + self.cfg.LINE_SPACING
            
            # 检查是否需要分页
            if used_height + system_height > page_height - self.cfg.PAGE_MARGIN_BOTTOM:
                # 当前页已满，保存并创建新页
                current_page.height = used_height
                pages.append(current_page)
                current_page = PageLayout(page_number=len(pages) + 1)
                used_height = self.cfg.PAGE_MARGIN_TOP
            
            current_page.systems.append(system)
            used_height += system_height
        
        # 处理最后一页
        if current_page.systems:
            current_page.height = used_height + self.cfg.PAGE_MARGIN_BOTTOM
            pages.append(current_page)
        
        return pages
