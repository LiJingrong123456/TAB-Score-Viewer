#!/bin/bash
# ============================================================
# macOS DMG 打包脚本
# 功能: 将 dist/TAB Score Viewer.app 打包为 .dmg 镜像
#
# 使用方法:
#   1. 先运行 pyinstaller 完成打包
#   2. 执行: bash build_dmg.sh
#   3. 输出: dist/TAB Score Viewer_<version>.dmg
# ============================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="TAB Score Viewer"
APP_PATH="$PROJECT_DIR/dist/$APP_NAME.app"
VERSION="2.0.7"
DMG_NAME="${APP_NAME}_${VERSION}.dmg"
DMG_PATH="$PROJECT_DIR/dist/$DMG_NAME"
STAGING_DIR="$PROJECT_DIR/dist/_dmg_staging"

# 检查 .app 是否存在
if [ ! -d "$APP_PATH" ]; then
    echo "错误: 未找到 $APP_PATH"
    echo "请先执行 pyinstaller \"TAB Score Viewer_macOS.spec\" 完成打包"
    exit 1
fi

# 清理旧的暂存目录
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

echo "=== 创建 DMG 安装镜像 ==="

# ============================================================
# Step 1: 复制 .app 到暂存目录
# ============================================================
echo "  [1/4] 复制 .app 到暂存目录..."
cp -R "$APP_PATH" "$STAGING_DIR/$APP_NAME.app"

# ============================================================
# Step 2: 创建 /Applications 快捷方式
# ============================================================
echo "  [2/4] 创建 /Applications 快捷方式..."
ln -s /Applications "$STAGING_DIR/Applications"

# ============================================================
# Step 3: 生成 DMG 卷宗图标 (可选，复用 icon.icns)
# ============================================================
echo "  [3/4] 设置卷宗图标..."
# 将 icon.icns 复制为卷宗图标
if [ -f "$PROJECT_DIR/icon.icns" ]; then
    cp "$PROJECT_DIR/icon.icns" "$STAGING_DIR/.VolumeIcon.icns"
    # 设置自定义卷宗图标的标志位
    SetFile -a C "$STAGING_DIR" 2>/dev/null || true
fi

# ============================================================
# Step 4: 创建 DMG
# ============================================================
echo "  [4/4] 创建 DMG 文件..."

# 计算合适的 DMG 大小 (.app 大小 + 100MB 余量)
APP_SIZE_MB=$(du -sm "$APP_PATH" | cut -f1)
DMG_SIZE_MB=$((APP_SIZE_MB + 150))
echo "  .app 大小: ${APP_SIZE_MB}MB, DMG 分配大小: ${DMG_SIZE_MB}MB"

# 使用 hdiutil 创建压缩 DMG
# -srcfolder: 源文件夹
# -volname: 卷宗名称 (挂载后显示的名称)
# -fs: 文件系统 HFS+
# -format: UDZO = 压缩的 UDIF 只读镜像
# -imagekey zlib-level=9: 最大压缩级别
hdiutil create \
    -srcfolder "$STAGING_DIR" \
    -volname "$APP_NAME" \
    -fs HFS+ \
    -format UDZO \
    -imagekey zlib-level=9 \
    -size "${DMG_SIZE_MB}m" \
    "$DMG_PATH" \
    -ov

# ============================================================
# 清理
# ============================================================
echo "  清理暂存目录..."
rm -rf "$STAGING_DIR"

# ============================================================
# 完成
# ============================================================
echo ""
echo "=== DMG 打包完成! ==="
echo "  输出: $DMG_PATH"
echo "  大小: $(du -sh "$DMG_PATH" | cut -f1)"
echo ""
echo "  分发前建议签名:"
echo "    codesign --force --deep --sign - \"$APP_PATH\""
echo "    hdiutil verify \"$DMG_PATH\""
echo ""
echo "  安装方式: 双击 DMG → 将 $APP_NAME.app 拖入 Applications 文件夹"