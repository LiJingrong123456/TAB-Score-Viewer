/**
 * ============================================================
 * 文件名: ControlPanel.tsx
 * 功能描述: 控制面板容器组件 - 侧边栏控制区
 *          整合：速度曲线编辑器、标注管理、视图模式切换
 *          可折叠的侧边栏布局
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: React, 子组件, playerStore
 * ============================================================
 */

import { MessageSquare, Gauge, List } from 'lucide-react';
import { useAppStore } from '@/stores/playerStore';
import { SpeedCurve } from './SpeedCurve';
import { AnnotationManager } from '../Annotation/NoteEditor';
import { cn } from '@/utils/cn';

/** 视图模式选项配置 */
const VIEW_MODES = [
  { id: 'viewer' as const, label: '查看', icon: List },
  { id: 'annotation' as const, label: '标注', icon: MessageSquare },
  { id: 'speed-curve' as const, label: '速度', icon: Gauge },
];

/**
 * 控制面板组件
 * 右侧可折叠侧边栏，包含各种工具面板
 */
export function ControlPanel() {
  const { showSidebar, viewMode, setViewMode, scoreData } = useAppStore();

  // 如果侧边栏隐藏，不渲染内容（但保留切换按钮）
  if (!showSidebar) {
    return null;
  }

  /** 是否为图片/PDF格式（支持速度曲线和标注） */
  const isImageOrPdf = scoreData?.type === 'image' || scoreData?.type === 'pdf';

  return (
    <aside className="w-80 shrink-0 bg-app-surface border-l border-app-border flex flex-col overflow-hidden">
      {/* 视图模式切换标签页 */}
      <div className="flex border-b border-app-border">
        {VIEW_MODES.map(({ id, label, icon: Icon }) => {
          // GTP模式下禁用标注和速度曲线标签
          const disabled = !isImageOrPdf && (id === 'annotation' || id === 'speed-curve');
          
          return (
            <button
              key={id}
              onClick={() => !disabled && setViewMode(id)}
              disabled={disabled}
              className={cn(
                "flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium transition-colors cursor-pointer",
                viewMode === id && !disabled
                  ? "text-primary border-b-2 border-primary bg-primary/5"
                  : disabled
                    ? "text-text-muted/40 cursor-not-allowed"
                    : "text-text-secondary hover:text-text-primary hover:bg-app-card"
              )}
              aria-label={`切换到${label}模式`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          );
        })}
      </div>

      {/* 面板内容区域 */}
      <div className="flex-1 overflow-auto scrollbar-custom">
        {viewMode === 'speed-curve' && (
          isImageOrPdf ? (
            <SpeedCurve />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-text-muted p-8 text-center">
              <Gauge className="w-12 h-12 mb-3 opacity-30" />
              <p className="text-sm">速度曲线仅支持</p>
              <p className="text-sm">图片和PDF格式</p>
            </div>
          )
        )}

        {viewMode === 'annotation' && (
          isImageOrPdf ? (
            <AnnotationManager />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-text-muted p-8 text-center">
              <MessageSquare className="w-12 h-12 mb-3 opacity-30" />
              <p className="text-sm">文本标注仅支持</p>
              <p className="text-sm">图片和PDF格式</p>
            </div>
          )
        )}

        {viewMode === 'viewer' && (
          <div className="p-4 space-y-4">
            <h3 className="text-sm font-semibold text-text-primary">查看选项</h3>
            
            {/* 缩放控制 */}
            <div className="space-y-2">
              <label className="text-xs text-text-secondary">缩放比例</label>
              <input
                type="range"
                min="10"
                max="500"
                value={useAppStore.getState().zoom.scale * 100}
                onChange={(e) => useAppStore.getState().setZoomScale(parseInt(e.target.value) / 100)}
                className="w-full accent-primary"
              />
              <div className="flex justify-between text-xs text-text-muted">
                <span>10%</span>
                <span>{Math.round(useAppStore.getState().zoom.scale * 100)}%</span>
                <span>500%</span>
              </div>
            </div>

            {/* 快捷键说明 */}
            <div className="pt-4 border-t border-app-border">
              <h4 className="text-xs font-semibold text-text-secondary mb-2">快捷操作</h4>
              <ul className="space-y-1.5 text-xs text-text-muted">
                <li className="flex justify-between">
                  <span>滚轮缩放</span>
                  <kbd className="px-1.5 py-0.5 rounded bg-app-card font-mono">Scroll</kbd>
                </li>
                <li className="flex justify-between">
                  <span>拖动平移</span>
                  <kbd className="px-1.5 py-0.5 rounded bg-app-card font-mono">Drag</kbd>
                </li>
                <li className="flex justify-between">
                  <span>重置视图</span>
                  <kbd className="px-1.5 py-0.5 rounded bg-app-card font-mono">双击</kbd>
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
