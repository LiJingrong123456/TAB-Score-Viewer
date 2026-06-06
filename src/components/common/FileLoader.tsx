/**
 * ============================================================
 * 文件名: FileLoader.tsx
 * 功能描述: 文件加载器组件 - 负责打开和加载吉他谱文件
 *          支持拖拽上传、点击选择等多种方式
 *          自动识别文件格式（图片/PDF/GTP）
 *          使用公共工具函数 fileParser.ts 进行文件解析
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06 (v1.1.0 - 使用公共文件解析工具)
 * 依赖项: React, playerStore, fileParser工具, types
 * ============================================================
 */

import { useCallback, useRef, useState } from 'react';
import { useAppStore } from '@/stores/playerStore';
import { parseFileToScore } from '@/utils/fileParser';
import type { SupportedFormat } from '@/types';
import { cn } from '@/utils/cn';

interface FileLoaderProps {
  /** 加载完成回调 */
  onLoad?: () => void;
}

/**
 * 文件加载器组件
 * 提供多种方式加载谱面文件：点击选择、拖拽上传
 */
export function FileLoader({ onLoad }: FileLoaderProps) {
  const { setScoreFile } = useAppStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  /**
   * 处理文件选择/拖拽
   * 使用公共工具函数 parseFileToScore 统一处理文件解析
   */
  const processFile = useCallback(async (file: File) => {
    // 先检查格式是否支持
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    const supportedExts = new Set(['png','jpg','jpeg','webp','bmp','gif','pdf','gtp','gp3','gp4','gp5','gp6','gp7','ptb','tef']);
    
    if (!supportedExts.has(ext)) {
      alert(`不支持的文件格式: ${file.name}\n支持格式: PNG, JPG, WEBP, PDF, GP3-GP7, GTP`);
      return;
    }

    try {
      // 使用公共工具函数解析文件
      const { file: scoreFile, data } = await parseFileToScore(file);
      setScoreFile(scoreFile, data);
      onLoad?.();
    } catch (error) {
      console.error('文件处理失败:', error);
      alert('文件处理失败，请检查文件是否损坏');
    }
  }, [setScoreFile, onLoad]);

  /**
   * 处理input文件选择变化
   */
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    // 重置input以便重复选择同一文件
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [processFile]);

  /**
   * 处理拖拽事件
   */
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }, [processFile]);

  /** 点击触发文件选择 */
  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <div
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        "flex flex-col items-center justify-center p-12",
        "border-2 border-dashed rounded-2xl cursor-pointer",
        "transition-all duration-300 ease-out",
        "min-h-[400px] min-w-[300px]",
        isDragOver
          ? "border-primary bg-primary/10 scale-[1.02]"
          : "border-app-border hover:border-primary/50 bg-app-surface/50 hover:bg-app-surface"
      )}
      role="button"
      tabIndex={0}
      aria-label="点击或拖拽上传吉他谱文件"
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
    >
      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".png,.jpg,.jpeg,.webp,.bmp,.gif,.pdf,.gtp,.gp3,.gp4,.gp5,.gp6,.gp7,.ptb,.tef"
        onChange={handleInputChange}
        className="hidden"
        aria-hidden="true"
      />

      {/* 上传图标区域 */}
      <div className={cn(
        "w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-colors duration-300",
        isDragOver ? "bg-primary/20" : "bg-app-card"
      )}>
        <svg 
          className={cn("w-10 h-10 transition-colors", isDragOver ? "text-primary" : "text-text-muted")}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor" 
          strokeWidth={1.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
        </svg>
      </div>

      {/* 提示文字 */}
      <h3 className="text-lg font-semibold text-text-primary mb-2">
        {isDragOver ? '松开以上传文件' : '打开吉他谱'}
      </h3>
      <p className="text-sm text-text-secondary text-center max-w-xs mb-4">
        点击选择文件或拖拽到此处
      </p>

      {/* 支持格式标签 */}
      <div className="flex flex-wrap gap-2 justify-center">
        {['PNG', 'JPG', 'WEBP', 'PDF', 'GTP/GP'].map((fmt) => (
          <span
            key={fmt}
            className="px-3 py-1 text-xs font-medium rounded-full bg-app-card text-text-secondary border border-app-border"
          >
            {fmt}
          </span>
        ))}
      </div>
    </div>
  );
}
