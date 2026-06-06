/**
 * ============================================================
 * 文件名: SpeedCurve.tsx
 * 功能描述: 速度曲线编辑器组件 - 可视化编辑变速曲线
 *          使用 recharts 库绘制可交互的速度曲线图
 *          支持：添加/删除/拖拽控制点、预设选择、插值方式切换
 *          仅对图片/PDF格式谱子生效
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: React, recharts, useSpeedCurve hook
 *          开源项目: recharts v2.x (MIT)
 * ============================================================
 */

import { useState, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
} from 'recharts';
import { useSpeedCurve, SPEED_PRESETS } from '@/hooks/useSpeedCurve';
import { cn } from '@/utils/cn';
import type { SpeedControlPoint } from '@/types';

/**
 * 速度曲线编辑器组件
 * 提供可视化界面编辑播放速度随时间变化的曲线
 * 用于图片/PDF格式的谱面变速练习
 */
export function SpeedCurve() {
  const {
    curve,
    presets,
    applyPreset,
    resetCurve,
    toggleEnabled,
    setInterpolation,
    addSpeedPoint,
    removeSpeedPoint,
    updateSpeedPoint,
  } = useSpeedCurve();

  const [selectedPointId, setSelectedPointId] = useState<string | null>(null);

  /**
   * 图表点击添加新控制点
   */
  const handleChartClick = useCallback((data: any) => {
    if (data?.activePayload?.[0]) {
      const point = data.activePayload[0].payload as SpeedControlPoint;
      setSelectedPointId(point.id);
    }
  }, []);

  /**
   * 删除选中的控制点
   */
  const handleDeleteSelected = useCallback(() => {
    if (selectedPointId && curve.points.length > 2) {
      removeSpeedPoint(selectedPointId);
      setSelectedPointId(null);
    }
  }, [selectedPointId, removeSpeedPoint, curve.points.length]);

  /**
   * 更新选中点的速度值
   */
  const handleUpdateSelectedSpeed = useCallback((speed: number) => {
    if (selectedPointId) {
      updateSpeedPoint(selectedPointId, { speed });
    }
  }, [selectedPointId, updateSpeedPoint]);

  return (
    <div className="flex flex-col gap-4 p-4 h-full overflow-auto scrollbar-custom">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-text-primary">速度曲线</h3>
        
        {/* 启用开关 */}
        <button
          onClick={toggleEnabled}
          className={cn(
            "relative w-11 h-6 rounded-full transition-colors duration-200 cursor-pointer",
            curve.enabled ? "bg-primary" : "bg-app-card"
          )}
          role="switch"
          aria-checked={curve.enabled}
          aria-label={curve.enabled ? '禁用速度曲线' : '启用速度曲线'}
        >
          <span
            className={cn(
              "absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200",
              curve.enabled ? "left-[22px]" : "left-0.5"
            )}
          />
        </button>
      </div>

      {/* 预设选择器 */}
      <div className="flex flex-wrap gap-2">
        {presets.map((preset) => (
          <button
            key={preset.name}
            onClick={() => applyPreset(preset)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer",
              "border border-app-border",
              "hover:border-primary/50 hover:bg-primary/5",
              "text-text-secondary hover:text-text-primary"
            )}
            title={preset.description}
          >
            {preset.name}
          </button>
        ))}
        <button
          onClick={resetCurve}
          className="px-3 py-1.5 rounded-lg text-xs font-medium text-red-400 border border-red-400/30 hover:bg-red-400/10 transition-colors cursor-pointer"
        >
          重置
        </button>
      </div>

      {/* 插值方式选择 */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-text-muted">插值:</span>
        {(['linear', 'bezier', 'step'] as const).map((mode) => (
          <button
            key={mode}
            onClick={() => setInterpolation(mode)}
            className={cn(
              "px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer",
              curve.interpolation === mode
                ? "bg-primary/20 text-primary border border-primary/30"
                : "text-text-secondary hover:bg-app-card border border-transparent"
            )}
          >
            {{ linear: '线性', bezier: '平滑', step: '阶梯' }[mode]}
          </button>
        ))}
      </div>

      {/* 速度曲线图表 */}
      <div className="flex-1 min-h-[250px] bg-app-bg rounded-xl p-4 border border-app-border">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={curve.points.map(p => ({ ...p, name: `${p.time}%` }))}
            onClick={handleChartClick}
            margin={{ top: 10, right: 30, left: 0, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#3A3A4A" />
            
            {/* X轴 - 时间(%) */}
            <XAxis 
              dataKey="time" 
              domain={[0, 100]}
              tick={{ fill: '#94A3B8', fontSize: 11 }}
              unit="%"
            />
            
            {/* Y轴 - 速度倍率 */}
            <YAxis 
              domain={[0.25, 2.5]}
              tick={{ fill: '#94A3B8', fontSize: 11 }}
              tickFormatter={(v) => `${v}x`}
            />

            {/* 自定义Tooltip */}
            <Tooltip
              contentStyle={{
                backgroundColor: '#252536',
                border: '1px solid #3A3A4A',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#E2E8F0' }}
              formatter={(value: any) => [`${Number(value).toFixed(2)}x`, '速度']}
              labelFormatter={(label) => `时间: ${label}%`}
            />

            {/* 速度曲线 */}
            <Line
              type="monotone"
              dataKey="speed"
              stroke="#3B82F6"
              strokeWidth={2.5}
              dot={{ 
                r: 5, 
                fill: '#121212', 
                stroke: selectedPointId ? '#F97316' : '#3B82F6',
                strokeWidth: 2,
                cursor: 'pointer',
              }}
              activeDot={{ r: 7, fill: '#F97316', stroke: '#fff', strokeWidth: 2 }}
              animationDuration={300}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 选中点编辑面板 */}
      {selectedPointId && (() => {
        const point = curve.points.find(p => p.id === selectedPointId);
        if (!point) return null;
        
        return (
          <div className="flex items-center gap-3 p-3 rounded-xl bg-app-card border border-app-border animate-fade-in">
            <div className="flex-1 flex items-center gap-3">
              <span className="text-xs text-text-muted">
                位置: {point.time.toFixed(0)}%
              </span>
              
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-muted">速度:</span>
                <input
                  type="range"
                  min="0.25"
                  max="2.5"
                  step="0.05"
                  value={point.speed}
                  onChange={(e) => handleUpdateSelectedSpeed(parseFloat(e.target.value))}
                  className="w-24 accent-primary"
                />
                <span className="text-sm font-mono text-text-primary w-10">
                  {point.speed.toFixed(2)}x
                </span>
              </div>
            </div>

            <button
              onClick={handleDeleteSelected}
              disabled={curve.points.length <= 2}
              className={cn(
                "px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer",
                curve.points.length <= 2
                  ? "text-text-muted opacity-50 cursor-not-allowed"
                  : "text-red-400 hover:bg-red-400/10"
              )}
            >
              删除
            </button>

            <button
              onClick={() => setSelectedPointId(null)}
              className="text-xs text-text-muted hover:text-text-secondary cursor-pointer"
            >
              取消
            </button>
          </div>
        );
      })()}

      {/* 说明文字 */}
      <p className="text-xs text-text-muted leading-relaxed">
        点击图表上的点可以编辑或删除。速度曲线仅在图片/PDF格式下生效，
        GTP文件使用内置播放器的速度控制。
      </p>
    </div>
  );
}
