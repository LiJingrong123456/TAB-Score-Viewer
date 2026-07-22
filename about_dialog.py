# -*- coding: utf-8 -*-
"""
TAB Score Viewer - About Dialog

关于对话框：显示软件版本、ApolloTab 版本、作者信息、许可证、检查更新
"""

import os
from typing import Optional

from PyQt5.QtCore import Qt, QThreadPool, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QHBoxLayout,
)

from theme import ThemeManager, get_app_icon, _get_cached_qss
from i18n import I18n
from fonts import get_font_family_css
from update_checker import (
    UpdateCheckWorker,
    UpdateResult,
    UpdateStatus,
)


class AboutDialog(QDialog):
    """
    关于对话框

    功能:
      - 显示软件版本号(从 VERSION 文件读取)
      - 显示 ApolloTab 库版本号
      - 显示作者信息和联系方式
      - 显示许可证和AI辅助声明
      - 一键检查 GitHub Releases 更新（带网络错误处理）
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(I18n.t("about_dialog.window_title"))
        self.setWindowIcon(get_app_icon())
        self.resize(500, 600)

        # 异步更新检查用：缓存工作线程池引用，避免被 GC 导致回调丢失
        self._check_pool = QThreadPool.globalInstance()
        self._check_worker = None  # type: Optional[UpdateCheckWorker]
        self._update_btn = None   # type: Optional[QPushButton]

        self._setup_ui()
        self._apply_theme()

    # ------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------

    def _setup_ui(self) -> None:
        """初始化关于对话框 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 软件标题
        title_label = QLabel("TAB Score Viewer")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 版本信息
        version_layout = QVBoxLayout()
        version_layout.setSpacing(6)

        # 软件版本
        app_version = self._get_app_version()
        app_version_label = QLabel(f"{I18n.t('about_dialog.app_version')}: {app_version}")
        app_version_label.setStyleSheet("font-size: 14px;")
        version_layout.addWidget(app_version_label)

        # ApolloTab 版本
        apollo_version = self._get_apollo_version()
        apollo_version_label = QLabel(f"{I18n.t('about_dialog.apollo_version')}: {apollo_version}")
        apollo_version_label.setStyleSheet("font-size: 14px;")
        version_layout.addWidget(apollo_version_label)

        layout.addLayout(version_layout)
        layout.addSpacing(10)

        # 许可证
        license_label = QLabel(I18n.t("about_dialog.license"))
        license_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(license_label)

        license_text = QLabel(I18n.t("about_dialog.license_text"))
        license_text.setWordWrap(True)
        license_text.setStyleSheet("font-size: 13px; margin-left: 10px;")
        layout.addWidget(license_text)
        layout.addSpacing(10)

        # 作者
        author_label = QLabel(I18n.t("about_dialog.author"))
        author_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(author_label)

        author_text = QLabel(f"{I18n.t('about_dialog.author_name')}\n\n{I18n.t('about_dialog.author_project')}")
        author_text.setWordWrap(True)
        author_text.setStyleSheet("font-size: 13px; margin-left: 10px;")
        layout.addWidget(author_text)
        layout.addSpacing(10)

        # 联系方式
        contact_label = QLabel(I18n.t("about_dialog.contact"))
        contact_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(contact_label)

        contact_text = QLabel(
            f"{I18n.t('about_dialog.contact_email')}\n"
            f"{I18n.t('about_dialog.contact_qq')}\n"
            f"{I18n.t('about_dialog.contact_bilibili')}"
        )
        contact_text.setWordWrap(True)
        contact_text.setStyleSheet("font-size: 13px; margin-left: 10px;")
        layout.addWidget(contact_text)
        layout.addSpacing(10)

        # AI 辅助声明
        ai_label = QLabel(I18n.t("about_dialog.ai_statement"))
        ai_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(ai_label)

        ai_text = QLabel(f"{I18n.t('about_dialog.ai_text_line1')}\n{I18n.t('about_dialog.ai_text_line2')}")
        ai_text.setWordWrap(True)
        ai_text.setStyleSheet("font-size: 13px; margin-left: 10px;")
        layout.addWidget(ai_text)

        layout.addStretch()

        # 底部按钮行: 检查更新 + 关闭
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self._update_btn = QPushButton(I18n.t("about_dialog.check_update_btn"))
        self._update_btn.setToolTip(I18n.t("about_dialog.check_update_tooltip"))
        self._update_btn.clicked.connect(self._on_check_update_clicked)
        self._update_btn.setFixedWidth(160)

        close_btn = QPushButton(I18n.t("about_dialog.close_btn"))
        close_btn.clicked.connect(self.close)
        close_btn.setFixedWidth(120)

        button_row.addStretch()
        button_row.addWidget(self._update_btn)
        button_row.addWidget(close_btn)
        button_row.addStretch()
        layout.addLayout(button_row)

    # ------------------------------------------------------------
    # 更新检查交互
    # ------------------------------------------------------------

    def _on_check_update_clicked(self) -> None:
        """点击「检查更新」按钮: 异步执行检查，按钮置灰避免重复点击"""
        if self._check_worker is not None:
            return  # 已有任务在跑

        self._update_btn.setEnabled(False)
        self._update_btn.setText(I18n.t("about_dialog.check_update_checking"))

        worker = UpdateCheckWorker()
        worker.signals.finished.connect(self._on_check_finished)
        # 兜底信号 - 正常不会触发
        worker.signals.error.connect(self._on_check_error)
        self._check_worker = worker
        self._check_pool.start(worker)

    def _on_check_finished(self, result: UpdateResult) -> None:
        """更新检查完成回调（在主线程派发，Qt 信号跨线程安全）"""
        self._update_btn.setEnabled(True)
        self._update_btn.setText(I18n.t("about_dialog.check_update_btn"))
        self._check_worker = None

        if result.status == UpdateStatus.NEW_VERSION:
            self._show_new_version_dialog(result)
        elif result.status == UpdateStatus.UP_TO_DATE:
            QMessageBox.information(
                self,
                I18n.t("about_dialog.update_up_to_date_title"),
                I18n.t(
                    "about_dialog.update_up_to_date_msg",
                    version=result.current_version,
                ),
            )
        elif result.status == UpdateStatus.NO_RELEASE:
            QMessageBox.information(
                self,
                I18n.t("about_dialog.update_no_release_title"),
                I18n.t("about_dialog.update_no_release_msg"),
            )
        else:  # NETWORK_ERROR - 手动检查必须显式提示
            QMessageBox.warning(
                self,
                I18n.t("about_dialog.update_network_error_title"),
                I18n.t(
                    "about_dialog.update_network_error_msg",
                    error=result.error_message or "Unknown",
                ),
            )

    def _on_check_error(self, msg: str) -> None:
        """兜底错误回调（正常不会触发）"""
        self._update_btn.setEnabled(True)
        self._update_btn.setText(I18n.t("about_dialog.check_update_btn"))
        self._check_worker = None
        QMessageBox.warning(
            self,
            I18n.t("about_dialog.update_network_error_title"),
            I18n.t("about_dialog.update_network_error_msg", error=msg),
        )

    def _show_new_version_dialog(self, result: UpdateResult) -> None:
        """
        弹出"发现新版本"对话框:
          - 顶部显示新版本号
          - 中间一行"打开 Release 页面"按钮(点击用系统默认浏览器打开)
          - 底部确定按钮关闭对话框
        """
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle(I18n.t("about_dialog.update_new_title"))
        box.setText(
            I18n.t(
                "about_dialog.update_new_msg",
                current=result.current_version,
                latest=result.latest_version or "?",
            )
        )
        box.setTextFormat(Qt.PlainText)

        # 「打开 Release 页面」按钮
        open_btn = box.addButton(
            I18n.t("about_dialog.update_open_release_btn"),
            QMessageBox.AcceptRole,
        )
        # 关闭按钮
        close_btn = box.addButton(QMessageBox.Close)
        box.setDefaultButton(close_btn)

        # 点击打开按钮: 用 QDesktopServices 调起系统默认浏览器（跨平台一致）
        def _open_release() -> None:
            url = result.release_url or "https://github.com/Zhuwenqian/TAB-Score-Viewer/releases"
            QDesktopServices.openUrl(QUrl(url))
            box.accept()

        open_btn.clicked.disconnect()
        open_btn.clicked.connect(_open_release)

        box.exec_()

    # ------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------

    def _get_app_version(self) -> str:
        """读取软件版本号"""
        try:
            version_path = os.path.join(os.path.dirname(__file__), "VERSION")
            if os.path.exists(version_path):
                with open(version_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception:
            pass
        return "Unknown"

    def _get_apollo_version(self) -> str:
        """获取 ApolloTab 库版本号"""
        try:
            import ApolloTab
            return getattr(ApolloTab, '__version__', 'Unknown')
        except ImportError:
            return "Not Installed"
        except Exception:
            return "Unknown"

    def _apply_theme(self) -> None:
        """应用当前主题样式到关于对话框"""
        theme_name = ThemeManager.current_name()
        t = ThemeManager.current()
        qss = _get_cached_qss('AboutDialog', theme_name, lambda: f"""
            QDialog {{ background-color: {t['bg_primary']}; color: {t['text_primary']};
                font-family: {get_font_family_css('ui')}; }}
            QLabel {{ color: {t['text_primary']}; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none;
                border-radius: 6px; padding: 8px 20px; font-weight: 500; }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
            QPushButton:pressed {{ background-color: {t['primary']}; }}
            QPushButton:disabled {{ background-color: {t['border']}; color: {t['text_muted']}; }}
        """)
        self.setStyleSheet(qss)
