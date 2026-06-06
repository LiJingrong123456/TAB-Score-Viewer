/**
 * ============================================================
 * 文件名: index.ts (类型定义)
 * 功能描述: TAB Score Viewer 全局类型定义文件
 *          定义了应用中使用的所有TypeScript接口和类型
 *          包括：谱面类型、标注类型、播放状态、速度曲线等
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * ============================================================
 */

// ====== 支持的文件格式枚举 ======
/** 支持的谱面文件格式 */
export type SupportedFormat = 'image' | 'pdf' | 'gtp' | 'unknown';

/** 图片格式扩展名 */
export const IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif'] as const;
/** PDF格式扩展名 */
export const PDF_EXTENSIONS = ['pdf'] as const;
/** GTP(Guitar Pro)格式扩展名 */
export const GTP_EXTENSIONS = ['gtp', 'gp3', 'gp4', 'gp5', 'gp6', 'gp7', 'ptb', 'tef'] as const;

// ====== 谱面数据类型 ======

/** 谱面文件信息 */
export interface ScoreFile {
  /** 文件名（不含路径） */
  name: string;
  /** 文件完整路径/URL */
  url: string;
  /** 文件格式类型 */
  format: SupportedFormat;
  /** 文件大小(字节) */
  size?: number;
}

/** 图片谱面数据 */
export interface ImageScoreData {
  type: 'image';
  /** 图片源(URL或base64) */
  src: string;
  /** 原始宽度 */
  naturalWidth: number;
  /** 原始高度 */
  naturalHeight: number;
}

/** PDF谱面数据 */
export interface PdfScoreData {
  type: 'pdf';
  /** PDF文件URL */
  url: string;
  /** 总页数 */
  totalPages: number;
  /** 当前页码(从1开始) */
  currentPage: number;
}

/** GTP谱面数据 */
export interface GtpScoreData {
  type: 'gtp';
  /** GTP文件内容(ArrayBuffer) */
  data: ArrayBuffer;
  /** 曲目标题 */
  title?: string;
  /** 艺术家 */
  artist?: string;
  /** BPM */
  bpm?: number;
  /** 时间长度(毫秒) */
  duration?: number;
}

/** 联合谱面数据类型 */
export type ScoreData = ImageScoreData | PdfScoreData | GtpScoreData;

// ====== 标注系统类型 ======

/** 单个文本标注 */
export interface Annotation {
  /** 唯一ID */
  id: string;
  /** 标注文本内容 */
  text: string;
  /** 相对于谱面的X位置(百分比 0-100) */
  x: number;
  /** 相对于谱面的Y位置(百分比 0-100) */
  y: number;
  /** 关联的时间点(毫秒)，用于播放时高亮 */
  timestamp?: number;
  /** 标注颜色 */
  color?: string;
  /** 创建时间 */
  createdAt: number;
  /** 最后更新时间 */
  updatedAt: number;
}

/** 标注编辑状态 */
export interface AnnotationEditState {
  /** 是否处于编辑模式 */
  isEditing: boolean;
  /** 当前编辑的标注ID */
  editingId: string | null;
  /** 新建标注的临时位置 */
  pendingPosition: { x: number; y: number } | null;
}

// ====== 播放控制类型 ======

/** 播放状态 */
export type PlayState = 'idle' | 'playing' | 'paused';

/** 循环模式 */
export type LoopMode = 'none' | 'all' | 'region';

/** 区域循环范围 */
export interface LoopRegion {
  /** 起始位置(毫秒或百分比) */
  start: number;
  /** 结束位置(毫秒或百分比) */
  end: number;
}

/** 播放器状态 */
export interface PlayerState {
  /** 当前播放状态 */
  playState: PlayState;
  /** 当前播放时间(毫秒) */
  currentTime: number;
  /** 总时长(毫秒) */
  duration: number;
  /** 播放速度倍率 (0.25 - 4.0) */
  playbackRate: number;
  /** 音量 (0 - 1) */
  volume: number;
  /** 循环模式 */
  loopMode: LoopMode;
  /** 区域循环范围(仅loopMode='region'时有效) */
  loopRegion: LoopRegion;
}

// ====== 速度曲线类型 ======

/** 速度曲线控制点 */
export interface SpeedControlPoint {
  /** 时间位置(百分比 0-100) */
  time: number;
  /** 速度倍率 (0.25 - 4.0) */
  speed: number;
  /** 控制点唯一ID */
  id: string;
}

/** 速度曲线配置 */
export interface SpeedCurveConfig {
  /** 控制点数组 */
  points: SpeedControlPoint[];
  /** 插值方式: linear | bezier | step */
  interpolation: 'linear' | 'bezier' | 'step';
  /** 是否启用速度曲线 */
  enabled: boolean;
}

// ====== UI状态类型 ======

/** 应用视图模式 */
export type ViewMode = 'viewer' | 'speed-curve' | 'annotation';

/** 缩放设置 */
export interface ZoomSettings {
  /** 当前缩放比例 (0.1 - 5.0) */
  scale: number;
  /** 最小缩放 */
  minZoom: number;
  /** 最大缩放 */
  maxZoom: number;
}

// ====== 文件目录树类型 ======

/** 文件树节点类型 */
export type FileTreeNodeType = 'folder' | 'file';

/** 文件树节点 - 表示目录或文件 */
export interface FileTreeNode {
  /** 节点唯一ID (路径作为ID) */
  id: string;
  /** 名称（文件夹名或文件名） */
  name: string;
  /** 节点类型：文件夹或文件 */
  type: FileTreeNodeType;
  /** 完整相对路径 */
  path: string;
  /** 文件格式(仅文件节点) */
  format?: SupportedFormat;
  /** 子节点列表(仅文件夹节点) */
  children?: FileTreeNode[];
  /** 是否展开(仅文件夹节点) */
  isExpanded?: boolean;
  /** 层级深度(0为根级) */
  depth: number;
  /** File对象引用(仅文件节点，用于读取文件内容) */
  fileHandle?: File;
}

/** 文件夹根信息 */
export interface FolderRoot {
  /** 文件夹名称 */
  name: string;
  /** 文件树根节点 */
  root: FileTreeNode;
}
