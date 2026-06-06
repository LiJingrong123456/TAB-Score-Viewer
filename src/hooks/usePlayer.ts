/**
 * ============================================================
 * 文件名: usePlayer.ts
 * 功能描述: 播放控制Hook - 管理播放逻辑的核心Hook
 *          - 基于requestAnimationFrame的定时器系统
 *          - 支持速度曲线映射
 *          - 支持循环模式（全局/区域）
 *          - 自动与GTP文件的AlphaTab播放器同步
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: playerStore, types, React
 * ============================================================
 */

import { useCallback, useRef, useEffect } from 'react';
import { useAppStore } from '@/stores/playerStore';
import type { PlayState } from '@/types';

/**
 * 播放控制自定义Hook
 * 提供完整的播放控制功能，包括播放/暂停、进度更新、循环等
 * 
 * @returns 播放控制方法和状态引用
 */
export function usePlayer() {
  const {
    player,
    speedCurve,
    scoreData,
    setPlayState,
    setCurrentTime,
    setDuration,
    togglePlayPause,
    setLoopMode,
    setLoopRegion,
  } = useAppStore();

  // 动画帧ID引用
  const animationFrameRef = useRef<number | null>(null);
  // 上次更新时间戳
  const lastTimeRef = useRef<number>(0);
  // 开始播放的时间点
  const startTimeRef = useRef<number>(0);

  /**
   * 根据当前时间计算实际播放速度（考虑速度曲线）
   * @param currentTime - 当前播放时间(毫秒)
   * @returns 实际速度倍率
   */
  const getSpeedAtTime = useCallback((currentTime: number): number => {
    if (!speedCurve.enabled || speedCurve.points.length < 2) {
      return player.playbackRate;
    }

    // 计算当前位置的百分比
    const progress = player.duration > 0 ? (currentTime / player.duration) * 100 : 0;

    // 找到对应的控制点区间
    const points = speedCurve.points;
    for (let i = 0; i < points.length - 1; i++) {
      if (progress >= points[i].time && progress <= points[i + 1].time) {
        // 线性插值计算速度
        const range = points[i + 1].time - points[i].time;
        const localProgress = range > 0 ? (progress - points[i].time) / range : 0;
        const interpolatedSpeed =
          points[i].speed + (points[i + 1].speed - points[i].speed) * localProgress;
        return interpolatedSpeed * player.playbackRate;
      }
    }

    return player.playbackRate;
  }, [speedCurve, player.playbackRate, player.duration]);

  /**
   * 播放帧更新函数
   * 使用requestAnimationFrame实现平滑播放
   */
  const tick = useCallback(() => {
    if (player.playState !== 'playing') return;

    const now = performance.now();
    
    // 首次运行，初始化时间
    if (lastTimeRef.current === 0) {
      lastTimeRef.current = now;
      startTimeRef.current = now - player.currentTime / player.playbackRate;
    }

    // 计算经过的时间和当前速度
    const elapsed = now - startTimeRef.current;
    const currentSpeed = getSpeedAtTime(player.currentTime);
    
    // 更新当前时间
    let newTime = (elapsed * currentSpeed) / 1000; // 转换为秒

    // 处理区域循环
    if (player.loopMode === 'region' && player.duration > 0) {
      const regionStart = (player.loopRegion.start / 100) * player.duration;
      const regionEnd = (player.loopRegion.end / 100) * player.duration;
      
      if (newTime >= regionEnd) {
        newTime = regionStart;
        startTimeRef.current = now - regionStart / currentSpeed * 1000;
      }
    }
    // 处理全局循环
    else if (player.loopMode === 'all' && newTime >= player.duration) {
      newTime = 0;
      startTimeRef.current = now;
    }
    // 到达结尾停止
    else if (newTime >= player.duration) {
      newTime = player.duration;
      setPlayState('paused');
      setCurrentTime(newTime);
      return;
    }

    setCurrentTime(newTime);
    lastTimeRef.current = now;

    // 继续下一帧
    animationFrameRef.current = requestAnimationFrame(tick);
  }, [player.playState, player.currentTime, player.duration, player.loopMode, 
      player.loopRegion, player.playbackRate, getSpeedAtTime, setPlayState, setCurrentTime]);

  // 监听播放状态变化，启动/停止动画
  useEffect(() => {
    if (player.playState === 'playing') {
      lastTimeRef.current = 0;
      startTimeRef.current = performance.now() - (player.currentTime / player.playbackRate) * 1000;
      animationFrameRef.current = requestAnimationFrame(tick);
    } else {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [player.playState, tick, player.currentTime, player.playbackRate]);

  /**
   * 跳转到指定时间位置
   * @param time - 目标时间(秒)
   */
  const seekTo = useCallback((time: number) => {
    setCurrentTime(Math.max(0, Math.min(time, player.duration)));
    // 重置动画时间基准
    startTimeRef.current = performance.now() - (time / player.playbackRate) * 1000;
    lastTimeRef.current = 0;
  }, [setCurrentTime, player.duration, player.playbackRate]);

  /**
   * 切换循环模式
   * 循环顺序: none → all → region → none
   */
  const cycleLoopMode = useCallback(() => {
    const modes: PlayState[] = ['none', 'all', 'region'];
    const currentIndex = modes.indexOf(player.loopMode as any);
    const nextMode = modes[(currentIndex + 1) % modes.length] as any;
    setLoopMode(nextMode);
  }, [player.loopMode, setLoopMode]);

  return {
    // 当前状态
    currentTime: player.currentTime,
    duration: player.duration,
    playState: player.playState,
    playbackRate: player.playbackRate,
    volume: player.volume,
    loopMode: player.loopMode,
    loopRegion: player.loopRegion,

    // 控制方法
    togglePlayPause,
    seekTo,
    cycleLoopMode,
    setLoopMode,
    setLoopRegion,
    getSpeedAtTime,
  };
}
