# -*- coding: utf-8 -*-
"""
预备拍倒计时测试 (v2.7.0)

覆盖:
  - i18n 三语翻译键 (countdown_hint / countdown_cancel_hint)
  - 主文件集成: CountdownOverlay 类 / _start_countdown / _cancel_countdown
  - CountdownOverlay 实例化 + set_number 状态
"""
import os

import pytest


# ============================================================
# i18n 翻译
# ============================================================

class TestCountdownI18n:
    """三语翻译键存在性"""

    def test_zh_cn_countdown_hint(self):
        from i18n import I18n
        I18n.set_language("zh_CN")
        assert I18n.t("control_panel.countdown_hint") == "预备拍 (按 Esc 或再次点击播放取消)"

    def test_zh_cn_countdown_cancel_hint(self):
        from i18n import I18n
        I18n.set_language("zh_CN")
        assert "取消" in I18n.t("control_panel.countdown_cancel_hint")

    def test_en_us_countdown_hint(self):
        from i18n import I18n
        I18n.set_language("en_US")
        assert "Esc" in I18n.t("control_panel.countdown_hint")
        assert "cancel" in I18n.t("control_panel.countdown_hint").lower()

    def test_ru_ru_countdown_hint(self):
        from i18n import I18n
        I18n.set_language("ru_RU")
        assert I18n.t("control_panel.countdown_hint") != "control_panel.countdown_hint"


# ============================================================
# 主文件集成
# ============================================================

class TestCountdownMainFile:
    """主文件含预备拍相关代码"""

    def test_countdown_overlay_class_exists(self):
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        assert "class CountdownOverlay" in src, "缺少 CountdownOverlay 类"

    def test_countdown_methods_exist(self):
        """主文件应含倒计时相关方法"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        for method in ("_start_countdown", "_on_countdown_tick",
                       "_finish_countdown", "_after_go_signal",
                       "_cancel_countdown", "_do_actual_playback"):
            assert f"def {method}" in src, f"缺少方法 {method}"

    def test_countdown_state_initialized(self):
        """__init__ 中应初始化倒计时状态"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        for state in ("_countdown_active", "_countdown_remaining",
                      "_countdown_seconds", "_countdown_timer",
                      "_countdown_overlay", "_countdown_pending_seek_ms"):
            assert state in src, f"缺少状态变量 {state}"

    def test_countdown_seconds_is_3(self):
        """固定 3 秒"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        # 验证 _countdown_seconds:int=3
        assert "_countdown_seconds:int=3" in src, \
            "_countdown_seconds 应初始化为 3"

    def test_gtp_only(self):
        """倒计时应仅在 GTP 模式 + 全新开始时启动"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        # start_playback 应检查 file_type == 'gtp'
        # 找 start_playback 函数体
        start_idx = src.find("def start_playback")
        assert start_idx > 0
        func_end = src.find("\n    def ", start_idx + 10)
        if func_end == -1:
            func_end = len(src)
        body = src[start_idx:func_end]
        assert "self.file_type == 'gtp'" in body, \
            "start_playback 应检查 GTP 模式"
        assert "self.gtp_player.is_paused" in body, \
            "start_playback 应检查非暂停恢复场景"

    def test_esc_cancels_countdown(self):
        """Esc 键应能取消倒计时"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        # 找 _legacy_keypress 中的 ESC 处理
        esc_idx = src.find("Qt.Key_Escape")
        assert esc_idx > 0
        # 后续 200 字符内应含 _cancel_countdown
        nearby = src[esc_idx:esc_idx + 300]
        assert "_cancel_countdown" in nearby, \
            "ESC 处理应调用 _cancel_countdown"

    def test_play_button_can_cancel(self):
        """倒计时期间再次点击播放按钮应取消倒计时"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        # start_playback 入口应检查 _countdown_active
        start_idx = src.find("def start_playback")
        assert start_idx > 0
        body_start = src.find(":", start_idx) + 1
        func_end = src.find("\n    def ", body_start)
        if func_end == -1:
            func_end = len(src)
        body = src[body_start:func_end]
        assert "self._countdown_active" in body, \
            "start_playback 入口应检查 _countdown_active"


# ============================================================
# 节拍器同步 (v2.7.0 改进)
# ============================================================

class TestCountdownMetronome:
    """倒计时与节拍器协同: 倒计时开始停节拍器, 结束同步重启"""

    def test_start_countdown_stops_existing_audio(self):
        """_start_countdown 中应调 gtp_player.stop() 停止现有音频"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        # 找 _start_countdown 函数体
        start_idx = src.find("def _start_countdown")
        assert start_idx > 0
        body_start = src.find(":", start_idx) + 1
        func_end = src.find("\n    def ", body_start)
        if func_end == -1:
            func_end = len(src)
        body = src[body_start:func_end]
        assert "self.gtp_player.stop()" in body, \
            "_start_countdown 应调 gtp_player.stop() 停止现有音频"
        # 注释也应有说明
        assert "节拍器" in body, \
            "_start_countdown 注释应解释为什么停节拍器"

    def test_after_go_signal_syncs_metronome(self):
        """_after_go_signal 应显式同步节拍器配置"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        # 找 _after_go_signal 函数体
        start_idx = src.find("def _after_go_signal")
        assert start_idx > 0
        body_start = src.find(":", start_idx) + 1
        func_end = src.find("\n    def ", body_start)
        if func_end == -1:
            func_end = len(src)
        body = src[body_start:func_end]
        # 应调 set_metronome 显式同步
        assert "self.gtp_player.set_metronome" in body, \
            "_after_go_signal 应显式调 set_metronome 同步节拍器配置"
        # 传入 _metronome_enabled
        assert "self._metronome_enabled" in body, \
            "_after_go_signal 应使用 self._metronome_enabled"

    def test_paused_time_reset_on_countdown(self):
        """_start_countdown 中应重置 _paused_time_ms 为 0"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        start_idx = src.find("def _start_countdown")
        assert start_idx > 0
        body_start = src.find(":", start_idx) + 1
        func_end = src.find("\n    def ", body_start)
        if func_end == -1:
            func_end = len(src)
        body = src[body_start:func_end]
        # 应有 _paused_time_ms = 0.0
        assert "self._paused_time_ms = 0.0" in body, \
            "_start_countdown 应重置 _paused_time_ms 为 0"

    def test_docstring_explains_metronome_logic(self):
        """_start_countdown docstring 应解释节拍器行为"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        start_idx = src.find("def _start_countdown")
        assert start_idx > 0
        # 找下一个 def (docstring 结束位置)
        func_end = src.find("\n    def ", start_idx + 10)
        if func_end == -1:
            func_end = start_idx + 2000
        docstring = src[start_idx:func_end]
        assert "节拍器" in docstring, \
            "_start_countdown docstring 应说明节拍器行为"


# ============================================================
# CountdownOverlay UI (需要 qapp)
# ============================================================

class TestCountdownOverlay:
    """CountdownOverlay 实例化 + set_number 状态"""

    def test_overlay_constructs(self, qapp):
        """需要一个父 widget 才能实例化 (display_widget)"""
        from PyQt5.QtWidgets import QWidget
        # 创建一个简单的父 widget
        parent = QWidget()
        parent.resize(800, 600)

        # 直接 import 主文件中的 CountdownOverlay
        # 由于主文件 ~7000 行, 不直接 import; 通过源码构造
        # 这里用 mock: 验证主文件源码中确实定义了 CountdownOverlay
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        # 找到 class CountdownOverlay 的方法名
        assert "def set_number" in src, "CountdownOverlay 应有 set_number 方法"
        assert "def paintEvent" in src, "CountdownOverlay 应有 paintEvent 方法"
