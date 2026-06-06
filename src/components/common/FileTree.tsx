/**
 * ============================================================
 * 文件名: FileTree.tsx
 * 功能描述: 文件目录树组件 - 左侧可展开的文件浏览器
 *          显示选中文件夹中的所有谱面文件
 *          支持：展开/折叠文件夹、点击打开文件、高亮当前文件
 *          支持的文件格式会显示对应图标，其他文件自动隐藏
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: React, playerStore, fileParser工具, Lucide图标
 * ============================================================
 */

import { useCallback, useMemo, useState, useRef } from 'react';
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  FileImage,
  FileText,
  Music,
  Search,
  FolderPlus,
  LayoutGrid,
  List,
} from 'lucide-react';
import { useAppStore } from '@/stores/playerStore';
import { parseFileToScore, detectFormat } from '@/utils/fileParser';
import type { FileTreeNode, SupportedFormat } from '@/types';
import { cn } from '@/utils/cn';

/**
 * 根据文件格式获取对应的图标和颜色
 * @param format - 文件格式类型
 * @returns 图标组件和颜色类名
 */
function getFileIcon(format: SupportedFormat | undefined) {
  switch (format) {
    case 'image':
      return { icon: FileImage, color: 'text-green-400' };
    case 'pdf':
      return { icon: FileText, color: 'text-red-400' };
    case 'gtp':
      return { icon: Music, color: 'text-primary' };
    default:
      return { icon: FileText, color: 'text-text-muted' };
  }
}

interface TreeNodeProps {
  /** 当前节点数据 */
  node: FileTreeNode;
}

/**
 * 单个树节点组件
 * 递归渲染文件或文件夹节点
 */
function TreeNode({ node }: TreeNodeProps) {
  const {
    expandedNodes,
    toggleNodeExpand,
    currentFile,
    setScoreFile,
    folderRoot,
  } = useAppStore();

  const isExpanded = expandedNodes.has(node.id);
  const isSelected = currentFile?.url && (
    // 通过path匹配判断是否是当前选中的文件
    node.type === 'file' && node.fileHandle && 
    currentFile.name === node.name
  );
  const isFolder = node.type === 'folder';
  const hasChildren = isFolder && (node.children?.length ?? 0) > 0;

  /**
   * 点击节点处理
   * - 文件夹：切换展开/折叠
   * - 文件：打开文件进行查看
   */
  const handleClick = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (isFolder) {
      toggleNodeExpand(node.id);
      return;
    }

    // 文件：解析并打开
    if (!node.fileHandle) return;

    try {
      const { file, data } = await parseFileToScore(node.fileHandle);
      setScoreFile(file, data);
    } catch (error) {
      console.error('文件打开失败:', error);
    }
  }, [isFolder, node.id, node.fileHandle, toggleNodeExpand, setScoreFile]);

  /**
   * 双击文件夹：切换展开状态（备用交互方式）
   */
  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (isFolder) {
      toggleNodeExpand(node.id);
    }
  }, [isFolder, node.id, toggleNodeExpand]);

  // 获取图标信息
  const iconInfo = isFolder 
    ? { 
        icon: isExpanded ? FolderOpen : Folder, 
        color: isExpanded ? 'text-accent' : 'text-text-muted' 
      }
    : getFileIcon(node.format);

  const IconComponent = iconInfo.icon;

  // 缩进计算：每级缩进16px
  const paddingLeft = Math.max(0, (node.depth - 1) * 16 + 8);

  return (
    <div>
      {/* 节点行 */}
      <div
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        className={cn(
          "group flex items-center gap-1.5 py-1.5 pr-2 cursor-pointer",
          "transition-colors duration-150 rounded-md mx-1",
          // 选中状态
          isSelected
            ? "bg-primary/15 text-primary"
            : "hover:bg-app-card text-text-secondary hover:text-text-primary",
          // 文件夹样式
          isFolder && "font-medium"
        )}
        style={{ paddingLeft }}
        role="treeitem"
        aria-expanded={isFolder ? isExpanded : undefined}
        aria-selected={isSelected || false}
      >
        {/* 展开/折叠箭头（仅文件夹且有子节点时显示） */}
        {isFolder && (
          <span className="shrink-0 w-4 h-4 flex items-center justify-center">
            {hasChildren ? (
              isExpanded ? (
                <ChevronDown className="w-3.5 h-3.5 text-text-muted" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
              )
            ) : (
              /* 无子节点的空占位 */
              <span className="w-3.5" />
            )}
          </span>
        )}

        {/* 文件的缩进占位 */}
        {!isFolder && <span className="shrink-0 w-4" />}

        {/* 图标 */}
        <IconComponent className={cn("w-4 h-4 shrink-0", iconInfo.color)} />

        {/* 名称 */}
        <span className={cn(
          "truncate text-sm",
          isSelected && "font-medium"
        )}>
          {node.name}
        </span>

        {/* 文件大小提示(仅文件且非选中时显示) */}
        {!isFolder && !isSelected && node.fileHandle && (
          <span className="ml-auto text-xs text-text-muted shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
            {formatFileSize(node.fileHandle.size)}
          </span>
        )}
      </div>

      {/* 子节点（递归渲染） */}
      {isFolder && isExpanded && hasChildren && (
        <div role="group">
          {node.children!.map((child) => (
            <TreeNode key={child.id} node={child} />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * 格式化文件大小显示
 * @param bytes - 字节数
 * @returns 格式化字符串
 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

/**
 * 文件目录树组件
 * 左侧面板中的可展开文件浏览器
 */
export function FileTree() {
  const {
    folderRoot,
    expandedNodes,
    setFolderRoot,
    clearFolderRoot,
    expandAllNodes,
    collapseAllNodes,
    showFilePanel,
    toggleFilePanel,
  } = useAppStore();

  // 搜索关键词状态（本地state）
  const [searchKeyword, setSearchKeyword] = useState('');

  /** 隐藏的文件夹选择input引用 */
  const folderInputRef = useRef<HTMLInputElement>(null);

  /**
   * 处理文件夹选择
   * 使用webkitdirectory属性选择整个文件夹
   */
  const handleFolderSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    // 使用webkitRelativePath提取文件夹名
    const firstPath = files[0].webkitRelativePath || '';
    const folderName = firstPath.split('/')[0] || '未命名文件夹';

    // 构建文件树
    const { buildFileTree } = await import('@/utils/fileParser');
    const tree = buildFileTree(files, folderName);

    setFolderRoot(tree);
    
    // 重置input以便重复选择同一文件夹
    if (folderInputRef.current) folderInputRef.current.value = '';
  }, [setFolderRoot]);

  /**
   * 触发文件夹选择对话框
   */
  const handleOpenFolder = useCallback(() => {
    folderInputRef.current?.click();
  }, []);

  /**
   * 过滤后的树节点（搜索功能）
   * TODO: 实现搜索过滤逻辑
   */
  const filteredTree = useMemo(() => {
    if (!folderRoot) return null;
    if (!searchKeyword.trim()) return folderRoot.root;
    
    // 搜索过滤实现...
    return folderRoot.root;
  }, [folderRoot, searchKeyword]);

  // 文件统计
  const stats = useMemo(() => {
    if (!folderRoot) return { folders: 0, files: 0 };

    let folders = 0;
    let files = 0;

    const count = (node: FileTreeNode) => {
      if (node.type === 'folder') {
        folders++;
        node.children?.forEach(count);
      } else {
        files++;
      }
    };

    count(folderRoot.root);
    return { folders, files };
  }, [folderRoot]);

  return (
    <div className="flex flex-col h-full bg-app-surface">
      {/* ====== 工具栏区域 ====== */}
      <div className="p-3 border-b border-app-border space-y-2">
        {/* 选择文件夹按钮 */}
        <button
          onClick={handleOpenFolder}
          className={cn(
            "w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg",
            "text-sm font-medium transition-all duration-200 cursor-pointer",
            "bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20"
          )}
        >
          <FolderPlus className="w-4 h-4" />
          选择文件夹
        </button>

        {/* 隐藏的文件夹input */}
        <input
          ref={folderInputRef}
          type="file"
          // webkitdirectory属性允许选择整个文件夹
          webkitdirectory=""
          directory=""
          multiple
          onChange={handleFolderSelect}
          className="hidden"
          aria-hidden="true"
        />

        {/* 搜索框 */}
        {folderRoot && (
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
            <input
              type="text"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              placeholder="搜索文件..."
              className={cn(
                "w-full pl-8 pr-3 py-1.5 rounded-lg text-xs",
                "bg-app-bg border border-app-border",
                "text-text-primary placeholder:text-text-muted",
                "focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20",
                "transition-colors"
              )}
            />
          </div>
        )}

        {/* 操作按钮行 */}
        {folderRoot && (
          <div className="flex items-center gap-1">
            <button
              onClick={expandAllNodes}
              className="flex-1 px-2 py-1 rounded text-xs text-text-secondary hover:text-text-primary hover:bg-app-card transition-colors cursor-pointer"
              title="展开全部"
            >
              全部展开
            </button>
            <button
              onClick={collapseAllNodes}
              className="flex-1 px-2 py-1 rounded text-xs text-text-secondary hover:text-text-primary hover:bg-app-card transition-colors cursor-pointer"
              title="折叠全部"
            >
              全部折叠
            </button>
            <button
              onClick={clearFolderRoot}
              className="px-2 py-1 rounded text-xs text-red-400 hover:bg-red-400/10 transition-colors cursor-pointer"
              title="关闭文件夹"
            >
              关闭
            </button>
          </div>
        )}
      </div>

      {/* ====== 文件夹名称 + 统计 ====== */}
      {folderRoot && (
        <div className="px-3 py-2 border-b border-app-border flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <FolderOpen className="w-4 h-4 text-accent shrink-0" />
            <span className="text-sm font-medium text-text-primary truncate">
              {folderRoot.name}
            </span>
          </div>
          <span className="text-xs text-text-muted shrink-0 ml-2">
            {stats.files} 个文件
          </span>
        </div>
      )}

      {/* ====== 文件树内容区域 ====== */}
      <div className="flex-1 overflow-y-auto scrollbar-custom py-1">
        {filteredTree ? (
          /* 渲染文件树 */
          <div role="tree" aria-label="文件目录树">
            {filteredTree.children?.map((child) => (
              <TreeNode key={child.id} node={child} />
            ))}
            
            {/* 空文件夹提示 */}
            {(!filteredTree.children || filteredTree.children.length === 0) && (
              <div className="flex flex-col items-center justify-center py-8 text-text-muted">
                <Folder className="w-10 h-10 mb-2 opacity-30" />
                <p className="text-xs">没有找到支持的谱面文件</p>
                <p className="text-xs opacity-60 mt-1">支持: PNG, JPG, WEBP, PDF, GP</p>
              </div>
            )}
          </div>
        ) : (
          /* 未选择文件夹时的空状态 */
          <div className="flex flex-col items-center justify-center h-full px-6 text-center">
            <div className="w-16 h-16 rounded-2xl bg-app-card flex items-center justify-center mb-4">
              <FolderPlus className="w-7 h-7 text-text-muted" />
            </div>
            <h3 className="text-sm font-semibold text-text-primary mb-1">
              选择文件夹
            </h3>
            <p className="text-xs text-text-muted leading-relaxed max-w-[180px]">
              选择包含吉他谱的文件夹，浏览并快速打开文件
            </p>
            
            {/* 支持格式提示 */}
            <div className="flex flex-wrap gap-1 mt-4 justify-center">
              {['PNG', 'JPG', 'WEBP', 'PDF', 'GP'].map((fmt) => (
                <span
                  key={fmt}
                  className="px-2 py-0.5 text-[10px] font-medium rounded bg-app-card text-text-muted border border-app-border"
                >
                  {fmt}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
