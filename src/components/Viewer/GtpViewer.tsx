/**
 * ============================================================
 * 文件名: GtpViewer.tsx
 * 功能描述: GTP(Guitar Pro)查看器组件 - 解析和播放Guitar Pro文件
 *          基于 @coderline/alphatab 开源库实现
 *          支持：谱面渲染、MIDI播放、音轨切换、速度控制
 *          兼容格式：GP3, GP4, GP5, GP6, GP7, GTP, PTB, TEF
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: React, @coderline/alphatab, playerStore, types
 *          开源项目: @coderline/alphatab v1.3+ (MPL-2.0)
 * ============================================================
 */

import { useRef, useEffect, useCallback } from 'react';
import { AlphaTabApi } from '@coderline/alphatab';
import { useAppStore } from '@/stores/playerStore';
import type { GtpScoreData } from '@/types';
import { cn } from '@/utils/cn';

interface GtpViewerProps {
  /** GTP谱面数据 */
  data: GtpScoreData;
}

/**
 * GTP查看器组件
 * 使用AlphaTab开源库解析和渲染Guitar Pro格式的吉他谱
 * 支持完整的播放功能和可视化显示
 */
export function GtpViewer({ data }: GtpViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const apiRef = useRef<AlphaTabApi | null>(null);

  const { 
    player,
    setDuration,
    setCurrentTime,
    setPlayState,
    setPlaybackRate,
    scoreData,
  } = useAppStore();

  /**
   * 初始化AlphaTab实例
   * 在组件挂载和数据就绪时调用
   */
  useEffect(() => {
    if (!containerRef.current || !data.data) return;

    // 清理旧实例
    if (apiRef.current) {
      apiRef.current.destroy();
      apiRef.current = null;
    }

    // 创建新的AlphaTab实例
    // 使用开源项目 @coderline/alphatab 进行GTP文件解析和渲染
    const api = new AlphaTabApi(containerRef.current, {
      // 核心配置
      file: data.data as any,
      
      // 显示配置
      display: {
        // 显示布局模式
        layoutMode: 'Page',
        // 缩放级别 (可调整范围: 0.5 - 2.0)
        scale: 1.0,
        // 是否显示和弦图
        chordDiagram: true,
      },

      // 播放器配置
      player: {
        // 是否启用声音输出
        enablePlayer: true,
        // 音量 (0.0 - 1.0)，默认0.8
        soundFont: 'https://cdn.jsdelivr.net/npm/@coderline/alphatab@latest/dist/soundfont/sonivox.sf2',
        // 回调函数
      },
    });

    // 初始化完成回调
    api.ready.then(() => {
      console.log('AlphaTab初始化完成');
      
      // 获取曲目的总时长（毫秒）
      const duration = api.score.timeSignatureList.reduce((total, ts) => {
        return total + (ts.endTime - ts.startTime);
      }, 0);

      if (duration > 0) {
        setDuration(duration / 1000); // 转换为秒
      }

      // 监听播放位置更新
      api.player.on('playerPositionChanged', (position: any) => {
        setCurrentTime(position.currentTime / 1000); // 毫秒转秒
      });

      // 监听播放状态变化
      api.player.on('playerStateChanged', (state: any) => {
        switch (state) {
          case 'Playing':
            setPlayState('playing');
            break;
          case 'Paused':
            setPlayState('paused');
            break;
          case 'Stopped':
            setPlayState('idle');
            break;
        }
      });
    });

    apiRef.current = api;

    // 组件卸载时清理
    return () => {
      if (apiRef.current) {
        apiRef.current.destroy();
        apiRef.current = null;
      }
    };
  }, [data.data]); // 仅在数据变化时重新初始化

  /**
   * 同步外部播放控制到AlphaTab
   * 当用户通过UI控制播放时同步
   */
  useEffect(() => {
    if (!apiRef.current) return;

    const api = apiRef.current;

    // 同步播放速度
    api.player.playbackSpeed = player.playbackRate;

    // 同步音量
    api.player.volume = player.volume;
    
  }, [player.playbackRate, player.volume]);

  /**
   * 外部触发播放/暂停
   */
  useEffect(() => {
    if (!apiRef.current) return;

    switch (player.playState) {
      case 'playing':
        apiRef.current.play();
        break;
      case 'paused':
        apiRef.current.pause();
        break;
    }
  }, [player.playState]);

  /**
   * 手动跳转到指定时间点
   */
  useEffect(() => {
    if (!apiRef.current || !apiRef.current.player) return;
    // 注意：这里需要处理避免循环更新的逻辑
    // 实际跳转由PlayBar组件直接调用api实现
  }, []);

  return (
    <div className="relative w-full h-full overflow-auto scrollbar-custom bg-[#1a1a2e]">
      {/* AlphaTab渲染容器 */}
      <div
        ref={containerRef}
        className="alpha-tab-container w-full"
        style={{ minHeight: '100%' }}
      />

      {/* 加载提示 */}
      {!apiRef.current && (
        <div className="absolute inset-0 flex items-center justify-center bg-app-bg/50">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-text-secondary">正在解析Guitar Pro文件...</span>
          </div>
        </div>
      )}

      {/* 曲目信息 */}
      {scoreData?.type === 'gtp' && (scoreData as any).title && (
        <div className="absolute top-4 left-4 px-4 py-2 rounded-xl bg-app-bg/80 backdrop-blur-sm border border-app-border">
          <h3 className="font-display text-primary">{(scoreData as any).title}</h3>
          {(scoreData as any).artist && (
            <p className="text-sm text-text-secondary">{(scoreData as any).artist}</p>
          )}
        </div>
      )}
    </div>
  );
}
