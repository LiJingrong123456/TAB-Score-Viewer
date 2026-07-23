# -*- mode: python ; coding: utf-8 -*-
"""
============================================================
文件名: TAB Score Viewer_macOS.spec
功能描述: PyInstaller 打包配置 (macOS .app 版本)
         打包模式: onedir + BUNDLE → .app 目录
         
         打包原理:
           1. Analysis 阶段: 分析 Python 脚本的导入依赖树
           2. PYZ 阶段:     将纯 Python 模块打包为存档
           3. EXE 阶段:     生成可执行文件 (Mach-O)
           4. COLLECT 阶段: 收集所有依赖到输出目录
           5. BUNDLE 阶段:  将输出目录封装为 .app 捆绑包 (含 Info.plist)
         
         FluidSynth 动态库处理:
           - prepare_macos_build.sh 将 dylib 收集到 _dylibs/ 目录
           - install_name_tool 已将路径重写为 @rpath/<name>.dylib
           - 运行时钩子 (runtime_hook_macos.py) 设置 DYLD_LIBRARY_PATH 并预加载
           - 系统框架 (CoreAudio, AudioUnit, CoreFoundation 等) 不打包

使用方法:
  1. 准备:   bash prepare_macos_build.sh
  2. 安装:   pip install pyinstaller
  3. 打包:   pyinstaller "TAB Score Viewer_macOS.spec"
  4. 输出:   dist/TAB Score Viewer.app/

创建日期: 2026-06-26
============================================================
"""

import os
import sys
import glob

# 项目根目录
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))

block_cipher = None


# ===== 动态库配置 =====
# prepare_macos_build.sh 已将 FluidSynth 及其依赖的 dylib
# 收集到 _dylibs/ 目录，并重写了依赖路径为 @rpath
DYLIB_DIR = os.path.join(SPEC_DIR, '_dylibs')

# 收集 _dylibs/ 中的所有 .dylib 文件
# 格式: (源文件绝对路径, 目标目录) -> 文件会被复制到 _internal/
_binaries = []
if os.path.isdir(DYLIB_DIR):
    for f in sorted(glob.glob(os.path.join(DYLIB_DIR, '*.dylib'))):
        _binaries.append((f, '_internal'))
    print(f"[spec] 发现 {len(_binaries)} 个动态库: {DYLIB_DIR}")
else:
    print(f"[spec] 警告: 未找到 _dylibs/ 目录，请先运行 prepare_macos_build.sh")


# ===== 数据文件配置 =====
datas = [
    # 翻译文件目录
    (os.path.join(SPEC_DIR, 'locales'), 'locales'),
    # SVG图标目录
    (os.path.join(SPEC_DIR, 'icons'), 'icons'),
    # SoundFont 音色库 (GTP音频播放依赖)
    (os.path.join(SPEC_DIR, 'soundfont'), 'soundfont'),
    # 应用图标 (.icns 用于 .app 图标, .png 用于 QIcon 运行时加载)
    (os.path.join(SPEC_DIR, 'icon.icns'), '.'),
    (os.path.join(SPEC_DIR, 'icon.png'), '.'),
    # 应用配置目录
    (os.path.join(SPEC_DIR, 'config'), 'config'),
]


# ===== 隐藏导入配置 =====
# PyInstaller 静态分析可能遗漏的动态导入模块
hiddenimports = [
    # ApolloTab GTP引擎
    'ApolloTab',
    'ApolloTab.parser',
    'ApolloTab.renderer',
    'ApolloTab.audio',
    'ApolloTab.models',
    'ApolloTab.utils',
    'ApolloTab.player',
    # 第三方依赖
    'guitarpro',
    'pyfluidsynth',
    'fluidsynth',
]

# ===== 排除模块 =====
# 排除不需要的大型模块以减小包体积
_excludes = [
    'matplotlib', 'scipy', 'pandas',
    'tkinter', 'IPython', 'jupyter',
    'pytest', 'black', 'isort', 'mypy',
    # PyQt5 中不需要的模块
    'PyQt5.QtBluetooth',
    'PyQt5.QtDBus',
    'PyQt5.QtDesigner',
    'PyQt5.QtHelp',
    'PyQt5.QtMultimedia',
    'PyQt5.QtNetwork',
    'PyQt5.QtNfc',
    'PyQt5.QtOpenGL',
    'PyQt5.QtPositioning',
    'PyQt5.QtQml',
    'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets',
    'PyQt5.QtSensors',
    'PyQt5.QtSerialPort',
    'PyQt5.QtSql',
    'PyQt5.QtSvg',
    'PyQt5.QtTest',
    'PyQt5.QtWebChannel',
    'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtWebSockets',
    'PyQt5.QtXml',
    'PyQt5.QtXmlPatterns',
]


a = Analysis(
    [os.path.join(SPEC_DIR, 'TAB Score Viewer.py')],
    pathex=[SPEC_DIR],
    binaries=_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[
        os.path.join(SPEC_DIR, 'runtime_hook_macos.py'),
        # macOS TCC 预热钩子: 在主脚本加载前给用户上次打开的路径开绿灯
        # 修复 [Errno 1] Operation not permitted (系统重启后首次访问)
        os.path.join(SPEC_DIR, 'runtime_hook_macos_prewarm.py'),
    ],
    excludes=_excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ===== onedir: EXE (仅引导程序, 不含数据) =====
# exclude_binaries=True 表示实际数据由后续 COLLECT 处理
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TAB Score Viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # macOS 下 UPX 压缩可能导致 dylib 签名失效，关闭
    console=False,       # GUI 应用，不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,    # 自动检测当前架构 (x86_64 或 arm64)
    codesign_identity=None,
    entitlements_file=None,
)

# ===== onedir: COLLECT (收集所有依赖到 dist/TAB Score Viewer/) =====
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='TAB Score Viewer',
)

# ===== macOS .app 捆绑包配置 =====
# COLLECT 的输出会被整个打包进 .app/Contents/MacOS/
# BUNDLE 使用 icon.icns 作为 .app 图标
# 运行时 QIcon 会通过 _find_icon_file 查找 icon.png/icon.icns 作为窗口图标
app = BUNDLE(
    coll,
    name='TAB Score Viewer.app',
    icon=os.path.join(SPEC_DIR, 'icon.icns'),
    bundle_identifier='com.tabscoreviewer.app',
    bundle_name='TAB Score Viewer',
    info_plist={
        'CFBundleDisplayName': 'TAB Score Viewer',
        'CFBundleName': 'TAB Score Viewer',
        'CFBundleVersion': '2.0.7',
        'CFBundleShortVersionString': '2.0.7',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleExecutable': 'TAB Score Viewer',
        'CFBundleIconFile': 'icon.icns',
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Copyright 2026. All rights reserved.',
        'LSMinimumSystemVersion': '10.15',  # macOS Catalina 最低支持
        'NSRequiresAquaSystemAppearance': False,  # 支持深色模式
        'NSSupportsAutomaticGraphicsSwitching': True,
    },
)