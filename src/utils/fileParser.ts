/**
 * ============================================================
 * 文件名: fileParser.ts
 * 功能描述: 文件处理公共工具函数
 *          - 文件格式检测
 *          - 文件解析为ScoreData（图片/PDF/GTP通用）
 *          - 文件夹结构解析为文件树
 *          - 从FileList/FileSystemHandle构建目录树
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: types/index.ts
 * ============================================================
 */

import type {
  SupportedFormat,
  ScoreFile,
  ScoreData,
  ImageScoreData,
  PdfScoreData,
  GtpScoreData,
  FileTreeNode,
  FolderRoot,
} from '@/types';

// ====== 支持的扩展名常量 ======
const IMAGE_EXTS = new Set(['png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif']);
const PDF_EXTS = new Set(['pdf']);
const GTP_EXTS = new Set(['gtp', 'gp3', 'gp4', 'gp5', 'gp6', 'gp7', 'ptb', 'tef']);

/** 所有支持的谱面文件扩展名 */
export const SUPPORTED_EXTENSIONS = new Set([
  ...IMAGE_EXTS, ...PDF_EXTS, ...GTP_EXTS,
]);

/**
 * 根据文件扩展名判断格式类型
 * @param filename - 文件名
 * @returns 格式类型
 */
export function detectFormat(filename: string): SupportedFormat {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  
  if (IMAGE_EXTS.has(ext)) return 'image';
  if (PDF_EXTS.has(ext)) return 'pdf';
  if (GTP_EXTS.has(ext)) return 'gtp';
  
  return 'unknown';
}

/**
 * 判断文件是否为支持的谱面格式
 * @param filename - 文件名
 * @returns 是否支持
 */
export function isSupportedFile(filename: string): boolean {
  return detectFormat(filename) !== 'unknown';
}

/**
 * 将单个File对象解析为谱面数据
 * 统一处理图片、PDF、GTP三种格式的解析逻辑
 * 
 * @param file - 原始File对象
 * @returns Promise<{ file: ScoreFile, data: ScoreData }>
 * 
 * @example
 * const { file, data } = await parseFileToScore(fileInput.files[0]);
 */
export async function parseFileToScore(
  file: File
): Promise<{ file: ScoreFile; data: ScoreData }> {
  const format = detectFormat(file.name);
  
  // 构建文件元信息
  const scoreFile: ScoreFile = {
    name: file.name,
    url: URL.createObjectURL(file),
    format,
    size: file.size,
  };

  let scoreData: ScoreData;

  switch (format) {
    case 'image': {
      // 图片：加载获取原始尺寸
      const img = await loadImage(scoreFile.url);
      scoreData = {
        type: 'image',
        src: scoreFile.url,
        naturalWidth: img.naturalWidth,
        naturalHeight: img.naturalHeight,
      } as ScoreData;
      break;
    }
    case 'pdf': {
      scoreData = {
        type: 'pdf',
        url: scoreFile.url,
        totalPages: 1,
        currentPage: 1,
      } as ScoreData;
      break;
    }
    case 'gtp': {
      // GTP：读取为ArrayBuffer供AlphaTab使用
      const buffer = await file.arrayBuffer();
      scoreData = {
        type: 'gtp',
        data: buffer,
      } as ScoreData;
      break;
    }
    default:
      throw new Error(`不支持的文件格式: ${file.name}`);
  }

  return { file: scoreFile, data: scoreData };
}

/**
 * 加载图片并返回HTMLImageElement
 * @param src - 图片URL或路径
 * @returns 加载完成的Image对象
 */
function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('图片加载失败'));
    img.src = src;
  });
}

/**
 * 从扁平的文件列表构建树形结构
 * 根据文件路径中的 / 或 \ 分隔符构建层级关系
 * 
 * @param files - File数组（通常来自 input[type=file] webkitdirectory）
 * @param rootName - 根文件夹名称
 * @returns FolderRoot 文件夹根信息
 * 
 * @example
 * // 从 <input type="file" webkitdirectory> 获取的files构建树
 * const tree = buildFileTree(input.files, 'MyTabs');
 */
export function buildFileTree(files: FileList | File[], rootName: string = 'Root'): FolderRoot {
  /** 内部节点映射表: 路径 -> 节点 */
  const nodeMap = new Map<string, FileTreeNode>();
  
  // 根节点
  const rootNode: FileTreeNode = {
    id: '__root__',
    name: rootName,
    type: 'folder',
    path: '',
    depth: 0,
    children: [],
    isExpanded: true,
  };
  nodeMap.set('', rootNode);

  // 遍历所有文件，构建路径上的所有节点
  Array.from(files).forEach((file) => {
    // 获取文件的相对路径（webkitdirectory模式下 file.name 包含完整相对路径）
    const relativePath = file.webkitRelativePath || file.name;
    
    // 分割路径为各级段
    const parts = relativePath.split(/[/\\]/).filter(Boolean);
    
    if (parts.length === 0) return;
    
    let currentPath = '';
    
    // 构建从根到文件的每一级节点
    parts.forEach((part, index) => {
      const parentPath = currentPath;
      currentPath = currentPath ? `${currentPath}/${part}` : part;
      
      const isFile = index === parts.length - 1;
      const format = isFile ? detectFormat(part) : undefined;
      
      // 跳过不支持的文件类型（但保留文件夹）
      if (isFile && format === 'unknown') return;

      // 如果该路径节点不存在，则创建
      if (!nodeMap.has(currentPath)) {
        const parentNode = nodeMap.get(parentPath)!;
        const node: FileTreeNode = {
          id: currentPath,
          name: part,
          type: isFile ? 'file' : 'folder',
          path: currentPath,
          depth: index + 1,
          ...(isFile ? { format, fileHandle: file } : { children: [], isExpanded: false }),
        };
        
        nodeMap.set(currentPath, node);
        
        // 添加到父节点的children中
        if (parentNode.children) {
          parentNode.children.push(node);
          
          // 按名称排序：文件夹在前，然后按字母排序
          parentNode.children.sort((a, b) => {
            if (a.type !== b.type) return a.type === 'folder' ? -1 : 1;
            return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
          });
        }
      }
    });
  });

  return {
    name: rootName,
    root: rootNode,
  };
}

/**
 * 递归过滤文件树，只保留支持的谱面文件
 * 同时移除空文件夹
 * 
 * @param node - 当前节点
 * @returns 过滤后的节点（如果无有效子节点则返回null）
 */
export function filterSupportedFiles(node: FileTreeNode): FileTreeNode | null {
  if (node.type === 'file') {
    // 文件节点：仅保留支持的格式
    return node.format && node.format !== 'unknown' ? node : null;
  }

  // 文件夹节点：递归过滤子节点
  if (node.children) {
    const filteredChildren = node.children
      .map(filterSupportedFiles)
      .filter((child): child is FileTreeNode => child !== null);

    if (filteredChildren.length === 0) return null; // 空文件夹

    return {
      ...node,
      children: filteredChildren,
    };
  }

  return null;
}
