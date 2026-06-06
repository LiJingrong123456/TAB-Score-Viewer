/**
 * ============================================================
 * 文件名: Toolbar.tsx
 * 功能描述: 工具栏组件 - 应用顶部导航栏
 *          包含：Logo、文件操作按钮（打开文件/选择文件夹）、视图切换、设置入口
 *          更新：新增选择文件夹按钮、切换左侧文件面板按钮
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06 (v1.1.0 - 添加文件夹功能)
 * 依赖项: React, Lucide图标, playerStore
 * ============================================================ */

import { Music, Upload, Settings, PanelLeftClose, PanelLeft, FolderPlus, FolderOpen } from 'lucide-react';
import { useAppStore } from '@/stores/playerStore';
import { cn } from '@/utils/cn';

interface ToolbarProps {
  /** 打开单个文件的回调 */
  onOpenFile?: () => void;
  /** 选择文件夹的回调 */
  onOpenFolder?: () => void;
}

/**
 * 工具栏组件
 * 应用顶部固定导航栏，提供全局操作入口
 * 
 * 布局：
 * [Logo] [文件名]              [打开] [文件夹] [面板] [设置]
 */
export function Toolbar({ onOpenFile, onOpenFolder }: ToolbarProps) {
  const { 
    currentFile, 
    showSidebar, 
    toggleSidebar,
    folderRoot,
    showFilePanel,
    toggleFilePanel,
    clearScoreFile,
    clearFolderRoot,
  } = useAppStore();

  return (
    <header className="flex items-center justify-between h-14 px-4 bg-app-surface border-b border-app-border shrink-0">
      {/* 左侧：Logo + 文件/文件夹信息 */}
      <div className="flex items-center gap-3 min-w-0">
        {/* Logo */}
        <div className="flex items-center gap-2 shrink-0">
          <Music className="w-6 h-6 text-primary" />
          <span className="font-display text-lg text-text-primary hidden sm:block">
            TAB Viewer
          </span>
        </div>

        {/* 当前文件或文件夹信息 */}
        {(currentFile || folderRoot) && (
          <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-lg bg-app-card truncate max-w-[350px]">
            {/* 文件夹图标 */}
            {folderRoot && !currentFile && (
              <FolderOpen className="w-4 h-4 text-accent shrink-0" />
            )}
            
            {/* 显示名称 */}
            <span className="text-sm text-text-secondary truncate">
              {currentFile ? currentFile.name : folderRoot?.name}
            </span>

            {/* 关闭按钮 */}
            <button
              onClick={(e) => { 
                e.stopPropagation(); 
                currentFile ? clearScoreFile() : clearFolderRoot();
              }}
              className="shrink-0 p-0.5 rounded hover:bg-app-border transition-colors cursor-pointer"
              aria-label={currentFile ? "关闭文件" : "关闭文件夹"}
            >
              <svg className="w-3.5 h-3.5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* 右侧：操作按钮组 */}
      <div className="flex items-center gap-2">
        {/* 打开单个文件按钮 */}
        <button
          onClick={onOpenFile}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-lg",
            "text-sm font-medium transition-all duration-200",
            "bg-primary hover:bg-primary-hover text-white",
            "cursor-pointer"
          )}
          aria-label="打开文件"
          title="打开单个吉他谱文件"
        >
          <Upload className="w-4 h-4" />
          <span className="hidden sm:inline">打开</span>
        </button>

        {/* 选择文件夹按钮 */}
        <button
          onClick={onOpenFolder}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-lg",
            "text-sm font-medium transition-all duration-200",
            "border",
            folderRoot
              ? "border-accent/50 bg-accent/10 text-accent hover:bg-accent/20"
              : "border-app-border text-text-secondary hover:text-text-primary hover:bg-app-card",
            "cursor-pointer"
          )}
          aria-label="选择文件夹"
          title="选择包含谱面的文件夹"
        >
          <FolderPlus className="w-4 h-4" />
          <span className="hidden sm:inline">文件夹</span>
        </button>

        {/* 切换左侧文件面板 */}
        <button
          onClick={toggleFilePanel}
          className={cn(
            "p-2 rounded-lg transition-colors duration-200",
            "hover:bg-app-card text-text-secondary hover:text-text-primary",
            "cursor-pointer",
            showFilePanel && "bg-primary/10 text-primary"
          )}
          aria-label={showFilePanel ? '隐藏文件面板' : '显示文件面板'}
          title={showFilePanel ? '隐藏文件目录' : '显示文件目录'}
        >
          <PanelLeft className="w-5 h-5" />
        </button>

        {/* 切换右侧控制面板 */}
        <button
          onClick={toggleSidebar}
          className={cn(
            "p-2 rounded-lg transition-colors duration-200",
            "hover:bg-app-card text-text-secondary hover:text-text-primary",
            "cursor-pointer",
            showSidebar && "bg-primary/10 text-primary"
          )}
          aria-label={showSidebar ? '隐藏控制面板' : '显示控制面板'}
          title={showSidebar ? '隐藏工具面板' : '显示工具面板'}
        >
          {showSidebar ? (
            <PanelLeftClose className="w-5 h-5" />
          ) : (
            <PanelLeft className="w-5 h-5" />
          )}
        </button>

        {/* 设置按钮(预留) */}
        <button
          className={cn(
            "p-2 rounded-lg transition-colors duration-200",
            "hover:bg-app-card text-text-secondary hover:text-text-primary",
            "cursor-pointer"
          )}
          aria-label="设置"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
