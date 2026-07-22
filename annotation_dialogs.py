# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Annotation Dialogs

标注相关的三个对话框：新建 / 编辑 / 管理
"""

import uuid
from typing import List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTextEdit,
    QSpinBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QColorDialog,
    QMessageBox,
)

from models import Annotation
from theme import ThemeManager
from i18n import I18n
from fonts import get_font_family_css


class AnnotationCreateDialog(QDialog):
    """
    新建标注对话框 - 专门用于创建新标注(无删除功能)

    与AnnotationEditDialog的区别:
      - 标题: "新建标注" vs "编辑标注"
      - 无删除按钮(新标注不存在删除概念)
      - 只有 [确定] [取消] 两个按钮

    调用方式:
      dialog = AnnotationCreateDialog(parent, x, y)
      if dialog.exec_() == QDialog.Accepted:
          ann = dialog.get_annotation()  # 获取新建的标注
    """

    def __init__(self, parent=None, x: float = 0.1, y: float = 0.1):
        super().__init__(parent)
        self.annotation = Annotation(
            id=f"ann_{uuid.uuid4().hex[:8]}", x=x, y=y,
            text=I18n.t("annotation_create.default_text")
        )
        self._temp_color = self.annotation.color
        self.init_ui()

    def init_ui(self) -> None:
        """初始化标注编辑对话框UI - 从ThemeManager读取当前主题"""
        self.setWindowTitle(I18n.t("annotation_create.window_title"))
        self.setFixedSize(420, 360)
        t = ThemeManager.current()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {t['bg_primary']}; }}
            QLabel {{ color: {t['text_primary']}; font-family: {get_font_family_css('ui')}; }}
            QTextEdit {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 6px; padding: 6px; }}
            QSpinBox {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 4px; padding: 4px; }}
            QCheckBox {{ color: {t['text_primary']}; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none;
                           border-radius: 6px; padding: 8px 20px; font-family: {get_font_family_css('ui')}; }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
        """)
        layout = QVBoxLayout(self)

        # 位置信息(只读显示)
        pg = QGroupBox(I18n.t("annotation_create.position_group"))
        pl = QHBoxLayout(pg)
        pl.addWidget(QLabel(I18n.t("annotation_create.coord_display", x=self.annotation.x, y=self.annotation.y)))
        layout.addWidget(pg)

        # 标注内容
        tg = QGroupBox(I18n.t("annotation_create.content_group"))
        tl = QVBoxLayout(tg)
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.annotation.text)
        self.text_edit.setPlaceholderText(I18n.t("annotation_create.placeholder"))
        tl.addWidget(self.text_edit)
        layout.addWidget(tg)

        # 字体设置
        fg = QGroupBox(I18n.t("annotation_create.font_group"))
        fl = QHBoxLayout(fg)
        fl.addWidget(QLabel(I18n.t("annotation_create.size_label")))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.annotation.font_size)
        fl.addWidget(self.font_size_spin)
        self.bold_check = QCheckBox(I18n.t("annotation_create.bold_check"))
        self.bold_check.setChecked(self.annotation.is_bold)
        fl.addWidget(self.bold_check)
        fl.addStretch()
        layout.addWidget(fg)

        # 颜色选择
        cg = QGroupBox(I18n.t("annotation_create.color_group"))
        cl = QHBoxLayout(cg)
        self.color_btn = QPushButton(I18n.t("annotation_create.color_btn"))
        self.color_btn.clicked.connect(self._pick_color)
        self.color_btn.setStyleSheet(f"background-color:{self.annotation.color};color:white;")
        cl.addWidget(self.color_btn)
        cl.addStretch()
        layout.addWidget(cg)

        # 按钮区域: 确定 / 取消 (无删除按钮，因为是新建)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(I18n.t("annotation_create.create_btn"))
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton(I18n.t("annotation_create.cancel_btn"))
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            f"background-color:{ThemeManager.get('bg_surface', '#252536')};"
            f"color:{ThemeManager.get('text_secondary', '#94A3B8')};"
        )
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _pick_color(self) -> None:
        c = QColorDialog.getColor(self._temp_color or Qt.white, self, I18n.t("annotation_create.color_dialog_title"))
        if c.isValid():
            self._temp_color = c.name()
            self.color_btn.setStyleSheet(f"background-color:{self._temp_color};color:white;")

    def get_annotation(self) -> Annotation:
        """获取用户输入的标注数据"""
        self.annotation.text = self.text_edit.toPlainText()
        self.annotation.font_size = self.font_size_spin.value()
        self.annotation.is_bold = self.bold_check.isChecked()
        self.annotation.color = self._temp_color
        return self.annotation


class AnnotationEditDialog(QDialog):
    """
    编辑标注对话框 - 专门用于编辑已有标注(含删除功能)

    与AnnotationCreateDialog的区别:
      - 标题: "编辑标注" vs "新建标注"
      - 有删除按钮(🗑 删除此标注)
      - 按钮布局: [确定保存] [🗑 删除此标注] [取消]
      - 返回 should_delete 标记告知调用方是否执行删除

    调用方式:
      dialog = AnnotationEditDialog(parent, annotation)
      if dialog.exec_() == QDialog.Accepted:
          if dialog.should_delete:  # 用户点击了删除
              # 执行删除逻辑
          else:
              ann = dialog.get_annotation()  # 获取修改后的标注
    """

    def __init__(self, parent=None, annotation: Optional[Annotation] = None):
        super().__init__(parent)
        self.annotation = annotation or Annotation(
            id=f"ann_{uuid.uuid4().hex[:8]}", x=0.1, y=0.1,
            text=I18n.t("annotation_edit.default_text")
        )
        self._temp_color = self.annotation.color
        self.should_delete = False  # 标记用户是否点击了删除按钮
        self.init_ui()

    def init_ui(self) -> None:
        """初始化标注编辑对话框UI(编辑模式) - 从ThemeManager读取当前主题"""
        self.setWindowTitle(I18n.t("annotation_edit.window_title"))
        self.setFixedSize(420, 400)
        t = ThemeManager.current()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {t['bg_primary']}; }}
            QLabel {{ color: {t['text_primary']}; font-family: {get_font_family_css('ui')}; }}
            QTextEdit {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 6px; padding: 6px; }}
            QSpinBox {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 4px; padding: 4px; }}
            QCheckBox {{ color: {t['text_primary']}; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none;
                           border-radius: 6px; padding: 8px 20px; font-family: {get_font_family_css('ui')}; }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
            QPushButton#deleteBtn {{ background-color: {ThemeManager.get('danger', '#EF4444')}; }}
            QPushButton#deleteBtn:hover {{ background-color: #DC2626; }}
        """)
        layout = QVBoxLayout(self)

        pg = QGroupBox(I18n.t("annotation_edit.position_group"))
        pl = QHBoxLayout(pg)
        pl.addWidget(QLabel(I18n.t("annotation_edit.coord_display", x=self.annotation.x, y=self.annotation.y)))
        layout.addWidget(pg)

        tg = QGroupBox(I18n.t("annotation_edit.content_group"))
        tl = QVBoxLayout(tg)
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.annotation.text)
        self.text_edit.setPlaceholderText(I18n.t("annotation_edit.placeholder"))
        tl.addWidget(self.text_edit)
        layout.addWidget(tg)

        fg = QGroupBox(I18n.t("annotation_edit.font_group"))
        fl = QHBoxLayout(fg)
        fl.addWidget(QLabel(I18n.t("annotation_edit.size_label")))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.annotation.font_size)
        fl.addWidget(self.font_size_spin)
        self.bold_check = QCheckBox(I18n.t("annotation_edit.bold_check"))
        self.bold_check.setChecked(self.annotation.is_bold)
        fl.addWidget(self.bold_check)
        fl.addStretch()
        layout.addWidget(fg)

        cg = QGroupBox(I18n.t("annotation_edit.color_group"))
        cl = QHBoxLayout(cg)
        self.color_btn = QPushButton(I18n.t("annotation_edit.color_btn"))
        self.color_btn.clicked.connect(self._pick_color)
        self.color_btn.setStyleSheet(f"background-color:{self.annotation.color};color:white;")
        cl.addWidget(self.color_btn)
        cl.addStretch()
        layout.addWidget(cg)

        # 按钮区域: 确定 / 删除 / 取消 (编辑模式特有删除按钮)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(I18n.t("annotation_edit.save_btn"))
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        del_btn = QPushButton(I18n.t("annotation_edit.delete_btn"))
        del_btn.setObjectName("deleteBtn")
        del_btn.clicked.connect(self._on_delete_clicked)
        btn_layout.addWidget(del_btn)

        cancel_btn = QPushButton(I18n.t("annotation_edit.cancel_btn"))
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            f"background-color:{ThemeManager.get('bg_surface', '#252536')};"
            f"color:{ThemeManager.get('text_secondary', '#94A3B8')};"
        )
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _pick_color(self) -> None:
        c = QColorDialog.getColor(self._temp_color or Qt.white, self, I18n.t("annotation_edit.color_dialog_title"))
        if c.isValid():
            self._temp_color = c.name()
            self.color_btn.setStyleSheet(f"background-color:{self._temp_color};color:white;")

    def _on_delete_clicked(self) -> None:
        """点击删除按钮: 设置标记并以Accepted状态关闭(由调用方执行实际删除)"""
        reply = QMessageBox.question(
            self, I18n.t("messages.delete_confirm_title"),
            I18n.t("messages.delete_confirm_msg"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.should_delete = True
            self.accept()

    def get_annotation(self) -> Annotation:
        self.annotation.text = self.text_edit.toPlainText()
        self.annotation.font_size = self.font_size_spin.value()
        self.annotation.is_bold = self.bold_check.isChecked()
        self.annotation.color = self._temp_color
        return self.annotation


class AnnotationManagerDialog(QDialog):
    """
    标注管理器 - 列表管理所有标注

    功能: 新增/编辑/删除标注，支持 Ctrl+Z 撤销 / Ctrl+Y 重做
    注意: 撤销/重做已统一委托给父窗口DisplayWindow的全局栈，
          管理器内的操作与画布双击操作共享同一套撤销历史。

    调用方: DisplayWindow._open_annotation_manager()
    """
    annotationsChanged = pyqtSignal(list)

    def __init__(self, parent=None, annotations: Optional[List[Annotation]] = None):
        super().__init__(parent)
        self.annotations = annotations or []
        # 引用父窗口的撤销/重做方法(全局统一栈)
        self._parent_window = parent
        self.init_ui()

    def init_ui(self) -> None:
        """初始化标注管理器UI(列表模式) - 从ThemeManager读取当前主题"""
        self.setWindowTitle(I18n.t("annotation_manager.window_title"))
        self.setMinimumSize(550, 400)
        t = ThemeManager.current()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {t['bg_primary']}; }}
            QLabel {{ color: {t['text_primary']}; font-family: {get_font_family_css('ui')}; }}
            QListWidget {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 6px; }}
            QListWidget::item:selected {{ background-color: {t['primary']}; }}
            QListWidget::item:hover {{ background-color: {t['primary']}; opacity:0.15; border-radius: 4px; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none; border-radius: 6px; padding: 7px 14px; }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
            QPushButton#delBtn {{ background-color: {ThemeManager.get('danger', '#EF4444')}; }}
            QPushButton#delBtn:hover {{ background-color: #DC2626; }}
        """)
        layout = QVBoxLayout(self)
        title = QLabel(I18n.t("annotation_manager.list_title", count=len(self.annotations)))
        title.setStyleSheet(f"font-size:15px;font-weight:bold;color:{ThemeManager.get('primary_light', '#60A5FA')};")
        layout.addWidget(title)
        self.list_widget = QListWidget()
        self._populate_list()
        self.list_widget.itemDoubleClicked.connect(self._edit_item)
        layout.addWidget(self.list_widget)
        bl = QHBoxLayout()
        for txt, slot, st in [
            (I18n.t("annotation_manager.add_btn"), self._add_new, ""),
            (I18n.t("annotation_manager.edit_btn"), lambda: self._edit_item(self.list_widget.currentItem()), ""),
            (I18n.t("annotation_manager.delete_btn"), self._delete_item, "#delBtn"),
            (I18n.t("annotation_manager.clear_btn"), self._clear_all, "#delBtn"),
        ]:
            b = QPushButton(txt)
            if st:
                b.setObjectName(st)
            b.clicked.connect(slot)
            bl.addWidget(b)
        layout.addLayout(bl)
        bbox = QDialogButtonBox(QDialogButtonBox.Close)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def _populate_list(self) -> None:
        self.list_widget.clear()
        for a in self.annotations:
            pv = a.text[:28] + "..." if len(a.text) > 28 else a.text
            item = QListWidgetItem(f"[{a.id}]({a.x:.0%},{a.y:.0%}){pv}")
            item.setData(Qt.UserRole, a.id)
            self.list_widget.addItem(item)

    # ========== 撤销/重做(委托给父窗口全局栈) ==========
    def _save_snapshot(self) -> None:
        """修改前保存快照 → 委托给父窗口的全局撤销栈"""
        if self._parent_window and hasattr(self._parent_window, '_anno_save_snapshot'):
            self._parent_window._anno_save_snapshot()

    def _undo(self) -> None:
        """Ctrl+Z 撤销 → 委托给父窗口"""
        if self._parent_window and hasattr(self._parent_window, '_anno_undo'):
            self._parent_window._anno_undo()
            # 同步本地列表
            self.annotations = self._parent_window.annotations
            self._populate_list()

    def _redo(self) -> None:
        """Ctrl+Y 重做 → 委托给父窗口"""
        if self._parent_window and hasattr(self._parent_window, '_anno_redo'):
            self._parent_window._anno_redo()
            # 同步本地列表
            self.annotations = self._parent_window.annotations
            self._populate_list()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """键盘事件: Ctrl+Z撤销 / Ctrl+Y重做"""
        try:
            if event.modifiers() & Qt.ControlModifier:
                if event.key() == Qt.Key_Z:
                    self._undo()
                elif event.key() == Qt.Key_Y:
                    self._redo()
                else:
                    super().keyPressEvent(event)
            else:
                super().keyPressEvent(event)
        except Exception:
            super().keyPressEvent(event)

    # ========== 标注操作(已集成撤销) ==========
    def _add_new(self) -> None:
        self._save_snapshot()  # 修改前保存快照(委托给父窗口全局栈)
        dlg = AnnotationEditDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.annotations.append(dlg.get_annotation())
            self._populate_list()
            self.annotationsChanged.emit(self.annotations)
        else:
            # 取消则撤销刚才保存的快照，恢复状态
            self._undo()

    def _edit_item(self, item) -> None:
        if not item:
            return
        aid = item.data(Qt.UserRole)
        ann = next((a for a in self.annotations if a.id == aid), None)
        if ann:
            self._save_snapshot()  # 修改前保存快照(委托给父窗口全局栈)
            dlg = AnnotationEditDialog(self, annotation=ann)
            if dlg.exec_() == QDialog.Accepted:
                upd = dlg.get_annotation()
                idx = next(i for i, a in enumerate(self.annotations) if a.id == aid)
                self.annotations[idx] = upd
                self._populate_list()
                self.annotationsChanged.emit(self.annotations)
            else:
                # 取消则撤销刚才保存的快照，恢复状态
                self._undo()

    def _delete_item(self) -> None:
        item = self.list_widget.currentItem()
        if item:
            self._save_snapshot()
            aid = item.data(Qt.UserRole)
            self.annotations = [a for a in self.annotations if a.id != aid]
            self._populate_list()
            self.annotationsChanged.emit(self.annotations)

    def _clear_all(self) -> None:
        if QMessageBox.question(
            self,
            I18n.t("messages.clear_all_confirm_title"),
            I18n.t("messages.clear_all_confirm_msg"),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self._save_snapshot()
            self.annotations.clear()
            self._populate_list()
            self.annotationsChanged.emit(self.annotations)
