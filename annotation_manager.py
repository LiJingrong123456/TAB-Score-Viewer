# -*- coding: utf-8 -*-
"""
TAB Score Viewer - AnnotationManager

负责标注的加载/保存/切轨/撤销/重做管理。

设计:
  - AnnotationManager 持有 DisplayWindow 引用 (window)
  - 所有标注操作通过 window.display_widget 刷新UI
  - 通过 window.gtp_player 读取/切换当前音轨
  - 撤销/重做栈为模块内部状态
  - 打开/关闭标注管理器时由 DisplayWindow 调用对应 hook

迁移的方法 (原 DisplayWindow 内部):
  - _get_annotation_file_path
  - _get_annotation_file_path_legacy
  - _load_annotations
  - _save_annotations
  - _switch_track_annotations
  - _anno_save_snapshot
  - _anno_undo
  - _anno_redo
  - _load_track_annotations (导出/打印使用)
"""

import os
import json
from typing import Dict, List, Optional

from dataclasses import asdict

from models import Annotation
from constants import ANNOTATION_EXT, ANNOTATION_DIR


class AnnotationManager:
    """
    标注生命周期管理

    协作:
      - window.display_widget.set_annotations(...) - 刷新画布
      - window.gtp_player - 读取/切换当前音轨
      - window._ann_manager - 打开中的标注管理器 (用于 undo/redo 同步)
    """

    # 最大撤销深度 (防止内存膨胀)
    UNDO_MAX_DEPTH: int = 50

    def __init__(self, window) -> None:
        """
        参数:
            window: DisplayWindow 实例 (提供 display_widget, gtp_player, file_path)
        """
        self._window = window
        # 按音轨索引分轨存储的标注字典
        self._annotations_by_track: Dict[int, List[Annotation]] = {}
        # 撤销/重做栈(存 dict 列表, 避免每次快照创建对象, P0-3)
        self._undo_stack: List[List[dict]] = []
        self._redo_stack: List[List[dict]] = []

    # ============================================================
    # 当前标注的便捷访问(读写走 self._window.annotations)
    # ============================================================

    @property
    def annotations(self) -> List[Annotation]:
        return self._window.annotations

    @annotations.setter
    def annotations(self, value: List[Annotation]) -> None:
        self._window.annotations = value

    @property
    def file_path(self):
        return self._window.file_path

    @property
    def gtp_player(self):
        return self._window.gtp_player

    @property
    def display_widget(self):
        return self._window.display_widget

    # ============================================================
    # 路径解析
    # ============================================================

    def get_annotation_file_path(self) -> str:
        """
        获取当前音轨的标注存储路径(同名.anno.json策略 + 分轨)

        原理: 标注文件与源文件放在同一目录:
          - 非GTP/单轨: {源文件名}.anno.json (例: 晚安北京.png.anno.json)
          - GTP多轨:   {源文件名}.t{轨道号}.anno.json (例: song.gp4.t0.anno.json)
        兼容性: 源文件路径无效时回退到旧的 data/annotations/ 路径
        """
        if isinstance(self.file_path, str) and self.file_path:
            if self.gtp_player and self.gtp_player.is_loaded:
                return f"{self.file_path}.t{self.gtp_player.current_track}{ANNOTATION_EXT}"
            return self.file_path + ANNOTATION_EXT
        base = "multi_image"
        os.makedirs(ANNOTATION_DIR, exist_ok=True)
        return os.path.join(ANNOTATION_DIR, f"{base}.json")

    def get_annotation_file_path_legacy(self) -> str:
        """
        获取旧版标注存储路径(data/annotations/{base}.json)
        用于向后兼容: 加载时同时检查新旧两个位置
        """
        if isinstance(self.file_path, str):
            base = os.path.splitext(os.path.basename(self.file_path))[0]
        else:
            base = "multi_image"
        os.makedirs(ANNOTATION_DIR, exist_ok=True)
        return os.path.join(ANNOTATION_DIR, f"{base}.json")

    # ============================================================
    # 加载 / 保存
    # ============================================================

    def load(self) -> None:
        """
        从JSON加载标注 - 支持新旧两种路径(优先新路径)
        加载顺序:
          1. 新路径: {源文件}.anno.json (同目录)
          2. 旧路径: data/annotations/{base}.json (兼容旧版)
        """
        new_path = self.get_annotation_file_path()
        old_path = self.get_annotation_file_path_legacy()

        load_from: Optional[str] = None
        if os.path.exists(new_path):
            load_from = new_path
        elif os.path.exists(old_path):
            load_from = old_path  # 向后兼容: 旧位置有数据则加载

        if load_from:
            try:
                with open(load_from, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.annotations = [Annotation(**d) for d in data]
                return
            except Exception:
                pass
        self.annotations = []

    def save(self) -> None:
        """保存标注到JSON - 写入到源文件同目录的 .anno.json 文件"""
        try:
            fpath = self.get_annotation_file_path()
            dname = os.path.dirname(fpath)
            if dname:
                os.makedirs(dname, exist_ok=True)
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump([asdict(a) for a in self.annotations], f,
                          ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存标注失败: {e}")

    # ============================================================
    # 切轨
    # ============================================================

    def switch_track(self, old_track: int, new_track: int) -> None:
        """
        切换音轨时的标注切换(保存当前轨 → 加载目标轨)

        原理: GTP多轨文件每个音轨有独立的标注文件。
              切换音轨时:
                1. 将当前annotations存入分轨字典 _annotations_by_track[old_track]
                2. 从字典或文件中加载 new_track 的 annotations
                3. 更新画布显示 + 清空撤销/重做栈(跨轨撤销无意义)
        """
        if old_track == new_track:
            return

        # 1. 保存当前轨标注到内存字典
        self._annotations_by_track[old_track] = self.annotations.copy()

        # 2. 持久化当前轨标注到文件(此时 gtp_current_track 还是 old_track)
        try:
            fpath = self.get_annotation_file_path()
            dname = os.path.dirname(fpath)
            if dname:
                os.makedirs(dname, exist_ok=True)
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump([asdict(a) for a in self.annotations], f,
                          ensure_ascii=False, indent=2)
        except Exception:
            pass

        # 3. 加载目标轨标注(优先内存 > 文件 > 空列表)
        if self.gtp_player:
            self.gtp_player.current_track = new_track

        if new_track in self._annotations_by_track and self._annotations_by_track[new_track]:
            self.annotations = [Annotation(**asdict(a)) for a in self._annotations_by_track[new_track]]
        else:
            self.load()
            self._annotations_by_track[new_track] = self.annotations.copy()

        # 4. 更新画布显示
        if self.display_widget:
            self.display_widget.set_annotations(self.annotations)

        # 5. 清空撤销/重做栈(跨轨操作不应共享撤销历史)
        self._undo_stack.clear()
        self._redo_stack.clear()

    # ============================================================
    # 撤销 / 重做
    # ============================================================

    def save_snapshot(self) -> None:
        """
        保存当前标注状态快照到撤销栈(修改前必须调用)

        性能优化(P0-3): 存储 dict 列表而非 Annotation 对象列表,
                        避免每次快照创建N个Annotation对象。
                        仅在撤销/重做时按需重建Annotation对象。

        使用场景: 所有修改annotations的操作前调用此方法:
                  - 双击画布添加/编辑标注
                  - 管理器中新增/编辑/删除/清空标注
        """
        snapshot = [asdict(a) for a in self.annotations]
        self._undo_stack.append(snapshot)
        self._redo_stack.clear()  # 新操作清空重做栈
        # 限制深度防止内存膨胀
        if len(self._undo_stack) > self.UNDO_MAX_DEPTH:
            self._undo_stack.pop(0)

    def undo(self) -> None:
        """
        Ctrl+Z 全局撤销 - 回退到上一个标注状态
        """
        if not self._undo_stack:
            return
        # 当前状态存入重做栈
        redo_snap = [asdict(a) for a in self.annotations]
        self._redo_stack.append(redo_snap)
        # 恢复上一个状态
        prev = self._undo_stack.pop()
        self.annotations = [Annotation(**d) for d in prev]
        # 刷新UI
        if self.display_widget:
            self.display_widget.set_annotations(self.annotations)
        self.save()
        # 同步管理器(如果打开着)
        mgr = getattr(self._window, '_ann_manager', None)
        if mgr:
            mgr.annotations = self.annotations
            mgr._populate_list()

    def redo(self) -> None:
        """
        Ctrl+Y 全局重做 - 恢复被撤销的状态
        """
        if not self._redo_stack:
            return
        # 当前状态存入撤销栈
        undo_snap = [asdict(a) for a in self.annotations]
        self._undo_stack.append(undo_snap)
        # 恢复重做状态
        nxt = self._redo_stack.pop()
        self.annotations = [Annotation(**d) for d in nxt]
        # 刷新UI
        if self.display_widget:
            self.display_widget.set_annotations(self.annotations)
        self.save()
        # 同步管理器(如果打开着)
        mgr = getattr(self._window, '_ann_manager', None)
        if mgr:
            mgr.annotations = self.annotations
            mgr._populate_list()

    # ============================================================
    # 导出/打印场景:加载指定轨道的标注
    # ============================================================

    def load_track_annotations(self, track_idx: int) -> list:
        """
        加载指定轨道的标注(从文件或内存缓存) - 供导出/打印使用

        注意: 必须在调用前确保 track_idx 处的路径计算正确。
              临时切换 gtp_player.current_track 然后还原, 避免破坏状态。
        """
        if track_idx in self._annotations_by_track and self._annotations_by_track[track_idx]:
            return [Annotation(**asdict(a)) for a in self._annotations_by_track[track_idx]]
        fpath: Optional[str] = None
        if self.gtp_player:
            old_track = self.gtp_player.current_track
            self.gtp_player.current_track = track_idx
            try:
                fpath = self.get_annotation_file_path()
            finally:
                self.gtp_player.current_track = old_track
        if fpath and os.path.exists(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [Annotation(**d) for d in data]
            except Exception:
                pass
        return []

    # ============================================================
    # 便捷方法:添加标注
    # ============================================================

    def add(self, ann: Annotation) -> None:
        """添加标注(集成全局撤销)"""
        self.save_snapshot()
        self.annotations.append(ann)
        if self.display_widget:
            self.display_widget.set_annotations(self.annotations)
        self.save()

    def set_active_manager(self, manager) -> None:
        """
        设置/清除当前打开的标注管理器(供 undo/redo 同步)

        调用方式:
          - DisplayWindow._open_annotation_manager: 调用 set_active_manager(dlg)
          - 对话框关闭: 调用 set_active_manager(None)
        """
        self._window._ann_manager = manager
