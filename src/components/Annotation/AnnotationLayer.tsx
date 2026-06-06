/**
 * ============================================================
 * 文件名: AnnotationLayer.tsx
 * 功能描述: 标注层组件 - 覆盖在谱面上的透明交互层
 *          显示所有文本标注，支持点击编辑、拖拽移动
 *          使用 @dnd-kit 实现拖拽功能
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: React, @dnd-kit, useAnnotation hook, types
 *          开源项目: @dnd-kit/core v6.x (MIT)
 * ============================================================
 */

import { useState, useCallback } from 'react';
import { useDroppable } from '@dnd-kit/core';
import { useAppStore } from '@/stores/playerStore';
import { useAnnotation } from '@/hooks/useAnnotation';
import type { Annotation as AnnotationType } from '@/types';
import { cn } from '@/utils/cn';

interface AnnotationLayerProps {
  /** 当前标注列表 */
  annotations: AnnotationType[];
}

/** 标注颜色选项 */
const ANNOTATION_COLORS = [
  '#F97316', // 橙色
  '#3B82F6', // 蓝色
  '#10B981', // 绿色
  '#EF4444', // 红色
  '#8B5CF6', // 紫色
  '#EC4899', // 粉色
];

/**
 * 单个标注项组件
 */
function AnnotationItem({ 
  annotation, 
  isEditing, 
  onEdit, 
  onUpdate, 
  onDelete,
}: {
  annotation: AnnotationType;
  isEditing: boolean;
  onEdit: () => void;
  onUpdate: (updates: Partial<AnnotationType>) => void;
  onDelete: () => void;
}) {
  const [editText, setEditText] = useState(annotation.text);
  const [showMenu, setShowMenu] = useState(false);

  /**
   * 提交编辑内容
   */
  const handleSubmit = useCallback(() => {
    if (editText.trim()) {
      onUpdate({ text: editText.trim() });
    }
    onEdit(); // 退出编辑模式
  }, [editText, onUpdate, onEdit]);

  /**
   * 处理键盘事件
   */
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === 'Escape') {
      setEditText(annotation.text);
      onEdit();
    }
  }, [handleSubmit, annotation.text, onEdit]);

  return (
    <div
      className={cn(
        "absolute group -translate-x-1/2 -translate-y-1/2",
        "transition-shadow duration-200",
        isEditing && "z-50"
      )}
      style={{
        left: `${annotation.x}%`,
        top: `${annotation.y}%`,
        pointerEvents: 'auto',
      }}
    >
      {/* 标注气泡 */}
      <div
        className={cn(
          "relative px-3 py-1.5 rounded-lg shadow-lg",
          "border-2 cursor-pointer select-none",
          "min-w-[60px] max-w-[200px]",
          "transition-all duration-150",
          isEditing ? "scale-105" : "hover:scale-105"
        )}
        style={{
          backgroundColor: `${annotation.color || '#F97316'}20`,
          borderColor: annotation.color || '#F97316',
        }}
        onClick={(e) => {
          e.stopPropagation();
          if (!isEditing) onEdit();
        }}
        onContextMenu={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setShowMenu(!showMenu);
        }}
      >
        {/* 编辑模式：输入框 */}
        {isEditing ? (
          <input
            type="text"
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            onBlur={handleSubmit}
            onKeyDown={handleKeyDown}
            autoFocus
            className="w-full bg-transparent text-sm text-text-primary outline-none placeholder:text-text-muted"
            placeholder="输入标注..."
          />
        ) : (
          /* 显示模式：文本 */
          <span className={cn(
            "text-sm font-medium whitespace-pre-wrap break-words",
            `text-[${annotation.color || '#F97316'}]`
          )} style={{ color: annotation.color || '#F97316' }}>
            {annotation.text}
          </span>
        )}

        {/* 删除按钮(悬停时显示) */}
        {!isEditing && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className={cn(
              "absolute -top-2 -right-2 w-5 h-5 rounded-full",
              "bg-red-500 text-white opacity-0 group-hover:opacity-100",
              "flex items-center justify-center transition-opacity",
              "text-xs hover:bg-red-600 cursor-pointer"
            )}
            aria-label="删除标注"
          >
            ×
          </button>
        )}

        {/* 右键菜单 */}
        {showMenu && (
          <div className="absolute top-full left-0 mt-1 py-1 bg-app-card border border-app-border rounded-lg shadow-xl z-50 min-w-[120px]">
            {/* 颜色选择 */}
            <div className="px-2 pb-1 border-b border-app-border">
              <p className="text-xs text-text-muted mb-1">颜色</p>
              <div className="flex gap-1">
                {ANNOTATION_COLORS.map((color) => (
                  <button
                    key={color}
                    onClick={() => {
                      onUpdate({ color });
                      setShowMenu(false);
                    }}
                    className={cn(
                      "w-5 h-5 rounded-full border-2 transition-transform",
                      annotation.color === color ? "scale-125 border-white" : "border-transparent",
                      "cursor-pointer"
                    )}
                    style={{ backgroundColor: color }}
                    aria-label={`选择颜色 ${color}`}
                  />
                ))}
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="py-1">
              <button
                onClick={() => { onEdit(); setShowMenu(false); }}
                className="w-full px-3 py-1.5 text-left text-sm text-text-secondary hover:bg-app-border hover:text-text-primary transition-colors cursor-pointer"
              >
                编辑
              </button>
              <button
                onClick={() => { onDelete(); setShowMenu(false); }}
                className="w-full px-3 py-1.5 text-left text-sm text-red-400 hover:bg-red-400/10 transition-colors cursor-pointer"
              >
                删除
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 小三角指示器 */}
      <div 
        className="absolute top-full left-1/2 -translate-x-1/2 -mt-1"
        style={{
          width: 0,
          height: 0,
          borderLeft: '6px solid transparent',
          borderRight: '6px solid transparent',
          borderTop: `6px solid ${annotation.color || '#F97316'}`,
        }}
      />
    </div>
  );
}

/**
 * 标注层组件
 * 覆盖在谱面上方的透明层，用于显示和管理标注
 */
export function AnnotationLayer({ annotations }: AnnotationLayerProps) {
  const { editingId, startEdit, updateText, deleteAnnotation } = useAnnotation();
  const { setIsAddingNew } = useAnnotation();
  const { viewMode } = useAppStore();

  // 设置为可放置区域（用于添加新标注）
  const { isOver, setNodeRef } = useDroppable({
    id: 'annotation-layer',
  });

  /**
   * 点击空白区域添加新标注
   */
  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (viewMode !== 'annotation') return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    // 通过useAnnotation hook创建新标注
    const { createAnnotation } = useAnnotation();
    createAnnotation(x, y);
  }, [viewMode]);

  // 非标注模式下不渲染
  if (viewMode !== 'annotation') return null;

  return (
    <div
      ref={setNodeRef}
      onClick={handleCanvasClick}
      className={cn(
        "absolute inset-0 z-10",
        isOver && "bg-primary/5",
        viewMode === 'annotation' ? "cursor-crosshair" : "cursor-default"
      )}
      style={{ pointerEvents: viewMode === 'annotation' ? 'auto' : 'none' }}
    >
      {/* 渲染所有标注 */}
      {annotations.map((anno) => (
        <AnnotationItem
          key={anno.id}
          annotation={anno}
          isEditing={editingId === anno.id}
          onEdit={() => startEdit(anno.id)}
          onUpdate={(updates) => {
            if (updates.text !== undefined) {
              updateText(anno.id, updates.text);
            } else {
              useAppStore.getState().updateAnnotation(anno.id, updates);
            }
          }}
          onDelete={() => deleteAnnotation(anno.id)}
        />
      ))}

      {/* 空白提示 */}
      {annotations.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <p className="text-sm text-text-muted/50">
            点击任意位置添加标注
          </p>
        </div>
      )}
    </div>
  );
}
