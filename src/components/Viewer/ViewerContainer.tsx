/**
 * ============================================================
 * 文件名: ViewerContainer.tsx
 * 功能描述: 谱面查看器容器组件 - 自动选择合适的查看器
 *          根据文件格式自动分发到 ImageViewer / PdfViewer / GtpViewer
 *          同时作为标注层的父容器
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: React, 子查看器组件, AnnotationLayer, playerStore
 * ============================================================
 */

import { useAppStore } from '@/stores/playerStore';
import { ImageViewer } from './ImageViewer';
import { PdfViewer } from './PdfViewer';
import { GtpViewer } from './GtpViewer';
import { AnnotationLayer } from '../Annotation/AnnotationLayer';

/**
 * 谱面查看器容器组件
 * 根据当前加载的谱面类型自动渲染对应的查看器
 * 同时叠加标注层
 */
export function ViewerContainer() {
  const { scoreData, annotations, viewMode } = useAppStore();

  // 无数据时返回空
  if (!scoreData) {
    return (
      <div className="flex-1 flex items-center justify-center text-text-muted">
        请打开一个吉他谱文件
      </div>
    );
  }

  /**
   * 根据数据类型渲染对应的查看器
   */
  const renderViewer = () => {
    switch (scoreData.type) {
      case 'image':
        return <ImageViewer data={scoreData} />;
      case 'pdf':
        return <PdfViewer data={scoreData} />;
      case 'gtp':
        return <GtpViewer data={scoreData} />;
      default:
        return (
          <div className="flex-1 flex items-center justify-center text-red-400">
            不支持的谱面格式
          </div>
        );
    }
  };

  return (
    <div className="relative flex-1 overflow-hidden">
      {/* 谱面查看器 */}
      {renderViewer()}

      {/* 标注层覆盖 - 仅在图片/PDF模式下且启用标注模式时显示 */}
      {(scoreData.type === 'image' || scoreData.type === 'pdf') &&
       viewMode === 'annotation' && (
        <AnnotationLayer annotations={annotations} />
      )}
    </div>
  );
}
