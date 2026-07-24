# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Tuner Module (v2.7.0)

吉他调音器：
  - 录音（sounddevice）+ 自相关基频检测
  - 6 弦标准调（E2 / A2 / D3 / G3 / B3 / E4）
  - 可选琴弦，重点调该弦
  - 6 弦实时灯 + 选中弦指针表盘
  - 三语 UI（i18n.t）

依赖:
  - sounddevice
  - numpy
  - PyQt5
  - i18n
  - theme (ThemeManager 取色)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QWidget, QSizePolicy, QGridLayout, QFrame, QComboBox
)

from i18n import I18n
from theme import ThemeManager


# ============================================================
# 吉他 6 弦标准调 (EADGBE) - 12 平均律, A4=440Hz
# ============================================================
# 公式: f = 440 * 2^((midi - 69) / 12)
# E2=midi 40, A2=midi 45, D3=midi 50, G3=midi 55, B3=midi 59, E4=midi 64

@dataclass(frozen=True)
class StringSpec:
    """一根琴弦的规格"""
    name: str           # 音名 (E2 / A2 / ...)
    midi: int           # MIDI 音符号
    label: str          # UI 显示用 (E2 / A2 / ...)

    @property
    def frequency(self) -> float:
        """A4=440Hz 下的精确频率"""
        return 440.0 * (2.0 ** ((self.midi - 69) / 12.0))

    def cent_offset(self, detected_hz: float) -> float:
        """检测频率相对该弦的偏差（cent, 100 cent = 1 半音）"""
        if detected_hz <= 0:
            return 0.0
        return 1200.0 * math.log2(detected_hz / self.frequency)


GUITAR_STRINGS: List[StringSpec] = [
    StringSpec(name="E2", midi=40, label="E2 (6)"),
    StringSpec(name="A2", midi=45, label="A2 (5)"),
    StringSpec(name="D3", midi=50, label="D3 (4)"),
    StringSpec(name="G3", midi=55, label="G3 (3)"),
    StringSpec(name="B3", midi=59, label="B3 (2)"),
    StringSpec(name="E4", midi=64, label="E4 (1)"),
]

# 调音指示灯: 偏差绝对值小于此值视为"已对准"
IN_TUNE_CENT: float = 5.0
# 偏差绝对值小于此值视为"接近"
CLOSE_CENT: float = 20.0


# ============================================================
# 音名推断（用于无弦选中时的"全音域模式"）
# ============================================================
NOTE_NAMES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def freq_to_note_name(freq_hz: float) -> str:
    """频率 -> 最近音名 (如 A4)"""
    if freq_hz <= 0:
        return "—"
    midi = int(round(69.0 + 12.0 * math.log2(freq_hz / 440.0)))
    midi = max(0, min(127, midi))
    name = NOTE_NAMES_SHARP[midi % 12]
    octave = (midi // 12) - 1
    return f"{name}{octave}"


# ============================================================
# 自相关基频检测
# ============================================================

def detect_pitch(samples, sample_rate: int,
                 min_hz: float = 60.0, max_hz: float = 500.0) -> float:
    """
    自相关法基频检测

    参数:
        samples: 1D 数值数组（float32 / float64）
        sample_rate: 采样率
        min_hz / max_hz: 检测范围

    返回:
        基频 (Hz), 0.0 = 无法检测
    """
    import numpy as np

    if samples is None or len(samples) < 256:
        return 0.0

    # 1) RMS 阈值 - 静音跳过
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    if rms < 0.005:  # ~ -46 dBFS
        return 0.0

    # 2) 截取有效长度
    N = min(len(samples), 4096)
    x = np.asarray(samples[:N], dtype=np.float64)

    # 3) 去直流
    x = x - np.mean(x)

    # 4) 滞后范围
    lag_min = max(2, int(sample_rate / max_hz))
    lag_max = min(N // 2, int(sample_rate / min_hz))
    if lag_max <= lag_min:
        return 0.0

    # 5) 自相关（不带归一化版本即可, 因为我们只比较相对值）
    # autocorr[tau] = sum_{j=0..N-tau-1} x[j] * x[j+tau]
    best_lag = 0
    best_val = 0.0
    for tau in range(lag_min, lag_max + 1):
        # 整段累加 (Numpy 向量化)
        v = float(np.dot(x[:N - tau], x[tau:N]))
        if v > best_val:
            best_val = v
            best_lag = tau

    if best_lag == 0 or best_val <= 0:
        return 0.0

    # 6) 抛物线插值, 提升精度
    # 在 best_lag 邻域取三点, 拟合抛物线顶点
    if best_lag - 1 >= lag_min and best_lag + 1 <= lag_max:
        y_m1 = float(np.dot(x[:N - (best_lag - 1)], x[best_lag - 1:N]))
        y_0 = best_val
        y_p1 = float(np.dot(x[:N - (best_lag + 1)], x[best_lag + 1:N]))
        denom = (y_m1 - 2.0 * y_0 + y_p1)
        if denom != 0.0:
            shift = 0.5 * (y_m1 - y_p1) / denom
            # 限制 shift 在 [-1, 1] 防止数值异常
            shift = max(-1.0, min(1.0, shift))
            refined_lag = best_lag + shift
        else:
            refined_lag = float(best_lag)
    else:
        refined_lag = float(best_lag)

    if refined_lag <= 0:
        return 0.0
    return sample_rate / refined_lag


# ============================================================
# 后台录音线程
# ============================================================

class TunerWorkerSignals(QObject):
    """Worker 信号 (避免 QThread 直接定义 pyqtSignal)"""
    pitch_detected = pyqtSignal(float)     # Hz, 0 = 无效
    rms_changed = pyqtSignal(float)        # 当前 RMS (dBFS)
    error = pyqtSignal(str)                # 录音/设备错误信息


class TunerWorker(QThread):
    """
    后台录音 + 实时基频检测

    设计:
      - 使用 sounddevice.InputStream 回调写入 ring buffer
      - QThread 定时 (每 50ms = 20 fps) 从 ring buffer 取出 2048 样本做检测
      - 信号: pitch_detected(Hz) / rms_changed(dB) / error(msg)
    """

    SAMPLE_RATE = 44100
    CHANNELS = 1
    BLOCK_SIZE = 1024
    ANALYSIS_SIZE = 2048
    ANALYSIS_INTERVAL_MS = 50  # 20 fps

    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = TunerWorkerSignals()
        self._running = False
        self._stream = None
        self._buffer = bytearray()
        self._lock_buf = False  # 简单互斥

    def run(self):
        """线程入口"""
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError as e:
            self.signals.error.emit(
                f"调音器依赖缺失: {e}\n请执行: pip install sounddevice numpy"
            )
            return

        # 找默认输入设备
        try:
            default_in = sd.query_devices(kind='input')
        except Exception as e:
            self.signals.error.emit(f"找不到输入设备: {e}")
            return

        self._buffer = bytearray()
        self._running = True

        def callback(indata, frames, time, status):
            if status:
                # 常见状态: input overflow, 不致命
                pass
            # 拷贝为 bytes 防止引用失效
            self._buffer.extend(bytes(indata))

        try:
            self._stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype='float32',
                blocksize=self.BLOCK_SIZE,
                device=default_in['index'] if 'index' in default_in else None,
                callback=callback,
            )
            self._stream.start()
        except Exception as e:
            self.signals.error.emit(f"无法打开麦克风: {e}")
            return

        # 主循环: 每 ANALYSIS_INTERVAL_MS 跑一次检测
        while self._running:
            self.msleep(self.ANALYSIS_INTERVAL_MS)
            if not self._buffer:
                continue

            try:
                # 取最近 ANALYSIS_SIZE 个样本
                need_bytes = self.ANALYSIS_SIZE * 4  # float32
                if len(self._buffer) > need_bytes * 4:
                    # 限制最大缓冲, 防止堆积
                    self._buffer = self._buffer[-need_bytes * 4:]

                if len(self._buffer) < need_bytes:
                    continue

                # 取出最新的一段
                chunk = self._buffer[-need_bytes:]
                self._buffer = self._buffer[-need_bytes:]

                arr = np.frombuffer(chunk, dtype=np.float32).copy()
                rms = float(np.sqrt(np.mean(arr.astype(np.float64) ** 2)))
                rms_db = 20.0 * math.log10(rms + 1e-12)
                self.signals.rms_changed.emit(rms_db)

                freq = detect_pitch(arr, self.SAMPLE_RATE)
                self.signals.pitch_detected.emit(freq)
            except Exception:
                # 单帧失败不中断线程
                continue

        # 清理
        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
        except Exception:
            pass

    def stop(self):
        """停止线程"""
        self._running = False
        # 不等线程结束, 调用方再 wait()


# ============================================================
# UI 控件
# ============================================================

class TunerDial(QWidget):
    """圆形指针表盘 - 显示选中弦的偏差"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._cent = 0.0          # -50 ~ +50
        self._detected_hz = 0.0
        self._target_hz = 0.0
        self._target_label = "—"

    def update_state(self, cent: float, detected_hz: float,
                     target_hz: float, target_label: str):
        self._cent = max(-50.0, min(50.0, cent))
        self._detected_hz = detected_hz
        self._target_hz = target_hz
        self._target_label = target_label
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        colors = ThemeManager.current()
        w, h = self.width(), self.height()
        cx, cy = w // 2, int(h * 0.55)
        radius = min(w // 2 - 20, cy - 20)

        # ---- 1) 弧形刻度 (从 -50 cent ~ +50 cent, 总 180°) ----
        # 背景
        p.setPen(QPen(QColor(colors['border']), 2))
        p.setBrush(QBrush(QColor(colors['bg_secondary'])))
        p.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        # 内圆
        inner_r = radius - 18
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(colors['bg_surface']))
        p.drawEllipse(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)

        # 刻度线 + 数字 (-50, -25, 0, +25, +50)
        p.setPen(QPen(QColor(colors['text_secondary']), 1))
        for cent_val in (-50, -25, 0, 25, 50):
            angle_deg = -90.0 + (cent_val / 50.0) * 90.0  # -90° = 上, 0°= 右, 走 ±90°
            angle_rad = math.radians(angle_deg)
            x1 = cx + int(math.cos(angle_rad) * (inner_r - 4))
            y1 = cy + int(math.sin(angle_rad) * (inner_r - 4))
            x2 = cx + int(math.cos(angle_rad) * (inner_r - 16))
            y2 = cy + int(math.sin(angle_rad) * (inner_r - 16))
            p.drawLine(x1, y1, x2, y2)

            # 文字
            fm = QFontMetrics(p.font())
            txt = f"{cent_val:+d}"
            tw = fm.horizontalAdvance(txt)
            tx = cx + int(math.cos(angle_rad) * (inner_r - 30)) - tw // 2
            ty = cy + int(math.sin(angle_rad) * (inner_r - 30)) + fm.ascent() // 2
            p.setPen(QColor(colors['text_muted']))
            p.drawText(tx, ty, txt)
            p.setPen(QPen(QColor(colors['text_secondary']), 1))

        # ---- 2) 绿色 "in tune" 区 ( -5 ~ +5 cent ) ----
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(colors['success']))
        # 在 ±5 cent 之间画一个弧形扇区
        in_tune_half_angle = (5.0 / 50.0) * 90.0
        # Qt 不直接画弧形扇区, 用 path
        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(cx, cy)
        # 从 -5 到 +5
        a1 = math.radians(-90.0 - in_tune_half_angle)
        a2 = math.radians(-90.0 + in_tune_half_angle)
        rect = (cx - inner_r + 2, cy - inner_r + 2,
                (inner_r - 2) * 2, (inner_r - 2) * 2)
        # Qt 坐标 y 向下, 角度方向需要 -1
        path.arcTo(*rect, 90.0 + in_tune_half_angle,
                   -(in_tune_half_angle * 2))
        path.closeSubpath()
        p.setOpacity(0.35)
        p.drawPath(path)
        p.setOpacity(1.0)

        # ---- 3) 指针 ----
        if abs(self._cent) <= 50.0 and self._target_hz > 0:
            angle_deg = -90.0 + (self._cent / 50.0) * 90.0
            angle_rad = math.radians(angle_deg)
            # 指针颜色: in-tune=绿, close=黄, far=红
            if abs(self._cent) <= IN_TUNE_CENT:
                ptr_color = QColor(colors['success'])
            elif abs(self._cent) <= CLOSE_CENT:
                ptr_color = QColor(colors['warning'])
            else:
                ptr_color = QColor(colors['danger'])

            p.setPen(QPen(ptr_color, 4, Qt.SolidLine, Qt.RoundCap))
            tip_x = cx + int(math.cos(angle_rad) * (inner_r - 4))
            tip_y = cy + int(math.sin(angle_rad) * (inner_r - 4))
            p.drawLine(cx, cy, tip_x, tip_y)
            p.setBrush(QBrush(ptr_color))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 5, cy - 5, 10, 10)
        else:
            # 无信号 - 灰色圆点
            p.setBrush(QBrush(QColor(colors['text_muted'])))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 5, cy - 5, 10, 10)

        # ---- 4) 中心数字 (cent 偏差) ----
        if self._target_hz > 0 and self._detected_hz > 0:
            cent_text = f"{self._cent:+.1f}"
            cent_sub = "cent"
        else:
            cent_text = "—"
            cent_sub = I18n.t("tuner.no_signal")
        big = QFont(p.font())
        big.setPointSize(22)
        big.setBold(True)
        p.setFont(big)
        p.setPen(QColor(colors['text_primary']))
        fm = QFontMetrics(big)
        tw = fm.horizontalAdvance(cent_text)
        p.drawText(cx - tw // 2, cy + 40, cent_text)

        small = QFont(p.font())
        small.setPointSize(9)
        p.setFont(small)
        p.setPen(QColor(colors['text_secondary']))
        fm2 = QFontMetrics(small)
        tw2 = fm2.horizontalAdvance(cent_sub)
        p.drawText(cx - tw2 // 2, cy + 56, cent_sub)

        # ---- 5) 目标弦标签 (顶部) ----
        if self._target_label != "—":
            top = QFont(p.font())
            top.setPointSize(11)
            top.setBold(True)
            p.setFont(top)
            p.setPen(QColor(colors['primary']))
            fm3 = QFontMetrics(top)
            tw3 = fm3.horizontalAdvance(self._target_label)
            p.drawText(cx - tw3 // 2, 18, self._target_label)

            if self._target_hz > 0:
                target_text = f"{self._target_hz:.2f} Hz"
                p.setPen(QColor(colors['text_secondary']))
                small2 = QFont(p.font())
                small2.setPointSize(9)
                p.setFont(small2)
                fm4 = QFontMetrics(small2)
                tw4 = fm4.horizontalAdvance(target_text)
                p.drawText(cx - tw4 // 2, 36, target_text)


class StringIndicator(QFrame):
    """单根弦的状态指示器 (颜色 + cent 数字)"""

    def __init__(self, string: StringSpec, on_click, parent=None):
        super().__init__(parent)
        self.string = string
        self._on_click = on_click
        self._cent = 0.0
        self._selected = False
        self._has_signal = False
        self.setFrameShape(QFrame.NoFrame)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setMaximumHeight(56)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        # 灯 (颜色块)
        self._light = QLabel()
        self._light.setFixedSize(16, 16)
        self._light.setStyleSheet(
            "background: %s; border-radius: 8px;" % "#64748B"
        )
        layout.addWidget(self._light, 0, Qt.AlignVCenter)

        # 弦名
        self._name_lbl = QLabel(string.label)
        self._name_lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._name_lbl, 0, Qt.AlignVCenter)

        layout.addStretch(1)

        # cent 偏差
        self._cent_lbl = QLabel("—")
        layout.addWidget(self._cent_lbl, 0, Qt.AlignVCenter)

        self._refresh_style()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._refresh_style()

    def set_state(self, cent: float, has_signal: bool):
        self._cent = cent
        self._has_signal = has_signal
        self._refresh_style()

    def _refresh_style(self):
        colors = ThemeManager.current()

        # 背景
        if self._selected:
            bg = colors['primary']
            fg = "#FFFFFF"
            muted_fg = "#FFFFFF"
        else:
            bg = colors['bg_secondary']
            fg = colors['text_primary']
            muted_fg = colors['text_muted']
        self.setStyleSheet(
            f"QFrame {{ background: {bg}; border-radius: 6px; }}"
        )
        self._name_lbl.setStyleSheet(
            f"color: {fg}; font-weight: bold; background: transparent;"
        )

        # 灯颜色
        if not self._has_signal:
            light_color = colors['text_muted']
            cent_text = "—"
            cent_color = muted_fg
        else:
            a = abs(self._cent)
            if a <= IN_TUNE_CENT:
                light_color = colors['success']
            elif a <= CLOSE_CENT:
                light_color = colors['warning']
            else:
                light_color = colors['danger']
            sign = "+" if self._cent >= 0 else ""
            cent_text = f"{sign}{self._cent:.0f}¢"
            cent_color = colors['text_primary'] if self._selected else colors['text_primary']

        self._light.setStyleSheet(
            f"background: {light_color}; border-radius: 8px;"
        )
        self._cent_lbl.setText(cent_text)
        self._cent_lbl.setStyleSheet(
            f"color: {cent_color}; background: transparent; font-family: monospace;"
        )

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton and self._on_click is not None:
            self._on_click(self.string)
        super().mousePressEvent(ev)


# ============================================================
# 主对话框
# ============================================================

class TunerDialog(QDialog):
    """
    调音器主窗口

    用法:
        dlg = TunerDialog(parent)
        dlg.exec_()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(I18n.t("tuner.window_title"))
        self.setMinimumSize(560, 460)
        self.setModal(False)

        # 状态
        self._selected_string: Optional[StringSpec] = None
        self._last_hz: float = 0.0
        self._string_states: dict = {s.name: (0.0, False) for s in GUITAR_STRINGS}
        # 简单平滑 (最近 3 帧频率中位数)
        self._hz_history: List[float] = []
        self._worker: Optional[TunerWorker] = None
        self._error_shown: bool = False

        # UI
        self._build_ui()
        self._apply_theme()
        self._update_selected_string(None)

        # 主题切换响应
        try:
            ThemeManager.theme_changed.connect(self._on_theme_changed)
        except Exception:
            pass

    # ----------------- UI 构建 -----------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        # 顶部: 6 弦状态列表 (3列 2行)
        self._indicators: List[StringIndicator] = []
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, s in enumerate(GUITAR_STRINGS):
            ind = StringIndicator(s, on_click=self._on_string_clicked)
            self._indicators.append(ind)
            grid.addWidget(ind, i // 3, i % 3)
        outer.addLayout(grid)

        # 中央: 表盘
        self._dial = TunerDial()
        outer.addWidget(self._dial, 1)

        # 底部: 控制按钮
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        self._start_btn = QPushButton(I18n.t("tuner.start"))
        self._start_btn.clicked.connect(self._on_start_clicked)
        ctrl.addWidget(self._start_btn)

        self._stop_btn = QPushButton(I18n.t("tuner.stop"))
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        self._stop_btn.setEnabled(False)
        ctrl.addWidget(self._stop_btn)

        ctrl.addStretch(1)

        self._select_combo = QComboBox()
        for s in GUITAR_STRINGS:
            self._select_combo.addItem(s.label, s.name)
        self._select_combo.currentIndexChanged.connect(self._on_combo_changed)
        ctrl.addWidget(QLabel(I18n.t("tuner.target_string") + ":"))
        ctrl.addWidget(self._select_combo)

        outer.addLayout(ctrl)

        # 状态栏
        self._status_lbl = QLabel(I18n.t("tuner.status_idle"))
        self._status_lbl.setStyleSheet("color: gray;")
        outer.addWidget(self._status_lbl)

    def _apply_theme(self):
        colors = ThemeManager.current()
        self.setStyleSheet(f"""
            QDialog {{ background: {colors['bg_primary']}; color: {colors['text_primary']}; }}
            QPushButton {{
                background: {colors['primary']}; color: white;
                border: none; padding: 6px 14px; border-radius: 4px;
            }}
            QPushButton:hover {{ background: {colors['primary_hover']}; }}
            QPushButton:disabled {{ background: {colors['bg_card']}; color: {colors['text_muted']}; }}
            QComboBox {{
                background: {colors['bg_surface']}; color: {colors['text_primary']};
                border: 1px solid {colors['border']}; padding: 4px 8px; border-radius: 3px;
            }}
            QLabel {{ color: {colors['text_primary']}; }}
        """)

    # ----------------- 主题切换 -----------------
    def _on_theme_changed(self, _name: str):
        self._apply_theme()
        for ind in self._indicators:
            ind._refresh_style()
        self._dial.update()

    # ----------------- 选中弦 -----------------
    def _on_string_clicked(self, string: StringSpec):
        self._update_selected_string(string)
        # 同步下拉框
        for i, s in enumerate(GUITAR_STRINGS):
            if s.name == string.name:
                self._select_combo.blockSignals(True)
                self._select_combo.setCurrentIndex(i)
                self._select_combo.blockSignals(False)
                break

    def _on_combo_changed(self, idx: int):
        if idx < 0 or idx >= len(GUITAR_STRINGS):
            return
        self._update_selected_string(GUITAR_STRINGS[idx])

    def _update_selected_string(self, string: Optional[StringSpec]):
        self._selected_string = string
        for ind in self._indicators:
            ind.set_selected(ind.string == string)
        if string is None:
            self._dial.update_state(0.0, 0.0, 0.0, "—")
        else:
            cent = 0.0
            has = self._string_states.get(string.name, (0.0, False))[1]
            if has:
                cent = self._string_states[string.name][0]
            self._dial.update_state(cent, self._last_hz, string.frequency, string.label)

    # ----------------- Worker 控制 -----------------
    def _on_start_clicked(self):
        if self._worker is not None and self._worker.isRunning():
            return
        self._error_shown = False
        self._hz_history.clear()
        self._worker = TunerWorker(self)
        self._worker.signals.pitch_detected.connect(self._on_pitch)
        self._worker.signals.rms_changed.connect(self._on_rms)
        self._worker.signals.error.connect(self._on_worker_error)
        self._worker.start()

        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status_lbl.setText(I18n.t("tuner.status_listening"))
        self._status_lbl.setStyleSheet("color: #10B981;")  # success

    def _on_stop_clicked(self):
        if self._worker is not None:
            self._worker.stop()
            self._worker.wait(2000)
            self._worker = None
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_lbl.setText(I18n.t("tuner.status_stopped"))
        self._status_lbl.setStyleSheet("color: gray;")
        # 清空显示
        for ind in self._indicators:
            ind.set_state(0.0, False)
        self._string_states = {s.name: (0.0, False) for s in GUITAR_STRINGS}
        if self._selected_string is not None:
            self._dial.update_state(0.0, 0.0,
                                    self._selected_string.frequency,
                                    self._selected_string.label)
        else:
            self._dial.update_state(0.0, 0.0, 0.0, "—")

    def closeEvent(self, ev):
        """关闭时停止线程"""
        self._on_stop_clicked()
        super().closeEvent(ev)

    # ----------------- Worker 回调 -----------------
    def _on_pitch(self, hz: float):
        if hz <= 0:
            # 无信号
            self._string_states = {s.name: (0.0, False) for s in GUITAR_STRINGS}
            for ind in self._indicators:
                ind.set_state(0.0, False)
            if self._selected_string is not None:
                self._dial.update_state(0.0, 0.0,
                                        self._selected_string.frequency,
                                        self._selected_string.label)
            else:
                self._dial.update_state(0.0, 0.0, 0.0, "—")
            return

        # 平滑: 中位数过滤
        self._hz_history.append(hz)
        if len(self._hz_history) > 3:
            self._hz_history.pop(0)
        sorted_hz = sorted(self._hz_history)
        hz_smooth = sorted_hz[len(sorted_hz) // 2]
        self._last_hz = hz_smooth

        # 算每根弦的偏差
        for s in GUITAR_STRINGS:
            cent = s.cent_offset(hz_smooth)
            # 只在合理范围内显示 "has_signal"
            # 距离该弦 ±150 cent (1.5 半音) 内认为可能是这根
            has = abs(cent) < 150.0
            self._string_states[s.name] = (cent, has)

        # 更新 6 弦指示器
        for ind in self._indicators:
            cent, has = self._string_states[ind.string.name]
            ind.set_state(cent, has)

        # 更新表盘
        if self._selected_string is not None:
            cent, _ = self._string_states[self._selected_string.name]
            self._dial.update_state(cent, hz_smooth,
                                    self._selected_string.frequency,
                                    self._selected_string.label)
        else:
            # 全音域模式: 显示最近音名
            note = freq_to_note_name(hz_smooth)
            # 找最近的弦做指针（最近弦的 cent 偏差）
            nearest_str = min(GUITAR_STRINGS,
                              key=lambda s: abs(s.cent_offset(hz_smooth)))
            cent = nearest_str.cent_offset(hz_smooth)
            self._dial.update_state(cent, hz_smooth,
                                    nearest_str.frequency,
                                    f"{note} → {nearest_str.label}")

    def _on_rms(self, db: float):
        # 静音时不显示
        if db < -45.0 and self._last_hz > 0:
            self._last_hz = 0.0
            self._on_pitch(0.0)

    def _on_worker_error(self, msg: str):
        if self._error_shown:
            return
        self._error_shown = True
        self._status_lbl.setText(msg)
        self._status_lbl.setStyleSheet("color: #EF4444;")  # danger
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        # 打印到 stderr 便于排错
        import sys
        print(f"[Tuner] {msg}", file=sys.stderr)
