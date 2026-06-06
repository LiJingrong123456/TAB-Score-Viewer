/**
 * ============================================================
 * 文件名: playerStore.ts
 * 功能描述: 全局播放状态管理 (Zustand Store)
 *          管理播放器的所有状态：播放/暂停、进度、速度、循环等
 *          使用Zustand实现轻量级全局状态管理
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: zustand, types/index.ts
 * ============================================================
 */

import { create } from 'zustand';
import type {
  PlayerState,
  PlayState,
  LoopMode,
  LoopRegion,
  SpeedCurveConfig,
  SpeedControlPoint,
  Annotation,
  ScoreFile,
  ScoreData,
  ZoomSettings,
  FileTreeNode,
  FolderRoot,
} from '@/types';

// ====== Store状态接口 ======

/** 应用全局状态接口 */
interface AppState {
  // ---- 文件状态 ----
  /** 当前加载的谱面文件 */
  currentFile: ScoreFile | null;
  /** 当前谱面数据 */
  scoreData: ScoreData | null;

  // ---- 播放状态 ----
  /** 播放器状态 */
  player: PlayerState;
  
  // ---- 速度曲线 ----
  /** 速度曲线配置 */
  speedCurve: SpeedCurveConfig;

  // ---- 标注系统 ----
  /** 标注列表 */
  annotations: Annotation[];

  // ---- 视图状态 ----
  /** 缩放设置 */
  zoom: ZoomSettings;
  /** 当前视图模式 */
  viewMode: 'viewer' | 'speed-curve' | 'annotation';
  /** 是否显示侧边栏 */
  showSidebar: boolean;

  // ---- 文件目录树 ----
  /** 当前打开的文件夹根信息 */
  folderRoot: FolderRoot | null;
  /** 文件树展开状态映射 (节点ID -> 是否展开) */
  expandedNodes: Set<string>;
  /** 是否显示左侧文件面板 */
  showFilePanel: boolean;

  // ====== Actions ======
  
  // --- 文件操作 ---
  /** 设置当前文件和数据 */
  setScoreFile: (file: ScoreFile, data: ScoreData) => void;
  /** 清除当前文件 */
  clearScoreFile: () => void;

  // --- 播放控制 ---
  /** 设置播放状态 */
  setPlayState: (state: PlayState) => void;
  /** 更新当前时间 */
  setCurrentTime: (time: number) => void;
  /** 设置总时长 */
  setDuration: (duration: number) => void;
  /** 设置播放速度 */
  setPlaybackRate: (rate: number) => void;
  /** 设置音量 */
  setVolume: (volume: number) => void;
  /** 切换播放/暂停 */
  togglePlayPause: () => void;
  
  // --- 循环控制 ---
  /** 设置循环模式 */
  setLoopMode: (mode: LoopMode) => void;
  /** 设置循环区域 */
  setLoopRegion: (region: LoopRegion) => void;

  // --- 速度曲线 ---
  /** 设置速度曲线 */
  setSpeedCurve: (config: Partial<SpeedCurveConfig>) => void;
  /** 添加速度控制点 */
  addSpeedPoint: (point: Omit<SpeedControlPoint, 'id'>) => void;
  /** 删除速度控制点 */
  removeSpeedPoint: (id: string) => void;
  /** 更新速度控制点 */
  updateSpeedPoint: (id: string, updates: Partial<SpeedControlPoint>) => void;

  // --- 标注操作 ---
  /** 添加标注 */
  addAnnotation: (annotation: Omit<Annotation, 'id' | 'createdAt' | 'updatedAt'>) => void;
  /** 更新标注 */
  updateAnnotation: (id: string, updates: Partial<Annotation>) => void;
  /** 删除标注 */
  removeAnnotation: (id: string) => void;
  /** 清除所有标注 */
  clearAnnotations: () => void;

  // --- 视图操作 ---
  /** 设置缩放比例 */
  setZoomScale: (scale: number) => void;
  /** 设置视图模式 */
  setViewMode: (mode: 'viewer' | 'speed-curve' | 'annotation') => void;
  /** 切换侧边栏 */
  toggleSidebar: () => void;

  // --- 文件目录树操作 ---
  /** 设置文件夹根信息（打开文件夹后调用） */
  setFolderRoot: (root: FolderRoot) => void;
  /** 清除文件夹 */
  clearFolderRoot: () => void;
  /** 切换节点展开/折叠 */
  toggleNodeExpand: (nodeId: string) => void;
  /** 展开所有节点 */
  expandAllNodes: () => void;
  /** 折叠所有节点 */
  collapseAllNodes: () => void;
  /** 切换文件面板显示 */
  toggleFilePanel: () => void;
}

// ====== 默认值 ======

/** 默认播放器状态 */
const defaultPlayerState: PlayerState = {
  playState: 'idle',
  currentTime: 0,
  duration: 0,
  playbackRate: 1.0,
  volume: 0.8,
  loopMode: 'none',
  loopRegion: { start: 0, end: 100 },
};

/** 默认速度曲线配置 */
const defaultSpeedCurve: SpeedCurveConfig = {
  points: [
    { time: 0, speed: 1.0, id: 'default-start' },
    { time: 100, speed: 1.0, id: 'default-end' },
  ],
  interpolation: 'linear',
  enabled: false,
};

/** 默认缩放设置 */
const defaultZoom: ZoomSettings = {
  scale: 1.0,
  minZoom: 0.1,
  maxZoom: 5.0,
};

// ====== Store创建 ======

export const useAppStore = create<AppState>((set) => ({
  // 初始状态
  currentFile: null,
  scoreData: null,
  player: { ...defaultPlayerState },
  speedCurve: { ...defaultSpeedCurve },
  annotations: [],
  zoom: { ...defaultZoom },
  viewMode: 'viewer',
  showSidebar: true,
  folderRoot: null,
  expandedNodes: new Set<string>(),
  showFilePanel: true,

  // --- 文件操作 ---
  setScoreFile: (file, data) => set({
    currentFile: file,
    scoreData: data,
    player: { ...defaultPlayerState, playState: 'idle' },
    annotations: [],
  }),

  clearScoreFile: () => set({
    currentFile: null,
    scoreData: null,
    player: { ...defaultPlayerState },
    annotations: [],
  }),

  // --- 播放控制 ---
  setPlayState: (playState) => set((state) => ({
    player: { ...state.player, playState },
  })),

  setCurrentTime: (currentTime) => set((state) => ({
    player: { ...state.player, currentTime },
  })),

  setDuration: (duration) => set((state) => ({
    player: { ...state.player, duration },
  })),

  setPlaybackRate: (playbackRate) => set((state) => ({
    player: { ...state.player, playbackRate: Math.max(0.25, Math.min(4.0, playbackRate)) },
  })),

  setVolume: (volume) => set((state) => ({
    player: { ...state.player, volume: Math.max(0, Math.min(1, volume)) },
  })),

  togglePlayPause: () => set((state) => ({
    player: {
      ...state.player,
      playState: state.player.playState === 'playing' ? 'paused' : 'playing',
    },
  })),

  // --- 循环控制 ---
  setLoopMode: (loopMode) => set((state) => ({
    player: { ...state.player, loopMode },
  })),

  setLoopRegion: (loopRegion) => set((state) => ({
    player: { ...state.player, loopRegion },
  })),

  // --- 速度曲线 ---
  setSpeedCurve: (config) => set((state) => ({
    speedCurve: { ...state.speedCurve, ...config },
  })),

  addSpeedPoint: (point) => set((state) => ({
    speedCurve: {
      ...state.speedCurve,
      points: [
        ...state.speedCurve.points,
        { ...point, id: `point-${Date.now()}-${Math.random().toString(36).slice(2, 9)}` },
      ].sort((a, b) => a.time - b.time),
    },
  })),

  removeSpeedPoint: (id) => set((state) => ({
    speedCurve: {
      ...state.speedCurve,
      points: state.speedCurve.points.filter((p) => p.id !== id),
    },
  })),

  updateSpeedPoint: (id, updates) => set((state) => ({
    speedCurve: {
      ...state.speedCurve,
      points: state.speedCurve.points.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ).sort((a, b) => a.time - b.time),
    },
  })),

  // --- 标注操作 ---
  addAnnotation: (annotation) => set((state) => ({
    annotations: [
      ...state.annotations,
      {
        ...annotation,
        id: `anno-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      },
    ],
  })),

  updateAnnotation: (id, updates) => set((state) => ({
    annotations: state.annotations.map((a) =>
      a.id === id ? { ...a, ...updates, updatedAt: Date.now() } : a
    ),
  })),

  removeAnnotation: (id) => set((state) => ({
    annotations: state.annotations.filter((a) => a.id !== id),
  })),

  clearAnnotations: () => set({ annotations: [] }),

  // --- 视图操作 ---
  setZoomScale: (scale) => set((state) => ({
    zoom: {
      ...state.zoom,
      scale: Math.max(state.zoom.minZoom, Math.min(state.zoom.maxZoom, scale)),
    },
  })),

  setViewMode: (viewMode) => set({ viewMode }),

  toggleSidebar: () => set((state) => ({ showSidebar: !state.showSidebar })),

  // --- 文件目录树操作 ---
  setFolderRoot: (folderRoot) => set({
    folderRoot,
    // 默认展开第一层
    expandedNodes: new Set([folderRoot.root.id]),
  }),

  clearFolderRoot: () => set({
    folderRoot: null,
    expandedNodes: new Set(),
  }),

  toggleNodeExpand: (nodeId) => set((state) => {
    const newSet = new Set(state.expandedNodes);
    if (newSet.has(nodeId)) {
      newSet.delete(nodeId);
    } else {
      newSet.add(nodeId);
    }
    return { expandedNodes: newSet };
  }),

  expandAllNodes: () => set((state) => {
    if (!state.folderRoot) return {};
    
    /** 递归收集所有文件夹节点ID */
    const collectFolderIds = (node: FileTreeNode): string[] => {
      const ids: string[] = [];
      if (node.type === 'folder') {
        ids.push(node.id);
        if (node.children) {
          node.children.forEach((child) => ids.push(...collectFolderIds(child)));
        }
      }
      return ids;
    };

    return { expandedNodes: new Set(collectFolderIds(state.folderRoot.root)) };
  }),

  collapseAllNodes: () => set((state) => {
    if (!state.folderRoot) return {};
    // 只保留根节点展开
    return { expandedNodes: new Set([state.folderRoot.root.id]) };
  }),

  toggleFilePanel: () => set((state) => ({ showFilePanel: !state.showFilePanel })),
}));
