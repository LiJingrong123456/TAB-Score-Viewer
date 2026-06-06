/**
 * ============================================================
 * 文件名: useAnnotation.ts
 * 功能描述: 标注管理Hook - 管理谱面文本标注的逻辑
 *          - 标注的增删改查
 *          - 标注位置拖拽处理
 *          - 标注数据持久化准备
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: playerStore, types, React
 * ============================================================
 */

import { useCallback, useState } from 'react';
import { useAppStore } from '@/stores/playerStore';
import type { Annotation } from '@/types';

/**
 * 标注管理自定义Hook
 * 提供标注系统的完整交互逻辑
 * 
 * @returns 标注操作方法和编辑状态
 */
export function useAnnotation() {
  const {
    annotations,
    addAnnotation,
    updateAnnotation,
    removeAnnotation,
    clearAnnotations,
  } = useAppStore();

  // 编辑状态
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isAddingNew, setIsAddingNew] = useState(false);

  /**
   * 在指定位置添加新标注
   * @param x - X坐标(百分比)
   * @param y - Y坐标(百分比)
   */
  const createAnnotation = useCallback((x: number, y: number) => {
    addAnnotation({
      text: '新标注',
      x: Math.max(0, Math.min(100, x)),
      y: Math.max(0, Math.min(100, y)),
      color: '#F97316',
    });
    setIsAddingNew(false);
  }, [addAnnotation]);

  /**
   * 更新标注文本内容
   * @param id - 标注ID
   * @param text - 新文本内容
   */
  const updateText = useCallback((id: string, text: string) => {
    updateAnnotation(id, { text });
  }, [updateAnnotation]);

  /**
   * 更新标注位置
   * @param id - 标注ID
   * @param x - 新X坐标(百分比)
   * @param y - 新Y坐标(百分比)
   */
  const moveAnnotation = useCallback((id: string, x: number, y: number) => {
    updateAnnotation(id, {
      x: Math.max(0, Math.min(100, x)),
      y: Math.max(0, Math.min(100, y)),
    });
  }, [updateAnnotation]);

  /**
   * 删除指定标注
   * @param id - 标注ID
   */
  const deleteAnnotation = useCallback((id: string) => {
    removeAnnotation(id);
    if (editingId === id) setEditingId(null);
  }, [removeAnnotation, editingId]);

  /**
   * 开始编辑标注
   * @param id - 标注ID，传null退出编辑
   */
  const startEdit = useCallback((id: string | null) => {
    setEditingId(id);
  }, []);

  /**
   * 结束编辑
   */
  const endEdit = useCallback(() => {
    setEditingId(null);
  }, []);

  /**
   * 导出标注数据为JSON
   * @returns JSON字符串
   */
  const exportAnnotations = useCallback((): string => {
    return JSON.stringify(annotations, null, 2);
  }, [annotations]);

  /**
   * 从JSON导入标注数据
   * @param json - JSON字符串
   */
  const importAnnotations = useCallback((json: string) => {
    try {
      const data: Annotation[] = JSON.parse(json);
      clearAnnotations();
      data.forEach((anno) => {
        addAnnotation({
          text: anno.text,
          x: anno.x,
          y: anno.y,
          color: anno.color,
          timestamp: anno.timestamp,
        });
      });
      return true;
    } catch {
      console.error('导入标注数据失败');
      return false;
    }
  }, [clearAnnotations, addAnnotation]);

  return {
    // 数据
    annotations,
    editingId,
    isAddingNew,

    // 操作方法
    createAnnotation,
    updateText,
    moveAnnotation,
    deleteAnnotation,
    startEdit,
    endEdit,
    setIsAddingNew,
    exportAnnotations,
    importAnnotations,
    clearAnnotations,
  };
}
