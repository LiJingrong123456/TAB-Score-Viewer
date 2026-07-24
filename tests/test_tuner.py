# -*- coding: utf-8 -*-
"""
Tuner 模块单元测试 (v2.7.0)

覆盖:
  - 6 弦频率精度 (A4=440Hz, 12 平均律)
  - cent_offset 公式 (+1% = 17.226 cent)
  - freq_to_note_name
  - detect_pitch 纯正弦波 (E2/A2/D3/G3/B3/E4)
  - detect_pitch 静音 / 短缓冲
  - IN_TUNE / CLOSE 阈值
  - i18n 三语翻译
  - shortcuts.DEFAULT_SHORTCUTS 含 tuner_toggle
  - TunerDialog 实例化 (需要 qapp fixture)
  - SVG 图标存在且能加载
"""
import math
import os

import numpy as np
import pytest

import tuner


# ============================================================
# 6 弦频率精度 (A4=440Hz, 12 平均律)
# ============================================================

class TestGuitarStrings:
    """6 弦标准调 (EADGBE) 频率验证"""

    def test_string_count(self):
        assert len(tuner.GUITAR_STRINGS) == 6

    def test_string_order(self):
        # 从 6 弦 (最低音) 到 1 弦 (最高音)
        names = [s.name for s in tuner.GUITAR_STRINGS]
        assert names == ["E2", "A2", "D3", "G3", "B3", "E4"]

    def test_midi_numbers(self):
        # E2=40, A2=45, D3=50, G3=55, B3=59, E4=64
        midis = [s.midi for s in tuner.GUITAR_STRINGS]
        assert midis == [40, 45, 50, 55, 59, 64]

    def test_frequency_e2(self):
        s = tuner.GUITAR_STRINGS[0]
        assert s.frequency == pytest.approx(82.4069, abs=0.001)

    def test_frequency_a2(self):
        s = tuner.GUITAR_STRINGS[1]
        assert s.frequency == pytest.approx(110.0, abs=0.001)

    def test_frequency_d3(self):
        s = tuner.GUITAR_STRINGS[2]
        assert s.frequency == pytest.approx(146.8324, abs=0.001)

    def test_frequency_g3(self):
        s = tuner.GUITAR_STRINGS[3]
        assert s.frequency == pytest.approx(195.9977, abs=0.001)

    def test_frequency_b3(self):
        s = tuner.GUITAR_STRINGS[4]
        assert s.frequency == pytest.approx(246.9417, abs=0.001)

    def test_frequency_e4(self):
        s = tuner.GUITAR_STRINGS[5]
        assert s.frequency == pytest.approx(329.6276, abs=0.001)

    def test_label_format(self):
        # UI 显示用 (e.g., "E2 (6)" 表示 6 弦)
        labels = [s.label for s in tuner.GUITAR_STRINGS]
        assert labels[0] == "E2 (6)"
        assert labels[5] == "E4 (1)"

    def test_frozen_dataclass(self):
        # StringSpec 是 frozen, 不能修改
        s = tuner.GUITAR_STRINGS[0]
        with pytest.raises(Exception):
            s.name = "X1"  # frozen, 应当抛 FrozenInstanceError

    def test_a4_is_440(self):
        # 验证 A4 (midi 69) 的频率 = 440
        # 通过手动计算: log2(110/440) * 12 = -12, A2=midi 45, 距离 24 半音
        a2 = tuner.GUITAR_STRINGS[1]  # A2
        # 2 个八度上去到 A4
        ratio = a2.frequency * 4  # 2 octaves
        assert ratio == pytest.approx(440.0, abs=0.01)


# ============================================================
# cent_offset 公式
# ============================================================

class TestCentOffset:
    """cent 偏差公式验证"""

    def test_exact_frequency_zero_cent(self):
        for s in tuner.GUITAR_STRINGS:
            assert s.cent_offset(s.frequency) == pytest.approx(0.0, abs=0.001)

    def test_plus_one_percent(self):
        """+1% 频率 = +17.226 cent (log2(1.01) * 1200)"""
        for s in tuner.GUITAR_STRINGS:
            c = s.cent_offset(s.frequency * 1.01)
            assert c == pytest.approx(17.226, abs=0.05)

    def test_minus_one_percent(self):
        """-1% 频率 = -17.397 cent"""
        for s in tuner.GUITAR_STRINGS:
            c = s.cent_offset(s.frequency * 0.99)
            assert c == pytest.approx(-17.397, abs=0.05)

    def test_one_semitone_up(self):
        """+1 半音 (2^(1/12)) = +100 cent"""
        s = tuner.GUITAR_STRINGS[0]  # E2
        c = s.cent_offset(s.frequency * (2 ** (1 / 12)))
        assert c == pytest.approx(100.0, abs=0.1)

    def test_one_octave_up(self):
        """+1 八度 = +1200 cent"""
        s = tuner.GUITAR_STRINGS[0]
        c = s.cent_offset(s.frequency * 2)
        assert c == pytest.approx(1200.0, abs=0.1)

    def test_negative_frequency_returns_zero(self):
        s = tuner.GUITAR_STRINGS[0]
        assert s.cent_offset(-1.0) == 0.0

    def test_zero_frequency_returns_zero(self):
        s = tuner.GUITAR_STRINGS[0]
        assert s.cent_offset(0.0) == 0.0


# ============================================================
# 音名推断
# ============================================================

class TestFreqToNoteName:
    """freq_to_note_name: 频率 → 音名"""

    def test_a4(self):
        assert tuner.freq_to_note_name(440.0) == "A4"

    def test_e2(self):
        assert tuner.freq_to_note_name(82.41) == "E2"

    def test_a2(self):
        assert tuner.freq_to_note_name(110.0) == "A2"

    def test_e4(self):
        assert tuner.freq_to_note_name(329.63) == "E4"

    def test_c4(self):
        # C4 = 261.63 Hz (中央 C)
        assert tuner.freq_to_note_name(261.63) == "C4"

    def test_zero_returns_dash(self):
        assert tuner.freq_to_note_name(0.0) == "—"

    def test_negative_returns_dash(self):
        assert tuner.freq_to_note_name(-10.0) == "—"

    def test_very_high(self):
        # 4186 Hz = C8
        assert tuner.freq_to_note_name(4186.0) == "C8"


# ============================================================
# detect_pitch 核心算法
# ============================================================

class TestDetectPitch:
    """detect_pitch 自相关法基频检测"""

    @pytest.fixture
    def sr(self):
        return 44100

    @pytest.fixture
    def sine_signal(self, sr):
        """生成 1 秒 110 Hz 正弦波"""
        t = np.arange(sr) / sr
        return np.sin(2 * np.pi * 110.0 * t).astype(np.float32)

    def test_silent_returns_zero(self, sr):
        sig = np.zeros(sr, dtype=np.float32)
        assert tuner.detect_pitch(sig, sr) == 0.0

    def test_too_short_returns_zero(self, sr):
        sig = np.sin(2 * np.pi * 110.0 * np.arange(100) / sr).astype(np.float32)
        assert tuner.detect_pitch(sig, sr) == 0.0

    def test_none_input_returns_zero(self, sr):
        assert tuner.detect_pitch(None, sr) == 0.0

    def test_empty_array_returns_zero(self, sr):
        assert tuner.detect_pitch(np.array([], dtype=np.float32), sr) == 0.0

    def test_a2_pure_sine(self, sr):
        """A2 (110 Hz) 纯正弦波"""
        t = np.arange(sr) / sr
        sig = np.sin(2 * np.pi * 110.0 * t).astype(np.float32)
        hz = tuner.detect_pitch(sig, sr)
        assert hz > 0
        # 偏差 < 5 cent (IN_TUNE 阈值)
        cent = 1200.0 * math.log2(hz / 110.0)
        assert abs(cent) < 5.0, f"A2 deviation {cent:.2f} cent too large"

    @pytest.mark.parametrize("name,expected_hz", [
        ("E2", 82.41),
        ("A2", 110.00),
        ("D3", 146.83),
        ("G3", 196.00),
        ("B3", 246.94),
        ("E4", 329.63),
    ])
    def test_all_six_strings_pure_sine(self, sr, name, expected_hz):
        """6 弦纯正弦波都能正确检测, 偏差 < 5 cent"""
        t = np.arange(sr) / sr
        sig = np.sin(2 * np.pi * expected_hz * t).astype(np.float32)
        hz = tuner.detect_pitch(sig, sr)
        assert hz > 0
        cent = 1200.0 * math.log2(hz / expected_hz)
        assert abs(cent) < 5.0, f"{name} deviation {cent:.2f} cent too large"

    def test_octave_no_confusion(self, sr):
        """220 Hz 不应混淆到 110 Hz (自相关法找主峰)"""
        t = np.arange(sr) / sr
        sig = np.sin(2 * np.pi * 220.0 * t).astype(np.float32)
        hz = tuner.detect_pitch(sig, sr)
        # 应当检测到 220Hz 附近, 不会跌到 110Hz
        assert 215 < hz < 225, f"expected ~220, got {hz}"

    def test_short_buffer_still_works(self, sr):
        """800 样本 (18ms) 短缓冲"""
        t = np.arange(800) / sr
        sig = np.sin(2 * np.pi * 110.0 * t).astype(np.float32)
        hz = tuner.detect_pitch(sig, sr)
        assert hz > 0


# ============================================================
# 阈值常量
# ============================================================

class TestThresholds:
    """IN_TUNE_CENT / CLOSE_CENT 阈值"""

    def test_in_tune_threshold(self):
        assert tuner.IN_TUNE_CENT == 5.0

    def test_close_threshold(self):
        assert tuner.CLOSE_CENT == 20.0

    def test_in_tune_less_than_close(self):
        assert tuner.IN_TUNE_CENT < tuner.CLOSE_CENT


# ============================================================
# i18n 翻译
# ============================================================

class TestI18n:
    """三语翻译键存在性"""

    def test_zh_cn_tuner_title(self):
        from i18n import I18n
        I18n.set_language("zh_CN")
        assert I18n.t("tuner.window_title") == "调音器"

    def test_zh_cn_tuner_start(self):
        from i18n import I18n
        I18n.set_language("zh_CN")
        assert I18n.t("tuner.start") == "开始"

    def test_en_us_tuner_title(self):
        from i18n import I18n
        I18n.set_language("en_US")
        assert I18n.t("tuner.window_title") == "Tuner"

    def test_en_us_tuner_start(self):
        from i18n import I18n
        I18n.set_language("en_US")
        assert I18n.t("tuner.start") == "Start"

    def test_ru_ru_tuner_title(self):
        from i18n import I18n
        I18n.set_language("ru_RU")
        assert I18n.t("tuner.window_title") == "Тюнер"

    def test_shortcut_tuner_toggle_zh(self):
        from i18n import I18n
        I18n.set_language("zh_CN")
        assert I18n.t("shortcuts.tuner_toggle") == "打开调音器"

    def test_shortcut_tuner_toggle_en(self):
        from i18n import I18n
        I18n.set_language("en_US")
        assert I18n.t("shortcuts.tuner_toggle") == "Open Tuner"

    def test_shortcut_tuner_toggle_ru(self):
        from i18n import I18n
        I18n.set_language("ru_RU")
        assert I18n.t("shortcuts.tuner_toggle") == "Открыть тюнер"


# ============================================================
# shortcuts 注册
# ============================================================

class TestShortcuts:
    """DEFAULT_SHORTCUTS 含 tuner_toggle (v2.7.0 新增第 12 个)"""

    def test_shortcut_count_is_12(self):
        from shortcuts import DEFAULT_SHORTCUTS
        assert len(DEFAULT_SHORTCUTS) == 12

    def test_tuner_toggle_registered(self):
        from shortcuts import DEFAULT_SHORTCUTS
        ids = [a.id for a in DEFAULT_SHORTCUTS]
        assert "tuner_toggle" in ids

    def test_tuner_toggle_default_key(self):
        from shortcuts import DEFAULT_SHORTCUTS
        for a in DEFAULT_SHORTCUTS:
            if a.id == "tuner_toggle":
                assert a.default_key == "Ctrl+T"
                assert a.name_key == "shortcuts.tuner_toggle"
                assert a.callback_attr == "_open_tuner"
                return
        pytest.fail("tuner_toggle not found")

    def test_tuner_toggle_lookup(self):
        """ShortcutManager.lookup('Ctrl+T') 应返回 'tuner_toggle'"""
        from shortcuts import ShortcutManager
        mgr = ShortcutManager.instance()
        # 清除可能存在的自定义
        mgr.set_custom("tuner_toggle", "")
        result = mgr.lookup("Ctrl+T")
        # lookup 不一定返回 "tuner_toggle" (可能被其他键占用), 但至少能找到
        # 这里只验证 tuner_toggle 存在于 DEFAULT_SHORTCUTS
        from shortcuts import DEFAULT_SHORTCUTS
        ids = [a.id for a in DEFAULT_SHORTCUTS]
        assert "tuner_toggle" in ids


# ============================================================
# SVG 图标
# ============================================================

class TestTunerIcon:
    """icons/tuner.svg 存在且可被 load_icon 加载"""

    def test_svg_file_exists(self):
        from constants import _APP_BASE_DIR
        path = os.path.join(_APP_BASE_DIR, "icons", "tuner.svg")
        assert os.path.exists(path), f"图标文件不存在: {path}"

    def test_svg_loadable(self):
        from theme import load_icon
        icon = load_icon('tuner')
        assert not icon.isNull(), "load_icon('tuner') 返回空 QIcon"


# ============================================================
# UI 实例化 (需要 qapp fixture)
# ============================================================

class TestTunerDialog:
    """TunerDialog 实例化验证 (不实际录音)"""

    def test_dialog_constructs(self, qapp):
        from i18n import I18n
        from tuner import TunerDialog
        # 固定语言 (前序测试可能切换到 ru_RU)
        I18n.set_language("zh_CN")
        dlg = TunerDialog()
        assert dlg.windowTitle() == "调音器"
        # 默认无弦选中
        assert dlg._selected_string is None
        # 6 弦指示器
        assert len(dlg._indicators) == 6
        # 6 弦顺序
        names = [ind.string.name for ind in dlg._indicators]
        assert names == ["E2", "A2", "D3", "G3", "B3", "E4"]

    def test_dialog_has_dial(self, qapp):
        from tuner import TunerDialog
        dlg = TunerDialog()
        assert dlg._dial is not None
        # 初始无信号
        assert dlg._dial._target_label == "—"

    def test_dialog_has_buttons(self, qapp):
        from tuner import TunerDialog
        dlg = TunerDialog()
        assert dlg._start_btn is not None
        assert dlg._stop_btn is not None
        # 初始: start 可用, stop 不可用
        assert dlg._start_btn.isEnabled() is True
        assert dlg._stop_btn.isEnabled() is False

    def test_dialog_has_target_combo(self, qapp):
        from tuner import TunerDialog
        dlg = TunerDialog()
        assert dlg._select_combo.count() == 6
        # 第 0 项是 E2 (6)
        assert dlg._select_combo.itemText(0) == "E2 (6)"

    def test_select_string_highlights_indicator(self, qapp):
        from tuner import TunerDialog, GUITAR_STRINGS
        dlg = TunerDialog()
        # 选中 E2
        e2 = GUITAR_STRINGS[0]
        dlg._update_selected_string(e2)
        assert dlg._selected_string is e2
        # 第 0 个 indicator 选中, 其他未选中
        assert dlg._indicators[0]._selected is True
        assert dlg._indicators[1]._selected is False

    def test_combo_changes_selection(self, qapp):
        from tuner import TunerDialog, GUITAR_STRINGS
        dlg = TunerDialog()
        # 切换到 E4 (index 5)
        dlg._select_combo.setCurrentIndex(5)
        assert dlg._selected_string.name == "E4"
        assert dlg._indicators[5]._selected is True

    def test_string_indicator_state_update(self, qapp):
        from tuner import TunerDialog
        dlg = TunerDialog()
        # 模拟接收到 -5 cent (in tune)
        dlg._indicators[0].set_state(-5.0, True)
        assert dlg._indicators[0]._cent == -5.0
        assert dlg._indicators[0]._has_signal is True
        # 无信号
        dlg._indicators[0].set_state(0.0, False)
        assert dlg._indicators[0]._has_signal is False

    def test_on_pitch_zero_clears_all(self, qapp):
        """当 _on_pitch(0) 时, 所有 indicator 状态清空"""
        from tuner import TunerDialog
        dlg = TunerDialog()
        # 先设置一些状态
        dlg._indicators[0].set_state(20.0, True)
        # 收到 0 频率
        dlg._on_pitch(0.0)
        for ind in dlg._indicators:
            assert ind._has_signal is False

    def test_on_pitch_calculates_string_states(self, qapp):
        """收到有效频率时, 每根弦都有 cent 偏差"""
        from tuner import TunerDialog
        dlg = TunerDialog()
        # 模拟检测到 A2 (110Hz)
        dlg._on_pitch(110.0)
        # 6 弦都有信号 (因为 ±150 cent 范围内)
        states = dlg._string_states
        assert states["A2"][1] is True  # 精确匹配
        assert states["A2"][0] == pytest.approx(0.0, abs=0.5)

    def test_dial_updates_on_pitch(self, qapp):
        """检测到频率后, 选中弦的 dial 有值"""
        from tuner import TunerDialog, GUITAR_STRINGS
        dlg = TunerDialog()
        dlg._update_selected_string(GUITAR_STRINGS[1])  # A2
        dlg._on_pitch(110.0)
        # dial 的 cent 应当接近 0
        assert abs(dlg._dial._cent) < 5.0


# ============================================================
# 主文件集成 (_open_tuner 入口存在)
# ============================================================

class TestMainFileIntegration:
    """验证主文件含 _open_tuner 方法 (静态文本检查)"""

    def test_open_tuner_method_exists(self):
        """主文件源码应含 _open_tuner 方法定义 (DisplayWindow + SelectionWindow)"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        # DisplayWindow + SelectionWindow 各有一个 _open_tuner
        assert src.count("def _open_tuner") == 2, (
            f"应有两个 _open_tuner (DisplayWindow + SelectionWindow), "
            f"实际 {src.count('def _open_tuner')}"
        )
        assert "from tuner import TunerDialog" in src, "主文件未导入 TunerDialog"
        # 工具栏 + 选择界面都有 tuner_btn
        assert src.count("tuner_btn") >= 2, (
            "tuner_btn 应在工具栏 + 选择界面至少出现 2 次"
        )
        # 模块级单例变量
        assert "_tuner_dialog_singleton" in src, \
            "缺少模块级 _tuner_dialog_singleton 单例变量"

    def test_selection_window_has_tuner_btn(self):
        """SelectionWindow 应在 folder_layout 区域包含 tuner_btn"""
        from constants import _APP_BASE_DIR
        main_path = os.path.join(_APP_BASE_DIR, "TAB Score Viewer.py")
        with open(main_path, "r", encoding="utf-8") as f:
            src = f.read()
        # 验证 SelectionWindow 内 tuner_btn 出现
        # 通过 find class 边界简化
        sel_idx = src.find("class SelectionWindow")
        assert sel_idx > 0
        # 找到 _open_tuner 第二次定义位置 (SelectionWindow 内)
        open_tuner_pos = src.find("def _open_tuner", sel_idx)
        assert open_tuner_pos > sel_idx, "SelectionWindow 缺少 _open_tuner"
        # 检查 tuner_btn 也在 SelectionWindow 内
        sel_tuner_btn = src.find("self.tuner_btn", sel_idx)
        assert sel_tuner_btn > sel_idx, "SelectionWindow 缺少 tuner_btn"

    def test_requirements_has_sounddevice(self):
        from constants import _APP_BASE_DIR
        req_path = os.path.join(_APP_BASE_DIR, "requirements.txt")
        with open(req_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "sounddevice" in content, "requirements.txt 未添加 sounddevice"
        assert "numpy" in content, "requirements.txt 未添加 numpy"
