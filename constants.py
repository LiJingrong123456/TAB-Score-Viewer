# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Constants Module

全局常量定义：路径、文件扩展名、主题颜色、渲染参数等
"""

import os
from typing import Dict, Tuple, List, Any

# ============================================================
# 路径常量
# ============================================================

# 应用基目录（本文件所在目录 = 项目根目录）
_APP_BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

# 配置文件路径
CONFIG_FILE: str = os.path.join(_APP_BASE_DIR, "config", "settings.json")

# 标注数据存储目录
ANNOTATION_DIR: str = os.path.join(_APP_BASE_DIR, "data", "annotations")

# 用户自定义主题目录
CUSTOM_THEMES_DIR: str = os.path.join(_APP_BASE_DIR, "themes")

# 应用图标路径
ICON_PATH: str = os.path.join(_APP_BASE_DIR, "icon.ico")


# ============================================================
# 文件扩展名常量
# ============================================================

# 标注文件扩展名: 与源文件同目录，命名为 {源文件名}.anno.json
ANNOTATION_EXT: str = ".anno.json"

# 支持的图片扩展名
SUPPORTED_IMAGE_EXTENSIONS: Tuple[str, ...] = ('.png', '.jpg', '.jpeg', '.webp')

# 支持的 PDF 扩展名
SUPPORTED_PDF_EXTENSIONS: Tuple[str, ...] = ('.pdf',)

# 支持的 GTP 扩展名
SUPPORTED_GTP_EXTENSIONS: Tuple[str, ...] = ('.gp3', '.gp4', '.gp5', '.gpx', '.gtp', '.gp')

# 所有支持的扩展名
SUPPORTED_ALL_EXTENSIONS: Tuple[str, ...] = SUPPORTED_IMAGE_EXTENSIONS + SUPPORTED_PDF_EXTENSIONS + SUPPORTED_GTP_EXTENSIONS


# ============================================================
# UI 颜色主题 - 深色音乐风格（默认）
# ============================================================

THEME_DARK: Dict[str, str] = {
    'bg_primary': '#121212',
    'bg_secondary': '#1E1E2E',
    'bg_surface': '#252536',
    'bg_card': '#2D2D44',
    'border': '#3A3A4A',
    'text_primary': '#E2E8F0',
    'text_secondary': '#94A3B8',
    'text_muted': '#64748B',
    'primary': '#3B82F6',
    'primary_hover': '#2563EB',
    'primary_light': '#60A5FA',
    'accent': '#F97316',
    'accent_hover': '#EA580C',
    'accent_light': '#FB923C',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
}


# ============================================================
# UI 颜色主题 - 浅色清新风格
# ============================================================

THEME_LIGHT: Dict[str, str] = {
    'bg_primary': '#F8FAFC',
    'bg_secondary': '#F1F5F9',
    'bg_surface': '#FFFFFF',
    'bg_card': '#FFFFFF',
    'border': '#E2E8F0',
    'text_primary': '#1E293B',
    'text_secondary': '#64748B',
    'text_muted': '#94A3B8',
    'primary': '#2563EB',
    'primary_hover': '#1D4ED8',
    'primary_light': '#60A5FA',
    'accent': '#EA580C',
    'accent_hover': '#C2410C',
    'accent_light': '#FDBA74',
    'success': '#059669',
    'warning': '#D97706',
    'danger': '#DC2626',
}

# 向后兼容: 默认引用深色主题
THEME_COLORS: Dict[str, str] = THEME_DARK


# ============================================================
# GTP 渲染参数定义
# ============================================================
# 对应 ApolloTab.utils.constants.RenderConfig
# 每个元组: (类属性名, 中文标签, 类型, 最小值, 最大值, 步长)
# 说明: 修改这些参数后需要重新打开 GTP 文件才能看到效果

_RENDER_PARAMS: List[Tuple[str, str, type, Any, Any, Any]] = [
    ("TAB_LINE_SPACING", "弦线间距 (px)", int, 1, 100, 1),
    ("TAB_LINE_WIDTH_PER_STRING", "每弦水平宽度 (px)", int, 5, 200, 1),
    ("TAB_LINE_THICKNESS", "弦线粗细 (px)", int, 1, 20, 1),
    ("NOTE_FONT_SIZE", "品格数字字号 (px)", int, 4, 64, 1),
    ("NOTE_MIN_SPACING", "相邻拍最小间距 (px)", int, 10, 300, 1),
    ("NOTE_EXTRA_WIDTH_PER_CHAR", "多位数字额外宽度 (px/字符)", int, 0, 50, 1),
    ("STEM_HEIGHT", "符干高度 (px)", int, 5, 120, 1),
    ("STEM_THICKNESS", "符干粗细 (px)", int, 1, 20, 1),
    ("BEAM_HEIGHT", "符尾横杠高度 (px)", int, 1, 60, 1),
    ("BEAM_SLOPE_MAX", "符尾最大斜率", float, 0.0, 2.0, 0.05),
    ("BARLINE_THICKNESS", "小节线粗细 (px)", float, 0.1, 10.0, 0.1),
    ("BARLINE_HEIGHT_EXTEND", "小节线延伸量 (px)", int, 0, 80, 1),
    ("MEASURE_PADDING_LEFT", "小节左侧内边距 (px)", int, 0, 100, 1),
    ("MEASURE_PADDING_RIGHT", "小节右侧内边距 (px)", int, 0, 100, 1),
    ("INFO_SECTION_HEIGHT", "顶部信息区高度 (px)", int, 10, 200, 1),
    ("INFO_FONT_SIZE", "信息文字大小 (px)", int, 4, 64, 1),
    ("TRACK_NAME_FONT_SIZE", "音轨名称字号 (px)", int, 4, 80, 1),
    ("LINE_SPACING", "行间距 (px)", int, 5, 300, 1),
    ("SYSTEM_SPACING", "系统间距 (px)", int, 0, 300, 1),
]


# ============================================================
# 默认值常量
# ============================================================

# 默认 GTP 渲染字体（需要导入 RenderConfig，此处使用占位符，实际值在主模块导入时设置）
_DEFAULT_GTP_FONT: str = "Arial"

# 默认语言
_DEFAULT_LANGUAGE: str = "zh_CN"

# 默认主题
_DEFAULT_THEME: str = "dark"