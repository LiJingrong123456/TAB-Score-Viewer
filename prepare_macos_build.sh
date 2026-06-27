#!/bin/bash
# ============================================================
# macOS 构建准备脚本
# 功能:
#   1. 生成 icon.icns (从 icon.png)
#   2. 收集 FluidSynth 及其依赖的 dylib 到 _dylibs/ 目录
#   3. 使用 install_name_tool 重写 dylib 的依赖路径为 @rpath
#
# 使用方法:
#   chmod +x prepare_macos_build.sh
#   ./prepare_macos_build.sh
#
# 注意: 此脚本不需要 sudo
# ============================================================

set -e  # 遇到错误立即退出

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "=== 项目目录: $PROJECT_DIR"

# ============================================================
# Step 1: 生成 icon.icns
# ============================================================
echo ""
echo "=== [1/3] 生成 icon.icns ==="

ICON_PNG="$PROJECT_DIR/icon.png"
ICONSET_DIR="$PROJECT_DIR/icon.iconset"
ICON_ICNS="$PROJECT_DIR/icon.icns"

if [ ! -f "$ICON_PNG" ]; then
    echo "错误: 未找到 $ICON_PNG，请确保 icon.png 存在"
    exit 1
fi

# 创建 iconset 目录 (macOS 标准图标集)
mkdir -p "$ICONSET_DIR"

# 从 2048x2048 PNG 生成各尺寸 (使用 sips 工具)
sips -z 16 16   "$ICON_PNG" --out "$ICONSET_DIR/icon_16x16.png"      > /dev/null 2>&1
sips -z 32 32   "$ICON_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png"  > /dev/null 2>&1
sips -z 32 32   "$ICON_PNG" --out "$ICONSET_DIR/icon_32x32.png"      > /dev/null 2>&1
sips -z 64 64   "$ICON_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png"  > /dev/null 2>&1
sips -z 128 128 "$ICON_PNG" --out "$ICONSET_DIR/icon_128x128.png"    > /dev/null 2>&1
sips -z 256 256 "$ICON_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png" > /dev/null 2>&1
sips -z 256 256 "$ICON_PNG" --out "$ICONSET_DIR/icon_256x256.png"    > /dev/null 2>&1
sips -z 512 512 "$ICON_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png" > /dev/null 2>&1
sips -z 512 512 "$ICON_PNG" --out "$ICONSET_DIR/icon_512x512.png"    > /dev/null 2>&1
cp "$ICON_PNG" "$ICONSET_DIR/icon_512x512@2x.png"

# 使用 iconutil 转换为 .icns
iconutil -c icns "$ICONSET_DIR" --output "$ICON_ICNS"
rm -rf "$ICONSET_DIR"

echo "  已生成: $ICON_ICNS"

# ============================================================
# Step 2: 收集并处理 dylib
# ============================================================
echo ""
echo "=== [2/3] 收集 FluidSynth 及其依赖的动态库 ==="

DYLIB_DIR="$PROJECT_DIR/_dylibs"
rm -rf "$DYLIB_DIR"
mkdir -p "$DYLIB_DIR"

# 定义需要收集的动态库 (每行两个值: 源路径 目标文件名)
# 使用 cp -L 解析 symlink，确保复制的是实际文件

collect_dylib() {
    local src_path="$1"
    local dst_name="$2"
    if [ -f "$src_path" ]; then
        cp -L "$src_path" "$DYLIB_DIR/$dst_name"
        echo "  已复制: $src_path -> $dst_name"
    else
        echo "  警告: 未找到 $src_path"
    fi
}

collect_dylib "/usr/local/lib/libfluidsynth.3.dylib"  "libfluidsynth.3.dylib"
collect_dylib "/usr/local/lib/libfluidsynth.dylib"     "libfluidsynth.dylib"
collect_dylib "/usr/local/lib/libglib-2.0.0.dylib"     "libglib-2.0.0.dylib"
collect_dylib "/usr/local/lib/libgthread-2.0.0.dylib"  "libgthread-2.0.0.dylib"
collect_dylib "/usr/local/lib/libintl.8.dylib"         "libintl.8.dylib"
collect_dylib "/usr/local/lib/libsndfile.1.dylib"      "libsndfile.1.dylib"
collect_dylib "/usr/local/lib/libportaudio.2.dylib"    "libportaudio.2.dylib"
collect_dylib "/usr/local/lib/libreadline.8.dylib"     "libreadline.8.dylib"
collect_dylib "/usr/local/lib/libpcre2-8.0.dylib"      "libpcre2-8.0.dylib"
collect_dylib "/usr/local/lib/libogg.0.dylib"          "libogg.0.dylib"
collect_dylib "/usr/local/lib/libvorbis.0.dylib"       "libvorbis.0.dylib"
collect_dylib "/usr/local/lib/libvorbisenc.2.dylib"    "libvorbisenc.2.dylib"
collect_dylib "/usr/local/lib/libFLAC.14.dylib"        "libFLAC.14.dylib"
collect_dylib "/usr/local/lib/libopus.0.dylib"         "libopus.0.dylib"
collect_dylib "/usr/local/lib/libmpg123.0.dylib"       "libmpg123.0.dylib"
collect_dylib "/usr/local/lib/libmp3lame.0.dylib"      "libmp3lame.0.dylib"

echo "  动态库收集完毕，共 $(ls -1 "$DYLIB_DIR"/*.dylib 2>/dev/null | wc -l | tr -d ' ') 个文件"

# ============================================================
# Step 3: 使用 install_name_tool 重写 dylib 依赖路径
# ============================================================
echo ""
echo "=== [3/3] 重写 dylib 依赖路径 (install_name_tool) ==="

# 收集 _dylibs 目录中的 dylib 文件名列表 (不含路径)
DYLIB_NAMES=()
# macOS 的 bash 3: 避免未匹配的 glob 保留为字面字符串
shopt -s nullglob 2>/dev/null || true
for f in "$DYLIB_DIR"/*.dylib; do
    [ -f "$f" ] && DYLIB_NAMES+=("$(basename "$f")")
done
shopt -u nullglob 2>/dev/null || true

rewrite_dylib_id_and_deps() {
    local dylib_path="$1"
    local dylib_name="$(basename "$dylib_path")"

    echo "  处理: $dylib_name"

    # === Step 3a: 修改 LC_ID_DYLIB (自身标识) ===
    # 获取当前 install name
    local old_id
    old_id=$(otool -D "$dylib_path" 2>/dev/null | tail -1)
    if [ -n "$old_id" ] && [ "$old_id" != "$dylib_path" ]; then
        install_name_tool -id "@rpath/$dylib_name" "$dylib_path" 2>/dev/null
    fi

    # === Step 3b: 修改所有指向 Homebrew 路径的 LC_LOAD_DYLIB (依赖引用) ===
    # 获取所有依赖
    local deps
    deps=$(otool -L "$dylib_path" 2>/dev/null | tail -n +2 | awk '{print $1}')

    for dep in $deps; do
        # 只处理 /usr/local/ 下的依赖 (Homebrew 安装的)
        if [[ "$dep" == /usr/local/* ]]; then
            local dep_name=$(basename "$dep")
            # 检查这个依赖是否在我们收集的 _dylibs 中
            local found=0
            for n in "${DYLIB_NAMES[@]}"; do
                if [ "$n" == "$dep_name" ]; then
                    found=1
                    break
                fi
            done
            if [ "$found" -eq 1 ]; then
                echo "    重写依赖: $dep -> @rpath/$dep_name"
                install_name_tool -change "$dep" "@rpath/$dep_name" "$dylib_path" 2>/dev/null
            else
                # 依赖不在 _dylibs 中，可能来自 Cellar 的特定版本路径
                # 尝试用 basename 匹配
                local dep_basename=$(basename "$dep")
                for f2 in "$DYLIB_DIR"/*.dylib; do
                    local f2_name=$(basename "$f2")
                    if [ "$f2_name" == "$dep_basename" ]; then
                        echo "    重写依赖(basename匹配): $dep -> @rpath/$f2_name"
                        install_name_tool -change "$dep" "@rpath/$f2_name" "$dylib_path" 2>/dev/null
                        break
                    fi
                done
            fi
        fi
        # 系统框架 (/System/Library, /usr/lib) 不处理
    done
}

# 对每个 dylib 执行路径重写 (只在有文件时才处理)
if [ ${#DYLIB_NAMES[@]} -gt 0 ]; then
    shopt -s nullglob 2>/dev/null || true
    for f in "$DYLIB_DIR"/*.dylib; do
        [ -f "$f" ] && rewrite_dylib_id_and_deps "$f"
    done
    shopt -u nullglob 2>/dev/null || true
fi

echo ""
echo "=== 全部完成! ==="
echo ""
echo "生成的文件:"
echo "  - $ICON_ICNS"
echo "  - ${DYLIB_DIR}/ (共 $(ls -1 "$DYLIB_DIR"/*.dylib 2>/dev/null | wc -l | tr -d ' ') 个动态库)"
echo ""
echo "下一步:"
echo "  1. 确保已安装 pyinstaller:"
echo "     pip install pyinstaller"
echo "  2. 运行打包:"
echo "     pyinstaller \"TAB Score Viewer_macOS.spec\""
echo "  3. 输出目录: dist/TAB Score Viewer.app/"