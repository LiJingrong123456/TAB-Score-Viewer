/**
 * ============================================================
 * 文件名: App.tsx
 * 功能描述: TAB Score Viewer 主应用组件 - 吉他谱查看器根组件
 *          整合所有子组件：工具栏、文件目录树、查看器容器、控制面板、播放栏
 *          管理应用整体布局和状态流转
 *          支持格式：PNG, JPG, JPEG, WEBP, PDF, GTP(GP3-GP7)
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06 (v1.1.0 - 添加文件夹浏览功能)
 * 依赖项: React, 所有子组件, playerStore
 * ============================================================
 */

import { useCallback, useRef, useEffect } from 'react';
import { Toolbar } from '@/components/common/Toolbar';
import { FileLoader } from '@/components/common/FileLoader';
import { FileTree } from '@/components/common/FileTree';
import { ViewerContainer } from '@/components/Viewer/ViewerContainer';
import { ControlPanel } from '@/components/Controls/ControlPanel';
import { PlayBar } from '@/components/Controls/PlayBar';
import { useAppStore } from '@/stores/playerStore';
import { parseFileToScore } from '@/utils/fileParser';

/**
 * TAB Score Viewer 主应用组件
 * 
 * 功能概述：
 * 1. 多格式吉他谱文件查看（图片/PDF/Guitar Pro）
 * 2. 文件夹浏览（可展开的文件目录树）
 * 3. 播放控制（播放/暂停/进度拖拽/速度调节）
 * 4. 变速曲线编辑（仅图片/PDF模式）
 * 5. 文本标注系统（在谱面任意位置添加说明）
 * 6. 循环播放（全局循环/区域A-B循环）
 * 7. 缩放和平移（图片/PDF模式）
 * 
 * 布局结构 (v1.1.0):
 * ┌──────────────────────────────────────────────┐
 * │              Toolbar (固定顶部)               │
 * ├──────────┬──────────────────────┬────────────┤
 * │          │                      │            │
 * │ FileTree │    ViewerContainer   │ Control    │
 * │ (左侧)   │    (谱面显示区域)      │ Panel      │
 * │ 可折叠   │                      │ (右侧)     │
 * │          ├──────────────────────┤            │
 * │          │      PlayBar         │            │
 * └──────────┴──────────────────────┴────────────┘
 */
function App() {
  // 获取全局状态
  const { 
    currentFile, 
    scoreData, 
    folderRoot,
    showFilePanel,
    showSidebar,
    clearScoreFile,
  } = useAppStore();
  
  // 文件加载器ref（用于触发打开文件）
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * 处理打开单个文件请求
   * 触发隐藏的file input点击
   */
  const handleOpenFile = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  /**
   * 处理文件选择（来自Toolbar"打开"按钮）
   * 使用公共工具函数解析并加载文件
   */
  const handleFileInputChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const { file: scoreFile, data } = await parseFileToScore(file);
      useAppStore.getState().setScoreFile(scoreFile, data);
    } catch (error) {
      console.error('文件加载失败:', error);
      alert('文件加载失败，请检查文件是否损坏');
    }

    // 重置input以便重复选择同一文件
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

  /**
   * 处理选择文件夹请求
   * 通过FileTree组件内部处理，这里触发显示文件面板
   */
  const handleOpenFolder = useCallback(() => {
    // 确保文件面板可见
    if (!useAppStore.getState().showFilePanel) {
      useAppStore.getState().toggleFilePanel();
    }
  }, []);

  /**
   * 文件加载完成回调
   */
  const handleFileLoaded = useCallback(() => {
    console.log('文件加载完成');
  }, []);

  /** 是否有内容可以显示（有文件或文件夹） */
  const hasContent = scoreData || folderRoot;

  return (
    <div className="h-screen flex flex-col bg-app-bg overflow-hidden font-sans">
      {/* ====== 隐藏的文件选择input ====== */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".png,.jpg,.jpeg,.webp,.bmp,.gif,.pdf,.gtp,.gp3,.gp4,.gp5,.gp6,.gp7,.ptb,.tef"
        onChange={handleFileInputChange}
        className="hidden"
        aria-hidden="true"
        id="__tab_file_input__"
      />

      {/* ====== 顶部工具栏 ====== */}
      <Toolbar 
        onOpenFile={handleOpenFile} 
        onOpenFolder={handleOpenFolder}
      />

      {/* ====== 主内容区域 ====== */}
      <main className="flex-1 flex overflow-hidden relative">
        {hasContent ? (
          /* 有内容时的三栏布局 */
          <>
            {/* 左侧：文件目录树（可折叠） */}
            {showFilePanel && (
              <div className="w-64 shrink-0 border-r border-app-border overflow-hidden">
                <FileTree />
              </div>
            )}

            {/* 中间：谱面查看器 + 播放栏 */}
            <div className="flex-1 flex flex-col min-w-0">
              <ViewerContainer />
              <PlayBar />
            </div>

            {/* 右侧：控制面板（可折叠） */}
            {showSidebar && (
              <ControlPanel />
            )}
          </>
        ) : (
          /* 无内容时：显示文件加载器（居中） */
          <div className="flex-1 flex items-center justify-center p-8 overflow-auto">
            <div className="w-full max-w-2xl animate-fade-in">
              <FileLoader onLoad={handleFileLoaded} />
              
              {/* 快捷提示 */}
              <div className="mt-6 text-center text-sm text-text-muted space-y-1">
                <p>支持拖拽文件到此区域快速打开</p>
                <p>或使用工具栏的「文件夹」按钮浏览整个目录</p>
                <p className="text-xs opacity-60 mt-2">
                  支持格式：PNG · JPG · JPEG · WEBP · PDF · GP3-GP7 · GTP
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ====== 全局快捷键监听 ====== */}
      <GlobalHotkeys />
    </div>
  );
}

/**
 * 全局快捷键组件
 * 监听键盘事件提供快捷操作支持
 * 
 * 快捷键列表：
 * - Space: 播放 / 暂停
 * - Ctrl+←: 减速 (-0.1x)
 * - Ctrl+→: 加速 (+0.1x)
 */
function GlobalHotkeys() {
  const { togglePlayPause, setPlaybackRate, playbackRate } = useAppStore();

  /**
   * 键盘事件处理
   */
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // 忽略输入框内的按键
    const target = e.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
      return;
    }

    switch (e.code) {
      case 'Space':
        // 空格键：播放/暂停
        e.preventDefault();
        togglePlayPause();
        break;

      case 'ArrowLeft':
        // 左箭头：减速
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          setPlaybackRate(Math.max(0.25, playbackRate - 0.1));
        }
        break;

      case 'ArrowRight':
        // 右箭头：加速
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          setPlaybackRate(Math.min(4.0, playbackRate + 0.1));
        }
        break;

      default:
        break;
    }
  }, [togglePlayPause, setPlaybackRate, playbackRate]);

  // 绑定键盘事件
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return null; // 不渲染任何UI
}

export default App;
