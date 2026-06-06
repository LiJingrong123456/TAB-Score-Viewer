/**
 * ============================================================
 * 文件名: PlayBar.tsx
 * 功能描述: 播放进度条组件 - 核心播放控制UI
 *          包含：播放/暂停按钮、进度条(可拖拽)、时间显示
 *          支持区域循环选择(A-B点)、循环模式切换
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: React, usePlayer hook, playerStore, types
 * ============================================================
 */

import { useCallback, useRef, useState, useEffect } from 'react';
import { Play, Pause, SkipBack, SkipForward, Repeat, Repeat1 } from 'lucide-react';
import { usePlayer } from '@/hooks/usePlayer';
import { useAppStore } from '@/stores/playerStore';
import { cn } from '@/utils/cn';

/**
 * 格式化时间为 mm:ss 或 hh:mm:ss
 * @param seconds - 秒数
 * @returns 格式化时间字符串
 */
function formatTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return '00:00';
  
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);

  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

/**
 * 播放进度条组件
 * 提供完整的播放控制和进度显示功能
 */
export function PlayBar() {
  const {
    currentTime,
    duration,
    playState,
    loopMode,
    togglePlayPause,
    seekTo,
    cycleLoopMode,
  } = usePlayer();

  const { setPlaybackRate, playbackRate } = useAppStore();
  
  // 进度条拖拽状态
  const [isDragging, setIsDragging] = useState(false);
  const [dragProgress, setDragProgress] = useState(0);
  const progressRef = useRef<HTMLDivElement>(null);

  /** 当前进度百分比 */
  const progress = isDragging 
    ? dragProgress 
    : (duration > 0 ? (currentTime / duration) * 100 : 0);

  /**
   * 处理进度条点击/拖拽
   */
  const handleProgressClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressRef.current || !duration) return;

    const rect = progressRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const newProgress = Math.max(0, Math.min(100, (clickX / rect.width) * 100));
    
    setDragProgress(newProgress);
    seekTo((newProgress / 100) * duration);
  }, [duration, seekTo]);

  /**
   * 开始拖拽进度条
   */
  const handleDragStart = useCallback(() => {
    setIsDragging(true);
  }, []);

  /**
   * 拖拽中更新位置
   */
  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!progressRef.current) return;
      const rect = progressRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      setDragProgress(Math.max(0, Math.min(100, (x / rect.width) * 100)));
    };

    const handleMouseUp = () => {
      if (!isDragging || !duration) return;
      setIsDragging(false);
      seekTo((dragProgress / 100) * duration);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragProgress, duration, seekTo]);

  /**
   * 快退5秒
   */
  const handleSkipBack = useCallback(() => {
    seekTo(Math.max(0, currentTime - 5));
  }, [currentTime, seekTo]);

  /**
   * 快进5秒
   */
  const handleSkipForward = useCallback(() => {
    seekTo(Math.min(duration, currentTime + 5));
  }, [currentTime, duration, seekTo]);

  /**
   * 调整播放速度
   */
  const handleSpeedChange = useCallback((delta: number) => {
    setPlaybackRate(playbackRate + delta);
  }, [playbackRate, setPlaybackRate]);

  // 循环模式图标映射
  const LoopIcon = loopMode === 'all' ? Repeat1 : Repeat;

  return (
    <div className="flex flex-col gap-2 px-4 py-3 bg-app-surface border-t border-app-border">
      {/* 进度条 */}
      <div 
        ref={progressRef}
        onClick={handleProgressClick}
        onMouseDown={handleDragStart}
        className="relative h-2 rounded-full bg-app-card cursor-pointer group"
        role="slider"
        aria-label="播放进度"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress)}
        tabIndex={0}
      >
        {/* 已播放部分背景 */}
        <div 
          className="absolute inset-y-0 left-0 rounded-full bg-primary transition-[width] duration-75"
          style={{ width: `${progress}%` }}
        />

        {/* 循环区域高亮（仅region模式下显示） */}
        {loopMode === 'region' && (
          <div 
            className="absolute top-0 bottom-0 bg-accent/20 border-y border-accent/40"
            style={{
              left: `${useAppStore.getState().player.loopRegion.start}%`,
              width: `${useAppStore.getState().player.loopRegion.end - useAppStore.getState().player.loopRegion.start}%`,
            }}
          />
        )}

        {/* 拖拽手柄 */}
        <div 
          className={cn(
            "absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full",
            "bg-primary shadow-lg border-2 border-white",
            "opacity-0 group-hover:opacity-100 transition-opacity",
            "hover:scale-125",
            isDragging && "opacity-100 scale-125"
          )}
          style={{ left: `calc(${progress}% - 8px)` }}
        />
      </div>

      {/* 控制栏：播放按钮 + 时间 + 速度 + 循环 */}
      <div className="flex items-center justify-between gap-3">
        {/* 左侧：播放控制按钮组 */}
        <div className="flex items-center gap-1">
          {/* 循环模式切换 */}
          <button
            onClick={cycleLoopMode}
            className={cn(
              "p-2 rounded-lg transition-all duration-200 cursor-pointer",
              loopMode !== 'none' 
                ? "text-primary bg-primary/10" 
                : "text-text-secondary hover:text-text-primary hover:bg-app-card"
            )}
            title={`循环模式: ${loopMode === 'none' ? '关闭' : loopMode === 'all' ? '全部循环' : '区域循环'}`}
            aria-label="切换循环模式"
          >
            <LoopIcon className="w-4 h-4" />
          </button>

          {/* 快退5秒 */}
          <button
            onClick={handleSkipBack}
            className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-app-card transition-colors cursor-pointer"
            title="快退5秒"
            aria-label="快退5秒"
          >
            <SkipBack className="w-5 h-5" />
          </button>

          {/* 播放/暂停（主按钮） */}
          <button
            onClick={togglePlayPause}
            className={cn(
              "p-3 rounded-full transition-all duration-200 cursor-pointer",
              "bg-primary hover:bg-primary-hover text-white",
              "hover:scale-105 active:scale-95",
              "shadow-lg shadow-primary/25"
            )}
            aria-label={playState === 'playing' ? '暂停' : '播放'}
          >
            {playState === 'playing' ? (
              <Pause className="w-6 h-6" fill="currentColor" />
            ) : (
              <Play className="w-6 h-6 ml-0.5" fill="currentColor" />
            )}
          </button>

          {/* 快进5秒 */}
          <button
            onClick={handleSkipForward}
            className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-app-card transition-colors cursor-pointer"
            title="快进5秒"
            aria-label="快进5秒"
          >
            <SkipForward className="w-5 h-5" />
          </button>
        </div>

        {/* 中间：时间显示 */}
        <div className="flex items-center gap-2 font-mono text-sm min-w-[120px] justify-center">
          <span className="text-text-primary">{formatTime(currentTime)}</span>
          <span className="text-text-muted">/</span>
          <span className="text-text-secondary">{formatTime(duration)}</span>
        </div>

        {/* 右侧：速度控制 */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted">速度</span>
          <button
            onClick={() => handleSpeedChange(-0.1)}
            disabled={playbackRate <= 0.25}
            className="px-2 py-1 rounded text-sm text-text-secondary hover:bg-app-card disabled:opacity-30 cursor-pointer"
            aria-label="减速"
          >
            -
          </button>
          <span className="font-mono text-sm text-text-primary min-w-[48px] text-center">
            {playbackRate.toFixed(1)}x
          </span>
          <button
            onClick={() => handleSpeedChange(0.1)}
            disabled={playbackRate >= 4.0}
            className="px-2 py-1 rounded text-sm text-text-secondary hover:bg-app-card disabled:opacity-30 cursor-pointer"
            aria-label="加速"
          >
            +
          </button>
        </div>
      </div>
    </div>
  );
}
