/**
 * ============================================================
 * 文件名: PdfViewer.tsx
 * 功能描述: PDF查看器组件 - 显示PDF格式的吉他谱
 *          基于 react-pdf (pdf.js) 实现
 *          支持：分页显示、缩放、页面导航
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: React, react-pdf, playerStore, types
 *          开源项目: react-pdf v7.x (基于pdf.js)
 * ============================================================
 */

import { useState, useCallback, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { useAppStore } from '@/stores/playerStore';
import type { PdfScoreData } from '@/types';
import { cn } from '@/utils/cn';

// 配置PDF.js worker - 使用CDN加载
// 调用开源项目: pdfjs-dist v4.x
pdfjs.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.mjs`;

interface PdfViewerProps {
  /** PDF谱面数据 */
  data: PdfScoreData;
}

/**
 * PDF查看器组件
 * 用于显示PDF格式的吉他谱，支持分页浏览和缩放
 */
export function PdfViewer({ data }: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number>(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageWidth, setPageWidth] = useState(0);

  const { zoom } = useAppStore();

  /**
   * PDF文档加载成功回调
   */
  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setCurrentPage(1);
  }, []);

  /**
   * 计算容器宽度用于自适应PDF渲染
   */
  useEffect(() => {
    const updateWidth = () => {
      // 假设容器最大宽度约900px，留出边距
      const width = Math.min(window.innerWidth - 100, 900) * zoom.scale;
      setPageWidth(width);
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, [zoom.scale]);

  /**
   * 翻到上一页
   */
  const goToPrevPage = useCallback(() => {
    setCurrentPage((prev) => Math.max(1, prev - 1));
  }, []);

  /**
   * 翻到下一页
   */
  const goToNextPage = useCallback(() => {
    setCurrentPage((prev) => Math.min(numPages, prev + 1));
  }, [numPages]);

  return (
    <div className="flex flex-col items-center h-full overflow-auto scrollbar-custom p-4">
      {/* PDF文档容器 */}
      <Document
        file={data.url}
        onLoadSuccess={onDocumentLoadSuccess}
        loading={
          <div className="flex items-center justify-center h-64">
            <div className="flex flex-col items-center gap-3">
              {/* 加载动画 */}
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-text-secondary">正在加载PDF...</span>
            </div>
          </div>
        }
        error={
          <div className="flex flex-col items-center justify-center h-64 text-red-400">
            <p>PDF加载失败</p>
            <p className="text-sm text-text-muted mt-1">请检查文件是否损坏</p>
          </div>
        }
        className="flex justify-center"
      >
        {/* 当前页 */}
        <Page
          pageNumber={currentPage}
          width={pageWidth || 800}
          renderTextLayer={false}
          renderAnnotationLayer={false}
          className="shadow-lg rounded-lg"
          loading={
            <div className="flex items-center justify-center" style={{ width: pageWidth || 800, height: (pageWidth || 800) * 1.414 }}>
              <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          }
        />
      </Document>

      {/* 页面导航栏 */}
      {numPages > 1 && (
        <div className="flex items-center gap-3 mt-4 px-4 py-2 rounded-xl bg-app-surface border border-app-border">
          {/* 上一页按钮 */}
          <button
            onClick={goToPrevPage}
            disabled={currentPage <= 1}
            className={cn(
              "p-1.5 rounded-lg transition-colors",
              currentPage <= 1 
                ? "text-text-muted cursor-not-allowed" 
                : "hover:bg-app-card text-text-secondary cursor-pointer"
            )}
            aria-label="上一页"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </button>

          {/* 页码信息 */}
          <span className="text-sm text-text-secondary font-mono min-w-[80px] text-center">
            {currentPage} / {numPages}
          </span>

          {/* 下一页按钮 */}
          <button
            onClick={goToNextPage}
            disabled={currentPage >= numPages}
            className={cn(
              "p-1.5 rounded-lg transition-colors",
              currentPage >= numPages 
                ? "text-text-muted cursor-not-allowed" 
                : "hover:bg-app-card text-text-secondary cursor-pointer"
            )}
            aria-label="下一页"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </button>
        </div>
      )}

      {/* 缩放提示 */}
      <div className="mt-3 px-3 py-1 rounded-lg bg-app-bg/60 text-xs text-text-muted">
        缩放: {Math.round(zoom.scale * 100)}%
      </div>
    </div>
  );
}
