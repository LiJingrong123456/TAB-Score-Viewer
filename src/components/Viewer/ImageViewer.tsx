/**
 * ============================================================
 * 文件名: ImageViewer.tsx
 * 功能描述: 图片查看器组件 - 显示图片格式的吉他谱
 *          支持：缩放、平移、鼠标滚轮缩放、双击重置
 *          图片格式支持：PNG、JPG、JPEG、WEBP、BMP、GIF
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: React, playerStore, types
 * ============================================================
 */

import { useRef, useEffect, useCallback, useState } from 'react';
import { useAppStore } from '@/stores/playerStore';
import type { ImageScoreData } from '@/types';
import { cn } from '@/utils/cn';

interface ImageViewerProps {
  /** 图片谱面数据 */
  data: ImageScoreData;
}

/**
 * 图片查看器组件
 * 用于显示图片格式的吉他谱，支持缩放和平移操作
 */
export function ImageViewer({ data }: ImageViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const dragStart = useRef({ x: 0, y: 0 });
  const positionStart = useRef({ x: 0, y: 0 });

  const { zoom, setZoomScale } = useAppStore();

  /**
   * 鼠标滚轮缩放
   * 以鼠标位置为中心进行缩放
   */
  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    const newScale = Math.max(0.1, Math.min(5.0, zoom.scale + delta));
    
    setZoomScale(newScale);
  }, [zoom.scale, setZoomScale]);

  /**
   * 鼠标按下开始平移
   */
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    // 只响应左键或中键
    if (e.button !== 0 && e.button !== 1) return;
    
    setIsDragging(true);
    dragStart.current = { x: e.clientX, y: e.clientY };
    positionStart.current = { ...position };
  }, [position]);

  /**
   * 鼠标移动进行平移
   */
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging || !containerRef.current) return;

    const dx = e.clientX - dragStart.current.x;
    const dy = e.clientY - dragStart.current.y;

    setPosition({
      x: positionStart.current.x + dx,
      y: positionStart.current.y + dy,
    });
  }, [isDragging]);

  /**
   * 鼠标释放结束平移
   */
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  /**
   * 双击重置视图
   */
  const handleDoubleClick = useCallback(() => {
    setZoomScale(1.0);
    setPosition({ x: 0, y: 0 });
  }, [setZoomScale]);

  // 绑定滚轮事件
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, [handleWheel]);

  // 全局鼠标释放监听（防止拖出容器后卡住）
  useEffect(() => {
    if (!isDragging) return;
    
    const handleGlobalMouseUp = () => setIsDragging(false);
    window.addEventListener('mouseup', handleGlobalMouseUp);
    return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
  }, [isDragging]);

  return (
    <div
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onDoubleClick={handleDoubleClick}
      className={cn(
        "relative w-full h-full overflow-hidden cursor-grab active:cursor-grabbing",
        "bg-[#1a1a2e] flex items-center justify-center"
      )}
      style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
    >
      {/* 图片容器 - 应用变换 */}
      <div
        className="absolute origin-center transition-transform duration-75"
        style={{
          transform: `translate(${position.x}px, ${position.y}px) scale(${zoom.scale})`,
        }}
      >
        {/* 实际图片元素 */}
        <img
          src={data.src}
          alt="吉他谱"
          className="max-w-none select-none pointer-events-none"
          draggable={false}
          style={{
            width: data.naturalWidth > 1200 ? '1200px' : undefined,
            height: 'auto',
          }}
        />

        {/* 标注层容器占位 - 由父组件AnnotationLayer覆盖 */}
      </div>

      {/* 缩放提示 */}
      <div className="absolute bottom-4 left-4 px-3 py-1.5 rounded-lg bg-app-bg/80 backdrop-blur-sm text-xs text-text-secondary font-mono">
        {Math.round(zoom.scale * 100)}%
      </div>

      {/* 操作提示 */}
      <div className="absolute top-4 left-4 px-3 py-1.5 rounded-lg bg-app-bg/60 backdrop-blur-sm text-xs text-text-muted">
        滚轮缩放 · 拖动平移 · 双击重置
      </div>
    </div>
  );
}
