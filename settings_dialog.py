# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Settings Dialog

设置对话框：语言、主题、UI 字体、GTP 渲染参数
"""

from typing import Optional, Dict

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QLabel,
    QComboBox,
    QFontComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QAbstractButton,
    QCheckBox,
)

from ApolloTab.utils.constants import RenderConfig

from theme import ThemeManager, get_app_icon, _get_cached_qss
from i18n import I18n
from fonts import set_ui_font, get_ui_font_family, get_font_family, get_font_family_css
from constants import (
    _RENDER_PARAMS,
    _DEFAULT_LANGUAGE,
    _DEFAULT_THEME,
    _DEFAULT_GTP_FONT,
)
from config import _DEFAULT_RENDER_VALUES


def _get_selection_window_cls():
    """
    延迟获取主文件中的 SelectionWindow 类
    使用 importlib 实现以避免循环导入与文件名的空格问题
    """
    import importlib
    try:
        mod = importlib.import_module("TAB Score Viewer")
        return getattr(mod, "SelectionWindow", None)
    except Exception:
        return None


class SettingsDialog(QDialog):
    """
    设置对话框

    功能:
      - 集中管理应用常规设置(语言/主题/UI字体)
      - 集中管理 GTP 六线谱渲染参数(字体/线宽/间距等)
      - 支持实时预览主题与 UI 字体, 取消时恢复
      - 支持一键恢复所有设置为出厂默认值
      - 所有设置保存到 config/settings.json

    说明:
      _parent_window 应当是 SelectionWindow 实例，用于保存配置。
      为避免循环导入，类型判断通过 isinstance 实现，导入采用延迟导入。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._parent_window = parent
        self.setWindowTitle(I18n.t("settings_dialog.window_title"))
        self.setWindowIcon(get_app_icon())
        self.resize(560, 520)

        # 记录原始值, 用于取消时恢复主题和 UI 字体预览
        self._original_theme = ThemeManager.current_name()
        self._original_ui_font = get_ui_font_family()

        # 渲染参数控件映射 {属性名: QSpinBox/QDoubleSpinBox}
        self._render_spinboxes: Dict[str, QSpinBox] = {}

        self._setup_ui()
        self._apply_theme()
        self._load_current_values()

    def _setup_ui(self) -> None:
        """初始化设置对话框 UI"""
        main_layout = QVBoxLayout(self)

        # 标签页容器
        self.tabs = QTabWidget()

        # 常规设置页
        self.general_tab = QWidget()
        general_layout = QFormLayout(self.general_tab)
        general_layout.setLabelAlignment(Qt.AlignRight)

        # 语言选择
        self.lang_combo = QComboBox()
        for code, name in I18n.available_languages():
            self.lang_combo.addItem(name, code)
        general_layout.addRow(I18n.t("settings_dialog.language_label"), self.lang_combo)

        # 主题选择
        self.theme_combo = QComboBox()
        for name, display_name in ThemeManager.available_themes():
            self.theme_combo.addItem(display_name, name)
        general_layout.addRow(I18n.t("settings_dialog.theme_label"), self.theme_combo)

        # UI 字体选择
        self.ui_font_combo = QFontComboBox()
        # 仅显示可缩放字体, 保证跨平台一致性
        self.ui_font_combo.setFontFilters(QFontComboBox.ScalableFonts)
        general_layout.addRow(I18n.t("settings_dialog.ui_font_label"), self.ui_font_combo)

        # 启动时检查更新（默认关闭）
        self.check_update_on_startup_cb = QCheckBox(
            I18n.t("settings_dialog.check_update_on_startup_label")
        )
        self.check_update_on_startup_cb.setToolTip(
            I18n.t("settings_dialog.check_update_on_startup_tooltip")
        )
        general_layout.addRow("", self.check_update_on_startup_cb)

        self.tabs.addTab(self.general_tab, I18n.t("settings_dialog.tab_general"))

        # GTP 渲染设置页
        self.gtp_tab = QWidget()
        gtp_layout = QFormLayout(self.gtp_tab)
        gtp_layout.setLabelAlignment(Qt.AlignRight)

        # GTP 渲染字体
        self.gtp_font_combo = QFontComboBox()
        self.gtp_font_combo.setFontFilters(QFontComboBox.ScalableFonts)
        gtp_layout.addRow(I18n.t("settings_dialog.gtp_font_label"), self.gtp_font_combo)

        # 渲染参数分组标签
        render_group = QLabel(I18n.t("settings_dialog.render_params_group"))
        render_group.setStyleSheet("font-weight:bold;margin-top:8px;")
        gtp_layout.addRow(render_group)

        # 渲染参数输入控件
        for attr, label, typ, min_val, max_val, step in _RENDER_PARAMS:
            if typ is int:
                spin = QSpinBox()
                spin.setRange(min_val, max_val)
                spin.setSingleStep(step)
            else:
                spin = QDoubleSpinBox()
                spin.setRange(min_val, max_val)
                spin.setSingleStep(step)
                spin.setDecimals(1 if step >= 0.1 else 2)
            spin.setMinimumWidth(90)
            # 中文 tooltip: 说明参数作用与调整效果
            spin.setToolTip(f"RenderConfig.{attr}: 当前参数控制 {label}。数值越大通常间距/字号越大, 越小越紧凑。")
            gtp_layout.addRow(label, spin)
            self._render_spinboxes[attr] = spin

        self.tabs.addTab(self.gtp_tab, I18n.t("settings_dialog.tab_gtp"))
        main_layout.addWidget(self.tabs)

        # 按钮: 确定 / 取消 / 恢复默认
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.reset_btn = self.button_box.addButton(
            I18n.t("settings_dialog.reset_btn"), QDialogButtonBox.ResetRole
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self._on_reject)
        self.button_box.clicked.connect(self._on_button_clicked)
        main_layout.addWidget(self.button_box)

        # 实时预览连接 (主题和 UI 字体)
        self.theme_combo.currentIndexChanged.connect(self._preview_theme)
        self.ui_font_combo.currentFontChanged.connect(self._preview_ui_font)

    def _apply_theme(self) -> None:
        """
        应用当前主题样式到设置对话框

        性能优化(P0-1): 使用 _get_cached_qss() 缓存QSS字符串。
        """
        theme_name = ThemeManager.current_name()
        t = ThemeManager.current()
        qss = _get_cached_qss('SettingsDialog', theme_name, lambda: f"""
            QDialog {{ background-color: {t['bg_primary']}; color: {t['text_primary']};
                font-family: {get_font_family_css('ui')}; }}
            QLabel {{ color: {t['text_primary']}; font-size: 13px; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none;
                border-radius: 6px; padding: 6px 14px; font-family: {get_font_family_css('ui')}; }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
            QLineEdit, QComboBox, QFontComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {t['bg_surface']}; color: {t['text_primary']};
                border: 1px solid {t['border']}; border-radius: 4px; padding: 4px 8px; }}
            QCheckBox {{ color: {t['text_primary']}; spacing: 6px; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {t['border']};
                border-radius: 3px; background-color: {t['bg_surface']}; }}
            QCheckBox::indicator:checked {{ background-color: {t['primary']};
                border-color: {t['primary']}; }}
            QTabWidget::pane {{ border: 1px solid {t['border']}; background-color: {t['bg_surface']}; }}
            QTabBar::tab {{ background-color: {t['bg_secondary']}; color: {t['text_primary']};
                padding: 6px 14px; margin: 2px; border-radius: 4px; }}
            QTabBar::tab:selected {{ background-color: {t['primary']}; color: white; }}
            QGroupBox {{ color: {t['text_primary']}; border: 1px solid {t['border']}; margin-top: 8px; }}
        """)
        self.setStyleSheet(qss)

    def _load_current_values(self) -> None:
        """从当前配置和 RenderConfig 加载默认值到控件"""
        # 语言
        idx = self.lang_combo.findData(I18n.current_language())
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        # 主题
        idx = self.theme_combo.findData(ThemeManager.current_name())
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        # UI 字体
        ui_font = get_ui_font_family() or get_font_family('ui')
        idx = self.ui_font_combo.findText(ui_font)
        if idx >= 0:
            self.ui_font_combo.setCurrentIndex(idx)
        else:
            self.ui_font_combo.setCurrentText(ui_font)

        # GTP 渲染字体
        gtp_font = getattr(RenderConfig, "NOTE_FONT_FAMILY", "Arial")
        idx = self.gtp_font_combo.findText(gtp_font)
        if idx >= 0:
            self.gtp_font_combo.setCurrentIndex(idx)
        else:
            self.gtp_font_combo.setCurrentText(gtp_font)

        # 渲染参数
        for attr, spin in self._render_spinboxes.items():
            spin.setValue(getattr(RenderConfig, attr))

        # 启动时检查更新
        from config import get_check_update_on_startup
        self.check_update_on_startup_cb.setChecked(get_check_update_on_startup())

    def _refresh_parent_themes(self) -> None:
        """通知父窗口刷新主题（延迟导入避免循环）"""
        SelectionWindow = _get_selection_window_cls()
        if SelectionWindow is None or not isinstance(self._parent_window, SelectionWindow):
            return
        try:
            self._parent_window._apply_theme()
            if self._parent_window.display_window and hasattr(self._parent_window.display_window, '_refresh_theme'):
                self._parent_window.display_window._refresh_theme()
        except Exception:
            pass

    def _preview_theme(self) -> None:
        """主题下拉框变化时实时预览"""
        theme_name = self.theme_combo.currentData()
        if not theme_name or theme_name == ThemeManager.current_name():
            return
        ThemeManager.set_theme(theme_name)
        self._apply_theme()
        self._refresh_parent_themes()

    def _preview_ui_font(self) -> None:
        """UI 字体下拉框变化时实时预览"""
        family = self.ui_font_combo.currentFont().family()
        set_ui_font(family)
        self._apply_theme()
        self._refresh_parent_themes()

    def _on_accept(self) -> None:
        """点击确定: 应用语言、保存所有配置并关闭"""
        # 语言切换
        new_lang = self.lang_combo.currentData()
        if new_lang and new_lang != I18n.current_language():
            I18n.set_language(new_lang)
            QMessageBox.information(
                self,
                I18n.t("settings_window.language_switch_title"),
                I18n.t("settings_window.language_switch_msg")
            )

        # 主题和 UI 字体已在预览时应用, 这里只需要保存
        set_ui_font(self.ui_font_combo.currentFont().family())
        if self.theme_combo.currentData() != ThemeManager.current_name():
            ThemeManager.set_theme(self.theme_combo.currentData())

        # GTP 渲染字体
        RenderConfig.NOTE_FONT_FAMILY = self.gtp_font_combo.currentFont().family()

        # GTP 渲染参数
        for attr, spin in self._render_spinboxes.items():
            setattr(RenderConfig, attr, spin.value())

        # 启动时检查更新
        from config import set_check_update_on_startup
        set_check_update_on_startup(self.check_update_on_startup_cb.isChecked())

        # 保存到 settings.json
        SelectionWindow = _get_selection_window_cls()
        if SelectionWindow and isinstance(self._parent_window, SelectionWindow):
            try:
                self._parent_window.save_config()
            except Exception:
                pass

        self.accept()

    def _on_reject(self) -> None:
        """点击取消: 恢复主题和 UI 字体预览, 放弃其他修改"""
        # 恢复主题
        if ThemeManager.current_name() != self._original_theme:
            ThemeManager.set_theme(self._original_theme)
            self._refresh_parent_themes()

        # 恢复 UI 字体
        set_ui_font(self._original_ui_font)
        self._refresh_parent_themes()

        self.reject()

    def _on_button_clicked(self, button: QAbstractButton) -> None:
        """
        按钮点击统一处理（除确定/取消外的其他按钮）

        参数:
            button: 被点击的按钮对象
        """
        role = self.button_box.buttonRole(button)
        if role == QDialogButtonBox.ResetRole:
            self._reset_defaults()

    def _reset_defaults(self) -> None:
        """恢复所有设置为模块加载时捕获的默认值"""
        reply = QMessageBox.question(
            self,
            I18n.t("settings_dialog.reset_confirm_title"),
            I18n.t("settings_dialog.reset_confirm_msg"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 语言
        idx = self.lang_combo.findData(_DEFAULT_LANGUAGE)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        # 主题
        idx = self.theme_combo.findData(_DEFAULT_THEME)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        # UI 字体 → 平台默认
        default_ui_font = get_font_family('ui')
        idx = self.ui_font_combo.findText(default_ui_font)
        if idx >= 0:
            self.ui_font_combo.setCurrentIndex(idx)
        else:
            self.ui_font_combo.setCurrentText(default_ui_font)

        # GTP 渲染字体
        idx = self.gtp_font_combo.findText(_DEFAULT_GTP_FONT)
        if idx >= 0:
            self.gtp_font_combo.setCurrentIndex(idx)
        else:
            self.gtp_font_combo.setCurrentText(_DEFAULT_GTP_FONT)

        # 渲染数值参数
        for attr, spin in self._render_spinboxes.items():
            spin.setValue(_DEFAULT_RENDER_VALUES.get(attr, 0))

        # 启动时检查更新 → 默认值
        from config import _DEFAULT_CHECK_UPDATE_ON_STARTUP
        self.check_update_on_startup_cb.setChecked(_DEFAULT_CHECK_UPDATE_ON_STARTUP)
