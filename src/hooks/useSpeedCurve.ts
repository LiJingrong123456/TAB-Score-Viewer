/**
 * ============================================================
 * 文件名: useSpeedCurve.ts
 * 功能描述: 速度曲线管理Hook - 管理变速播放的速度曲线
 *          - 速度曲线的增删改
 *          - 速度插值计算
 *          - 曲线重置和预设
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: playerStore, types, React
 * ============================================================
 */

import { useCallback } from 'react';
import { useAppStore } from '@/stores/playerStore';
import type { SpeedControlPoint, SpeedCurveConfig } from '@/types';

/** 预设速度曲线配置 */
export interface SpeedPreset {
  /** 预设名称 */
  name: string;
  /** 预设描述 */
  description: string;
  /** 控制点数据 */
  points: Omit<SpeedControlPoint, 'id'>[];
}

/** 内置预设曲线 */
export const SPEED_PRESETS: SpeedPreset[] = [
  {
    name: '恒定速度',
    description: '全程保持相同速度',
    points: [
      { time: 0, speed: 1.0 },
      { time: 100, speed: 1.0 },
    ],
  },
  {
    name: '渐入渐出',
    description: '开头慢速逐渐加速，结尾减速',
    points: [
      { time: 0, speed: 0.5 },
      { time: 20, speed: 1.0 },
      { time: 80, speed: 1.0 },
      { time: 100, speed: 0.5 },
    ],
  },
  {
    name: '渐进加速',
    description: '从慢到快逐步加速',
    points: [
      { time: 0, speed: 0.5 },
      { time: 50, speed: 0.8 },
      { time: 100, speed: 1.5 },
    ],
  },
  {
    name: '难点慢练',
    description: '中间段落放慢练习',
    points: [
      { time: 0, speed: 1.0 },
      { time: 30, speed: 1.0 },
      { time: 50, speed: 0.6 },
      { time: 70, speed: 1.0 },
      { time: 100, speed: 1.0 },
    ],
  },
];

/**
 * 速度曲线管理自定义Hook
 * 提供速度曲线的完整操作能力
 * 
 * @returns 速度曲线操作方法和预设列表
 */
export function useSpeedCurve() {
  const {
    speedCurve,
    setSpeedCurve,
    addSpeedPoint,
    removeSpeedPoint,
    updateSpeedPoint,
  } = useAppStore();

  /**
   * 应用预设曲线
   * @param preset - 预设配置
   */
  const applyPreset = useCallback((preset: SpeedPreset) => {
    // 清除旧点并添加新点
    const newPoints = preset.points.map((p, index) => ({
      ...p,
      id: `preset-${preset.name}-${index}`,
    }));
    setSpeedCurve({ points: newPoints, enabled: true });
  }, [setSpeedCurve]);

  /**
   * 重置为默认曲线（恒定速度）
   */
  const resetCurve = useCallback(() => {
    applyPreset(SPEED_PRESETS[0]);
  }, [applyPreset]);

  /**
   * 切换速度曲线启用状态
   */
  const toggleEnabled = useCallback(() => {
    setSpeedCurve({ enabled: !speedCurve.enabled });
  }, [speedCurve.enabled, setSpeedCurve]);

  /**
   * 设置插值方式
   * @param interpolation - 插值方式
   */
  const setInterpolation = useCallback((interpolation: SpeedCurveConfig['interpolation']) => {
    setSpeedCurve({ interpolation });
  }, [setSpeedCurve]);

  /**
   * 获取指定时间点的速度值
   * @param timePercent - 时间位置(百分比 0-100)
   * @returns 速度倍率
   */
  const getSpeedAtPosition = useCallback((timePercent: number): number => {
    const points = speedCurve.points;
    if (points.length < 2) return 1.0;

    // 边界检查
    if (timePercent <= points[0].time) return points[0].speed;
    if (timePercent >= points[points.length - 1].time) return points[points.length - 1].speed;

    // 找到对应区间并插值
    for (let i = 0; i < points.length - 1; i++) {
      if (timePercent >= points[i].time && timePercent <= points[i + 1].time) {
        const range = points[i + 1].time - points[i].time;
        if (range === 0) return points[i].speed;

        const t = (timePercent - points[i].time) / range;
        
        switch (speedCurve.interpolation) {
          case 'linear':
            return points[i].speed + (points[i + 1].speed - points[i].speed) * t;
          case 'step':
            return points[i].speed;
          case 'bezier': // 简化贝塞尔，使用平滑step
            const smoothT = t * t * (3 - 2 * t); // smoothstep
            return points[i].speed + (points[i + 1].speed - points[i].speed) * smoothT;
          default:
            return points[i].speed;
        }
      }
    }

    return 1.0;
  }, [speedCurve]);

  return {
    // 当前状态
    curve: speedCurve,
    presets: SPEED_PRESETS,

    // 操作方法
    applyPreset,
    resetCurve,
    toggleEnabled,
    setInterpolation,
    addSpeedPoint,
    removeSpeedPoint,
    updateSpeedPoint,
    getSpeedAtPosition,
  };
}
