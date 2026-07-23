# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Workers Module

异步工作线程：
  - WorkerSignals        通用信号
  - LoadFileListWorker   异步扫描文件夹
  - LoadContentWorker    异步加载 PDF / 图片 / GTP
  - ThemeRefreshSignals / ThemeRefreshWorker  异步 GTP 主题刷新

注: ExportWorker 与 DisplayWindow 高度耦合, 暂保留在主文件中
"""

import os
from typing import List, Tuple, Optional

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QPen
from PyQt5.QtCore import Qt, QRect

import fitz  # PyMuPDF
from PIL import Image as PILImage

from constants import SUPPORTED_ALL_EXTENSIONS
from theme import ThemeManager
from i18n import I18n
from fonts import get_font_family


# ============================================================
# 通用信号
# ============================================================

class WorkerSignals(QObject):
    """通用异步工作信号类"""
    finished = pyqtSignal(object)  # object: 可携带任意数据(如文件列表)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    # macOS TCC 权限受限信号 - 携带被拒的文件路径，提示主线程弹出重新选择对话框
    # 触发场景: 系统重启后首次访问 ~/Downloads 等目录下的文件，macOS 可能返回 errno 1 (EPERM)
    # 此时通过 QFileDialog 让用户重新选择同一文件即可触发 macOS 授予 TCC 权限
    permission_denied = pyqtSignal(str)


# ============================================================
# 文件列表加载
# ============================================================

class LoadFileListWorker(QRunnable):
    """异步加载文件列表的工作线程"""

    def __init__(self, folder: str):
        super().__init__()
        self.folder = folder
        self.signals = WorkerSignals()
        self._result: List[Tuple] = []

    def run(self) -> None:
        """异步扫描文件夹 - 过滤支持的文件格式"""
        try:
            # 预检查: 目录不存在或不可访问时立即返回错误
            if not os.path.exists(self.folder):
                self.signals.error.emit(f"目录不存在: {self.folder}"); return
            if not os.path.isdir(self.folder):
                self.signals.error.emit(f"路径不是文件夹: {self.folder}"); return
            if not os.access(self.folder, os.R_OK):
                self.signals.error.emit(f"无权限访问目录: {self.folder}"); return

            file_items = []
            for file in os.listdir(self.folder):
                file_path = os.path.join(self.folder, file)
                if os.path.isdir(file_path) and not file.startswith('.'):
                    file_items.append((file + '/', file_path, True))
            for file in os.listdir(self.folder):
                file_path = os.path.join(self.folder, file)
                if os.path.isfile(file_path) and file.lower().endswith(SUPPORTED_ALL_EXTENSIONS):
                    file_items.append((file, file_path, False))
            self._result = sorted(file_items, key=lambda x: (not x[2], x[0]))
            self.signals.finished.emit(self._result)  # 携带文件列表数据
        except PermissionError:
            self.signals.error.emit(f"无权限访问目录: {self.folder}")
        except OSError as e:
            self.signals.error.emit(f"访问目录出错: {e}")
        except Exception as e:
            self.signals.error.emit(str(e))


# ============================================================
# 谱面内容加载
# ============================================================

class LoadContentWorker(QRunnable):
    """
    异步加载谱面内容的工作线程
    原理: 在后台线程中解析文件，避免阻塞UI主线程
    支持: PDF(PyMuPDF)、图片(Pillow)、GTP(基础预览)
    """

    def __init__(self, window, file_path, file_type: str):
        """
        参数:
            window:     DisplayWindow 实例（提供 loaded_images、gtp_player、_page_layouts）
            file_path:  单个路径字符串 或 多图路径列表
            file_type:  'pdf' | 'images' | 'gtp'
        """
        super().__init__()
        self.window = window
        self.file_path = file_path
        self.file_type = file_type
        self.signals = WorkerSignals()

    def _precheck_file_access(self, path) -> Optional[str]:
        """
        预检查文件可访问性 (修复 macOS 重启后 [Errno 1] Operation not permitted)

        背景:
          macOS 上 TCC (Transparency, Consent, and Control) 会在系统重启后的
          首次访问时拒绝未授权的文件路径，errno = 1 (EPERM)。
          表现为: 程序加载 ~/Downloads/*.gp3 等文件失败，但用户在选择窗口
          里"重新打开文件夹"后再次选择同一文件即可成功——因为 QFileDialog
          会触发 macOS 授予 TCC 权限。

        返回:
          None - 可访问
          str  - 不可访问的错误描述
        """
        if isinstance(path, (list, tuple)):
            # 图片批量加载场景：任一文件不可访问就整体失败
            for p in path:
                err = self._precheck_file_access(p)
                if err:
                    return err
            return None
        if not path:
            return "文件路径为空"
        if not os.path.exists(path):
            return f"文件不存在: {path}"
        if not os.path.isfile(path):
            return f"路径不是文件: {path}"
        # 实际尝试打开，避免把权限问题延迟到 ApolloTab 内部
        try:
            with open(path, 'rb') as _f:
                _f.read(1)  # 读取1字节，强制触发系统调用
            return None
        except OSError as e:
            # macOS: errno 1 (EPERM) "Operation not permitted"
            # 常规: errno 13 (EACCES) "Permission denied"
            errno_no = getattr(e, 'errno', None)
            if errno_no in (1, 13) or 'not permitted' in str(e).lower() or 'permission denied' in str(e).lower():
                return (f"macOS系统权限限制 ({errno_no or 'EPERM'}): "
                        f"系统重启后首次访问此文件可能受限，"
                        f"请在文件选择窗口中重新打开此文件以授权。\n\n文件: {path}")
            return f"无法访问文件: {e}"

    def run(self) -> None:
        try:
            images: List[QPixmap] = []
            # 通用 macOS TCC 预检查 - 所有类型都先校验一次
            precheck_err = self._precheck_file_access(self.file_path)
            if precheck_err:
                # 通知主线程弹出恢复对话框 (QFileDialog 重新选择可触发 TCC 授权)
                self.signals.permission_denied.emit(
                    self.file_path[0] if isinstance(self.file_path, (list, tuple)) and self.file_path
                    else (self.file_path if isinstance(self.file_path, str) else "")
                )
                # 同时返回错误图，保证界面不会卡在空白/loading 状态
                err_image = self._create_error_image(
                    f"{I18n.t('messages.gtp_load_fail', error=precheck_err)}"
                )
                self.window.loaded_images = [err_image]
                self.signals.finished.emit([err_image])
                return

            if self.file_type == 'pdf':
                images = self._load_pdf()
            elif self.file_type == 'images':
                images = self._load_images()
            elif self.file_type == 'gtp':
                images = self._load_gtp()
            self.window.loaded_images = images
            self.signals.finished.emit(images)  # 携带加载结果
        except Exception as e:
            self.signals.error.emit(str(e))

    def _load_pdf(self) -> List[QPixmap]:
        """
        加载PDF文件 - 使用PyMuPDF渲染每页为高DPI图片

        性能优化(P1-2): 使用 concurrent.futures.ThreadPoolExecutor 并行渲染多页，
                        max_workers=4，将50页PDF加载时间从~3s降至~1s。
                        PyMuPDF文档非线程安全，每个线程独立打开文档实例。
        """
        pdf_document = fitz.open(self.file_path)
        total_pages = len(pdf_document)
        pdf_document.close()

        # 定义单页渲染函数（每个线程独立打开文档实例）
        def _render_page(page_num: int) -> QPixmap:
            doc = fitz.open(self.file_path)
            try:
                page = doc[page_num]
                pix = page.get_pixmap(dpi=200)  # 高DPI渲染保证清晰度
                qt_image = QPixmap()
                qt_image.loadFromData(pix.tobytes("png"))
                return qt_image
            finally:
                doc.close()

        # 并行渲染：使用ThreadPoolExecutor，max_workers=4
        images = [None] * total_pages
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 提交所有渲染任务
            future_to_page = {executor.submit(_render_page, i): i for i in range(total_pages)}
            completed = 0
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                images[page_num] = future.result()
                completed += 1
                self.signals.progress.emit(int(completed / total_pages * 100))

        return images

    def _load_images(self) -> List[QPixmap]:
        """
        加载图片文件列表
        支持: PNG, JPG, JPEG, WEBP (通过Pillow库)
        Pillow是Python图像处理标准库(PIL fork)，支持多种格式
        """
        images: List[QPixmap] = []
        paths = self.file_path if isinstance(self.file_path, list) else [self.file_path]
        total = len(paths)
        for idx, path in enumerate(paths):
            pil_img = PILImage.open(path)
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')  # 统一转换为RGBA确保兼容性
            qimage = QImage(pil_img.tobytes('raw', 'RGBA'), pil_img.width, pil_img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            if not pixmap.isNull():
                images.append(pixmap)
            pil_img.close()
            self.signals.progress.emit(int((idx + 1) / total * 100))
        return images

    def _load_gtp(self) -> List[QPixmap]:
        """
        加载Guitar Pro文件(.gp3/.gp4/.gp5/.gpx/.gtp/.gp)

        原理: 使用 gtp_engine 库的 GTPPlayer 高级API完整处理 GTP 文件,
              包括解析、渲染、音频初始化等。
              GTPPlayer 封装了所有GTP相关逻辑，主程序只需简单调用。

        依赖库:
          - gtp_engine (含 guitarpro, PyQt5, pyfluidsynth)

        macOS 兼容性:
          系统重启后首次访问文件可能因 TCC 权限返回 errno 1 (EPERM),
          run() 阶段的预检查会先拦截；此处仍保留 OSError 兜底以防
          预检查因路径大小写/符号链接差异漏判。
        """
        images: List[QPixmap] = []
        try:
            from ApolloTab import GTPPlayer

            # 创建播放器实例并加载文件
            player = GTPPlayer()
            player.load(self.file_path)

            # v2.0新增: 根据当前UI主题设置GTP渲染主题
            render_theme = ThemeManager.get_gtp_render_theme()
            # 安全检查: 确保GTPPlayer版本支持set_theme方法
            if hasattr(player, 'set_theme') and callable(getattr(player, 'set_theme')):
                try:
                    player.set_theme(render_theme)
                    print(f"[LoadContentWorker] GTP渲染主题: {render_theme}")
                except Exception as e:
                    print(f"[LoadContentWorker] 设置GTP渲染主题失败(使用默认): {e}")
            else:
                print(f"[LoadContentWorker] 当前GTPPlayer版本不支持主题切换，使用默认主题")

            # 渲染当前音轨（默认第0轨）
            pixmaps = player.render_track(0)

            # 保存播放器实例到window（供后续音频/时间线功能使用）
            self.window.gtp_player = player

            # 捕获布局数据(播放光标功能依赖此数据)
            self.window._page_layouts = player.last_layouts

            # 进度报告：完成
            self.signals.progress.emit(100)

            images = pixmaps

        except ImportError as e:
            # gtp_engine 或依赖未安装时，回退到信息展示图
            info_pixmap = self._create_gtp_info_image(
                f"GTP引擎依赖缺失:\n{str(e)}\n\n请安装: pip install gtp-engine"
            )
            images.append(info_pixmap)
        except OSError as e:
            # macOS TCC 权限限制 (errno 1) / 常规 EACCES (errno 13) — 兜底分支
            errno_no = getattr(e, 'errno', None)
            err_text = str(e)
            if errno_no in (1, 13) or 'not permitted' in err_text.lower() or 'permission denied' in err_text.lower():
                # 通知主线程弹出重新选择对话框
                self.signals.permission_denied.emit(self.file_path)
                friendly = (f"macOS系统权限限制 ({errno_no or 'EPERM'}): "
                            f"系统重启后首次访问此文件可能受限。\n\n"
                            f"请在弹出的对话框中点击「重新选择文件」以授权。\n\n"
                            f"原始错误: {err_text}")
            else:
                friendly = f"GTP加载失败:\n{err_text}"
            images.append(self._create_error_image(friendly))
        except Exception as e:
            # 其他错误时，显示错误信息和回退预览
            error_pixmap = self._create_error_image(f"GTP加载失败:\n{str(e)}")
            images.append(error_pixmap)

        return images

    def _create_error_image(self, message: str) -> QPixmap:
        """创建错误展示图（当GTP加载失败时显示）- 支持动态主题"""
        width, height = 800, 500
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(ThemeManager.get('bg_surface', '#252536')))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 标题
        painter.setPen(QColor(ThemeManager.get('danger', '#EF4444')))
        title_font = QFont(get_font_family("ui"), 26, QFont.Bold)
        painter.setFont(title_font)
        filename = os.path.basename(self.file_path) if isinstance(self.file_path, str) else ""
        painter.drawText(QRect(50, 40, 700, 60), Qt.AlignCenter, f"加载失败: {filename}")

        # 错误文本
        painter.setPen(QColor(ThemeManager.get('text_primary', '#E2E8F0')))
        info_font = QFont(get_font_family("ui"), 13)
        painter.setFont(info_font)

        # 将message按行分割并绘制
        lines = message.split('\n')
        y = 130
        for line in lines:
            if line.strip():
                painter.drawText(QRect(50, y, 700, 32), Qt.AlignLeft, line)
            y += 30

        # 边框
        painter.setPen(QPen(QColor(ThemeManager.get('danger', '#EF4444')), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(30, 30, width - 60, height - 60, 15, 15)
        painter.end()
        return pixmap

    def _create_gtp_info_image(self, message: str) -> QPixmap:
        """创建GTP信息/错误展示图（当gtp_engine不可用时回退显示）- 支持动态主题"""
        width, height = 800, 500
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(ThemeManager.get('bg_surface', '#252536')))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 标题
        painter.setPen(QColor(ThemeManager.get('primary', '#3B82F6')))
        title_font = QFont(get_font_family("ui"), 26, QFont.Bold)
        painter.setFont(title_font)
        filename = os.path.basename(self.file_path) if isinstance(self.file_path, str) else ""
        painter.drawText(QRect(50, 40, 700, 60), Qt.AlignCenter, f"Guitar Pro 文件: {filename}")

        # 信息文本
        painter.setPen(QColor(ThemeManager.get('text_primary', '#E2E8F0')))
        info_font = QFont(get_font_family("ui"), 13)
        painter.setFont(info_font)

        # 将message按行分割并绘制
        lines = message.split('\n')
        y = 130
        for line in lines:
            if line.strip():
                painter.drawText(QRect(50, y, 700, 32), Qt.AlignLeft, line)
            y += 30

        # 边框
        painter.setPen(QPen(QColor(ThemeManager.get('primary', '#3B82F6')), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(30, 30, width - 60, height - 60, 15, 15)
        painter.end()
        return pixmap


# ============================================================
# GTP 主题刷新
# ============================================================

class ThemeRefreshSignals(QObject):
    """主题刷新线程信号"""
    finished = pyqtSignal(list)  # 携带渲染结果 (all_pixmaps)
    error = pyqtSignal(str)      # 错误信息


class ThemeRefreshWorker(QRunnable):
    """
    异步GTP主题刷新工作线程

    原理: 在后台线程中调用 GTPPlayer 重新渲染所有页面,
          完成后通过信号将结果通知主线程更新UI。

    使用方式:
      worker = ThemeRefreshWorker(gtp_player, theme_name)
      worker.signals.finished.connect(update_callback)
      QThreadPool.globalInstance().start(worker)
    """
    def __init__(self, gtp_player, theme_name: str):
        super().__init__()
        self.gtp_player = gtp_player
        self.theme_name = theme_name
        self.signals = ThemeRefreshSignals()

    def run(self) -> None:
        try:
            self.gtp_player.set_theme(self.theme_name)
            all_pixmaps = self.gtp_player.render_track(self.gtp_player.current_track)
            self.signals.finished.emit(all_pixmaps)
        except Exception as e:
            self.signals.error.emit(str(e))
