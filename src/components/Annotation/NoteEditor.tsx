/**
 * ============================================================
 * 文件名: NoteEditor.tsx
 * 功能描述: 标注管理面板组件 - 侧边栏中的标注管理界面
 *          提供：标注列表、批量操作、导入导出功能
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: React, useAnnotation hook, playerStore
 * ============================================================
 */

import { useState, useCallback, useRef } from 'react';
import { Plus, Trash2, Download, Upload, MessageSquare } from 'lucide-react';
import { useAnnotation } from '@/hooks/useAnnotation';
import { useAppStore } from '@/stores/playerStore';
import type { Annotation } from '@/types';
import { cn } from '@/utils/cn';

/**
 * 标注管理面板组件
 * 在侧边栏中显示所有标注的列表和管理工具
 */
export function AnnotationManager() {
  const {
    annotations,
    editingId,
    isAddingNew,
    createAnnotation,
    updateText,
    deleteAnnotation,
    startEdit,
    endEdit,
    setIsAddingNew,
    exportAnnotations,
    importAnnotations,
    clearAnnotations,
  } = useAnnotation();

  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * 在中心位置快速添加标注
   */
  const handleQuickAdd = useCallback(() => {
    createAnnotation(50, 50); // 默认放在中间位置
  }, [createAnnotation]);

  /**
   * 导出标注到JSON文件
   */
  const handleExport = useCallback(() => {
    const json = exportAnnotations();
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `annotations-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [exportAnnotations]);

  /**
   * 从JSON文件导入标注
   */
  const handleImportClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  /**
   * 处理文件导入
   */
  const handleFileImport = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const success = importAnnotations(text);
      if (!success) {
        alert('导入失败：JSON格式错误');
      }
    } catch {
      alert('读取文件失败');
    }

    // 重置input
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [importAnnotations]);

  /**
   * 清除所有标注（带确认）
   */
  const handleClearAll = useCallback(() => {
    if (annotations.length === 0) return;
    
    if (window.confirm(`确定要删除全部 ${annotations.length} 个标注吗？此操作不可撤销。`)) {
      clearAnnotations();
    }
  }, [annotations.length, clearAnnotations]);

  return (
    <div className="flex flex-col gap-4 p-4 h-full overflow-auto scrollbar-custom">
      {/* 标题栏 + 操作按钮 */}
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-text-primary flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-accent" />
          文本标注
          <span className="text-xs font-normal text-text-muted">
            ({annotations.length})
          </span>
        </h3>
        
        <div className="flex items-center gap-1">
          {/* 导入 */}
          <button
            onClick={handleImportClick}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-app-card transition-colors cursor-pointer"
            title="导入标注"
            aria-label="导入标注"
          >
            <Upload className="w-4 h-4" />
          </button>

          {/* 导出 */}
          <button
            onClick={handleExport}
            disabled={annotations.length === 0}
            className={cn(
              "p-1.5 rounded-lg transition-colors cursor-pointer",
              annotations.length === 0
                ? "text-text-muted/30 cursor-not-allowed"
                : "text-text-secondary hover:text-text-primary hover:bg-app-card"
            )}
            title="导出标注"
            aria-label="导出标注"
          >
            <Download className="w-4 h-4" />
          </button>

          {/* 全部清除 */}
          <button
            onClick={handleClearAll}
            disabled={annotations.length === 0}
            className={cn(
              "p-1.5 rounded-lg transition-colors cursor-pointer",
              annotations.length === 0
                ? "text-text-muted/30 cursor-not-allowed"
                : "text-red-400 hover:bg-red-400/10"
            )}
            title="清除所有标注"
            aria-label="清除所有标注"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 快速添加按钮 */}
      <button
        onClick={handleQuickAdd}
        className={cn(
          "flex items-center justify-center gap-2 py-2.5 rounded-xl",
          "border-2 border-dashed border-app-border",
          "text-sm font-medium text-text-secondary",
          "hover:border-primary/50 hover:text-primary hover:bg-primary/5",
          "transition-colors cursor-pointer"
        )}
      >
        <Plus className="w-4 h-4" />
        添加标注
      </button>

      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileImport}
        className="hidden"
        aria-hidden="true"
      />

      {/* 标注列表 */}
      <div className="flex-1 space-y-2 min-h-0">
        {annotations.length === 0 ? (
          /* 空状态提示 */
          <div className="flex flex-col items-center justify-center py-12 text-text-muted">
            <MessageSquare className="w-12 h-12 mb-3 opacity-30" />
            <p className="text-sm">暂无标注</p>
            <p className="text-xs mt-1">点击上方按钮或直接在谱面上点击</p>
          </div>
        ) : (
          /* 标注列表 */
          <ul className="space-y-2">
            {annotations.map((anno) => (
              <li
                key={anno.id}
                className={cn(
                  "group p-3 rounded-xl bg-app-bg border border-app-border",
                  "hover:border-app-border/80 transition-all duration-150",
                  editingId === anno.id && "ring-2 ring-primary/30 border-primary/30"
                )}
              >
                {/* 标注头部 */}
                <div className="flex items-start gap-2">
                  {/* 颜色指示条 */}
                  <div
                    className="w-1 h-auto self-stretch rounded-full shrink-0 mt-1"
                    style={{ backgroundColor: anno.color || '#F97316' }}
                  />

                  {/* 内容区 */}
                  <div className="flex-1 min-w-0">
                    {/* 编辑模式：输入框 */}
                    {editingId === anno.id ? (
                      <input
                        type="text"
                        defaultValue={anno.text}
                        onBlur={(e) => {
                          if (e.target.value.trim()) {
                            updateText(anno.id, e.target.value.trim());
                          }
                          endEdit();
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            (e.target as HTMLInputElement).blur();
                          }
                          if (e.key === 'Escape') endEdit();
                        }}
                        autoFocus
                        className="w-full bg-transparent text-sm text-text-primary outline-none border-b border-primary/50 focus:border-primary"
                      />
                    ) : (
                      <>
                        {/* 文本内容 */}
                        <p 
                          className="text-sm text-text-primary cursor-pointer hover:text-primary transition-colors truncate"
                          onClick={() => startEdit(anno.id)}
                          style={{ color: anno.color || undefined }}
                        >
                          {anno.text}
                        </p>

                        {/* 元信息 */}
                        <div className="flex items-center gap-2 mt-1 text-xs text-text-muted">
                          <span>位置: ({anno.x.toFixed(0)}%, {anno.y.toFixed(0)}%)</span>
                          {anno.timestamp !== undefined && (
                            <span>{(anno.timestamp / 1000).toFixed(1)}s</span>
                          )}
                        </div>
                      </>
                    )}
                  </div>

                  {/* 操作按钮 */}
                  <button
                    onClick={() => deleteAnnotation(anno.id)}
                    className={cn(
                      "opacity-0 group-hover:opacity-100 p-1 rounded",
                      "text-text-muted hover:text-red-400 hover:bg-red-400/10",
                      "transition-all duration-150 shrink-0 cursor-pointer"
                    )}
                    aria-label={`删除标注: ${anno.text}`}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 底部说明 */}
      <div className="pt-3 border-t border-app-border">
        <p className="text-xs text-text-muted leading-relaxed">
          切换到「标注」视图模式后，可直接在谱面点击位置添加标注。
          标注可拖拽移动、右键更改颜色。
        </p>
      </div>
    </div>
  );
}

