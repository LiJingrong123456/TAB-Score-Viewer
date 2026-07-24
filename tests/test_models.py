# -*- coding: utf-8 -*-
"""
tests/test_models.py
models.py 单元测试: Annotation / SpeedCurvePoint / SpeedCurveConfig / LoopConfig
"""
from __future__ import annotations

import pytest
from fonts import get_font_family

from models import (
    Annotation,
    SpeedCurvePoint,
    SpeedCurveConfig,
    LoopConfig,
)


# ============================================================
# Annotation
# ============================================================
class TestAnnotation:
    """Annotation dataclass 默认值与字段行为"""

    def test_default_values(self):
        a = Annotation()
        assert a.id == ""
        assert a.x == 0.0
        assert a.y == 0.0
        assert a.text == ""
        assert a.color == "#F97316"
        assert a.font_size == 14
        # 字体族应回退到平台推荐字体, 不为空
        assert a.font_family == get_font_family("ui")
        assert a.is_bold is False
        assert a.background_color == "#00000080"

    def test_custom_values(self):
        a = Annotation(
            id="anno-1",
            x=0.25,
            y=0.5,
            text="技巧: 击勾弦",
            color="#FF0000",
            font_size=18,
            font_family="Consolas",
            is_bold=True,
            background_color="#20202080",
        )
        assert a.id == "anno-1"
        assert a.x == 0.25
        assert a.y == 0.5
        assert a.text == "技巧: 击勾弦"
        assert a.color == "#FF0000"
        assert a.font_size == 18
        assert a.font_family == "Consolas"
        assert a.is_bold is True
        assert a.background_color == "#20202080"

    def test_equality_by_value(self):
        """dataclass 默认 eq=True, 字段全等则实例相等"""
        a1 = Annotation(id="x", text="hi")
        a2 = Annotation(id="x", text="hi")
        assert a1 == a2
        a3 = Annotation(id="x", text="bye")
        assert a1 != a3

    def test_independent_instances(self):
        """default_factory 不会共享可变对象 (虽然 Annotation 全是不可变字段)"""
        a1 = Annotation()
        a2 = Annotation()
        a1.text = "A"
        assert a2.text == ""


# ============================================================
# SpeedCurvePoint
# ============================================================
class TestSpeedCurvePoint:
    def test_default_values(self):
        p = SpeedCurvePoint()
        assert p.position == 0.0
        assert p.speed == 50.0

    def test_custom_values(self):
        p = SpeedCurvePoint(position=75.5, speed=80.0)
        assert p.position == 75.5
        assert p.speed == 80.0


# ============================================================
# SpeedCurveConfig
# ============================================================
class TestSpeedCurveConfig:
    """注意: SpeedCurveConfig 在源码中缺少 @dataclass 装饰器,
    这是一个已知的源码 bug — 通过 __annotations__ 验证默认值会失败。
    本测试用 __annotations__ + class-level 访问来记录当前行为。
    """

    def test_class_annotations_defined(self):
        annotations = getattr(SpeedCurveConfig, "__annotations__", {})
        assert "points" in annotations
        assert "is_enabled" in annotations

    def test_class_level_field_object(self):
        """源码 bug 表现: 访问类属性会拿到 Field 对象而非默认值"""
        # points 类属性是 Field 对象, 不是 list
        cls_attr = vars(SpeedCurveConfig)["points"]
        from dataclasses import Field
        assert isinstance(cls_attr, Field), \
            "源码当前将 points 定义为 Field 但未加 @dataclass 装饰器, 这是已知 bug"

    def test_instantiation_returns_field_objects(self):
        """实例化后, .points 仍是 Field 对象 (源码 bug 表现)"""
        cfg = SpeedCurveConfig()
        from dataclasses import Field
        # points: 用了 field() 但没加 @dataclass, 实例化后仍是 Field 对象
        assert isinstance(cfg.points, Field)
        # is_enabled: 普通类属性赋值, 实例化后是 False (正常)
        assert cfg.is_enabled is False

    def test_default_points_via_class_attribute(self):
        """通过类属性直接调用 default_factory 验证默认点"""
        from dataclasses import fields
        # 因为 SpeedCurveConfig 不是 dataclass, fields() 不可用
        # 只能从类属性手动获取
        cls_attr = vars(SpeedCurveConfig)["points"]
        default_points = cls_attr.default_factory()
        assert len(default_points) == 2
        assert default_points[0].position == 0
        assert default_points[0].speed == 50
        assert default_points[1].position == 100
        assert default_points[1].speed == 50

    def test_default_factory_returns_new_list_each_call(self):
        """default_factory 每次调用都返回新实例 (避免共享可变)"""
        cls_attr = vars(SpeedCurveConfig)["points"]
        factory = cls_attr.default_factory
        list1 = factory()
        list2 = factory()
        list1.append(SpeedCurvePoint(50, 80))
        assert len(list2) == 2  # 未被污染


# ============================================================
# LoopConfig
# ============================================================
class TestLoopConfig:
    def test_default_values(self):
        lc = LoopConfig()
        assert lc.is_enabled is False
        assert lc.loop_type == "none"
        assert lc.start_position == 0.0
        assert lc.end_position == 100.0

    def test_region_loop(self):
        lc = LoopConfig(is_enabled=True, loop_type="region",
                        start_position=25.5, end_position=75.5)
        assert lc.is_enabled
        assert lc.loop_type == "region"
        assert lc.start_position == 25.5
        assert lc.end_position == 75.5
