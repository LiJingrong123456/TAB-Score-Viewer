# TAB Score Viewer - 万能吉他谱查看器

## 项目简介

TAB Score Viewer 是一款专业级的吉他谱查看与练习工具，支持多种格式的吉他谱文件，提供播放控制、变速曲线、文本标注等强大功能。

## 核心功能

| 功能 | 描述 | 支持格式 |
|------|------|----------|
| **多格式支持** | PNG、JPG、JPEG、WEBP、PDF、GTP(GP3-GP7) | 全部 |
| **谱面显示** | 高质量渲染，缩放(10%-500%)，平移拖拽 | 图片/PDF/GTP |
| **播放控制** | 播放/暂停、进度条拖拽、快进/快退5秒 | 全部 |
| **速度调节** | 0.25x - 4.0x 变速播放 | 全部 |
| **速度曲线** | 可视化编辑变速曲线（渐入渐出、渐进加速等预设） | 图片/PDF |
| **文本标注** | 在谱面任意位置添加演奏技巧说明，支持6种颜色 | 图片/PDF |
| **循环播放** | 全局循环 + 区域A-B循环 | 全部 |
| **导入导出** | 标注数据JSON导入/导出 | 图片/PDF |

## 技术栈

```
前端框架:    React 18 + TypeScript 5
构建工具:    Vite 6
UI样式:      Tailwind CSS 3
状态管理:    Zustand 4
图标库:      Lucide React
图表库:      Recharts (速度曲线)
PDF解析:     react-pdf (pdf.js)
GTP解析:     @coderline/alphatab
拖拽交互:    @dnd-kit
```

## 快速开始

### 安装依赖

```bash
# 使用国内镜像源安装（推荐清华源）
npm install --registry=https://registry.npmmirror.com
```

### 开发模式运行

```bash
npm run dev
```

访问 http://localhost:3000 查看应用

### 生产构建

```bash
npm run build
npm run preview
```

## 项目结构

```
src/
├── components/
│   ├── Viewer/              # 谱面查看器组件
│   │   ├── ImageViewer.tsx  #   图片查看器
│   │   ├── PdfViewer.tsx    #   PDF查看器
│   │   ├── GtpViewer.tsx    #   GTP(Guitar Pro)查看器
│   │   └── ViewerContainer.tsx # 自动选择查看器的容器
│   ├── Controls/            # 播放控制组件
│   │   ├── PlayBar.tsx      #   进度条和播放按钮
│   │   ├── SpeedCurve.tsx   #   速度曲线编辑器
│   │   └── ControlPanel.tsx #   控制面板容器
│   ├── Annotation/          # 标注系统组件
│   │   ├── AnnotationLayer.tsx # 标注层(覆盖在谱面上)
│   │   └── NoteEditor.tsx   #   标注管理面板
│   └── common/              # 通用组件
│       ├── FileLoader.tsx   #   文件加载器
│       └── Toolbar.tsx      #   顶部工具栏
├── hooks/                   # 自定义Hooks
│   ├── usePlayer.ts         #   播放控制逻辑
│   ├── useAnnotation.ts     #   标注管理逻辑
│   └── useSpeedCurve.ts     #   速度曲线管理
├── stores/                  # 状态管理(Zustand)
│   └── playerStore.ts       #   全局应用状态
├── types/                   # TypeScript类型定义
│   └── index.ts             #   所有接口和类型
├── utils/                   # 工具函数
│   └── cn.ts                #   类名合并工具
├── App.tsx                  # 主应用组件
├── main.tsx                 # 应用入口
└── index.css                # 全局样式
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Space` | 播放 / 暂停 |
| `Ctrl + ←` | 减速 (-0.1x) |
| `Ctrl + →` | 加速 (+0.1x) |

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

## 开源依赖

| 库名 | 版本 | 许可证 | 用途 |
|------|------|--------|------|
| @coderline/alphatab | ^1.3+ | MPL-2.0 | Guitar Pro文件解析/渲染/播放 |
| react-pdf | ^7.x | MIT | PDF文件渲染 |
| recharts | ^2.x | MIT | 速度曲线图表 |
| @dnd-kit/core | ^6.x | MIT | 标注拖拽交互 |
| zustand | ^4.x | MIT | 状态管理 |
| lucide-react | ^0.x | ISC | 图标库 |

## 许可证

MIT License
