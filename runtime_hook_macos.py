# -*- coding: utf-8 -*-
"""
macOS 运行时钩子 - PyInstaller 打包后加载动态库的辅助模块

功能:
  1. 设置 DYLD_LIBRARY_PATH 指向 _internal/ 目录
  2. 使用 @rpath 预加载所有 FluidSynth 依赖的动态库
  3. 确保 ctypes.util.find_library() 和 dyld 能定位到打包的 .dylib 文件

原理:
  - PyInstaller onedir 模式下，动态库被放在 .app/Contents/MacOS/_internal/ 目录
  - prepare_macos_build.sh 已将所有 dylib 的依赖路径重写为 @rpath/<name>.dylib
  - 此钩子设置 DYLD_LIBRARY_PATH 并被预加载库，使 dyld 能通过 @rpath 解析依赖
  - 钩子在主脚本之前执行，确保 import fluidsynth 时库已可用

注意事项:
  - 必须与 prepare_macos_build.sh 和 TAB Score Viewer_macOS.spec 配合使用
  - 开发模式下 (非 frozen) 此钩子不生效，不影响正常开发
"""

import os
import sys
import ctypes


def _setup_dylib_paths() -> None:
    """
    配置动态库搜索路径并预加载 FluidSynth 依赖库

    策略:
      1. 将 _internal/ 添加到 DYLD_LIBRARY_PATH (dyld 搜索路径优先级最高)
      2. 从 _internal/ 预加载所有 .dylib 文件 (RTLD_GLOBAL 使符号全局可见)
      3. 这样在 import fluidsynth 时，find_libfluidsynth() 和 CDLL() 都能成功
    """
    if not getattr(sys, 'frozen', False):
        return  # 开发模式，不执行

    # _internal/ 目录在 .app/Contents/MacOS/_internal/
    _internal = os.path.join(os.path.dirname(sys.executable), '_internal')

    if not os.path.isdir(_internal):
        return  # 未找到 _internal 目录，跳过

    # === 策略1: 设置 DYLD_LIBRARY_PATH ===
    # 当 fluidsynth.py 调用 find_library() 时，dyld 会在 DYLD_LIBRARY_PATH 中搜索
    # install_name_tool 已将 dylib 的 ID 改为 @rpath/<name>.dylib，
    # 设置 DYLD_LIBRARY_PATH 后，dyld 通过 @rpath 解析到 _internal/ 目录
    old_dyld = os.environ.get('DYLD_LIBRARY_PATH', '')
    if _internal not in old_dyld.split(':'):
        os.environ['DYLD_LIBRARY_PATH'] = _internal + ':' + old_dyld

    # 同时设置 DYLD_FALLBACK_LIBRARY_PATH 作为后备
    old_fallback = os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
    if _internal not in old_fallback.split(':'):
        os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = _internal + ':' + old_fallback

    # === 策略2: 按依赖顺序预加载所有 dylib ===
    # 使用 RTLD_GLOBAL 模式确保符号全局可见
    # 加载顺序很重要：被依赖的库必须先加载
    _load_order = [
        # 基础系统依赖 (无外部依赖)
        'libpcre2-8.0.dylib',
        'libintl.8.dylib',
        'libogg.0.dylib',
        'libvorbis.0.dylib',
        'libopus.0.dylib',
        'libmpg123.0.dylib',
        'libmp3lame.0.dylib',
        # 二级依赖
        'libFLAC.14.dylib',       # 依赖 libogg
        'libvorbisenc.2.dylib',   # 依赖 libvorbis
        'libglib-2.0.0.dylib',    # 依赖 libintl, libpcre2
        'libgthread-2.0.0.dylib', # 依赖 libglib
        'libreadline.8.dylib',    # 依赖 libncurses (系统)
        # 三级依赖
        'libsndfile.1.dylib',     # 依赖 libogg, libvorbis, libFLAC, libopus, libmpg123, libmp3lame
        'libportaudio.2.dylib',   # 依赖 CoreAudio (系统框架)
        # FluidSynth 本身
        'libfluidsynth.dylib',    # 用于 ctypes.util.find_library("fluidsynth")
        'libfluidsynth.3.dylib',  # FluidSynth 主库
    ]

    loaded = []
    for lib_name in _load_order:
        lib_path = os.path.join(_internal, lib_name)
        if os.path.exists(lib_path):
            try:
                ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
                loaded.append(lib_name)
            except Exception as e:
                # 某些库可能因顺序问题暂时加载失败，但不影响最终结果
                pass

    if loaded:
        print(f"[runtime_hook] 已预加载 {len(loaded)} 个动态库")


_setup_dylib_paths()