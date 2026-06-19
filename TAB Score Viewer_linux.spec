# -*- mode: python ; coding: utf-8 -*-
"""
============================================================
文件名: TAB Score Viewer_linux.spec
功能描述: PyInstaller Linux 打包配置(TAB Score Viewer)
         打包模式: onedir(目录模式，非单文件)
         图标: 根目录下的 icon.png

         原理: 使用PyInstaller将Python应用打包为Linux可执行程序
           - onedir模式: 生成一个文件夹，内含可执行文件和所有依赖(推荐，启动快)
           - 数据文件(locales/翻译、SO音频库)会被自动复制到输出目录
           - icon.png同时作为桌面快捷方式图标和运行时窗口图标

使用方法:
  1. 安装pyinstaller: pip install pyinstaller
  2. 执行打包:   pyinstaller "TAB Score Viewer_linux.spec"
  3. 输出目录: dist/TAB Score Viewer/
  4. 运行程序: dist/TAB Score Viewer/TAB Score Viewer

Linux 依赖安装:
  # 系统依赖 (FluidSynth 音频合成)
  Ubuntu/Debian: sudo apt-get install libfluidsynth3 libsndfile1 libpulse0
  Fedora/RHEL:   sudo dnf install fluidsynth-libs libsndfile pulseaudio-libs
  Arch Linux:    sudo pacman -S fluidsynth libsndfile pulseaudio

创建日期: 2026-06-19
最后修改: 2026-06-19 (v0.2.11: 新建 Linux 打包配置)
============================================================
"""

import os
import sys

# 项目根目录(本spec文件所在目录)
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))

block_cipher = None

# ===== 数据文件配置 =====
# 原理: PyInstaller会将这些文件/目录复制到打包输出目录中
# 运行时通过 sys.executable 所在目录定位(见 get_app_icon() 函数)
datas = [
    # 翻译文件目录 -> 打包后保留在 locales/
    (os.path.join(SPEC_DIR, 'locales'), 'locales'),
    # SVG图标目录 -> 打包后保留在 icons/(位于_internal/)
    (os.path.join(SPEC_DIR, 'icons'), 'icons'),
    # FluidSynth 音频合成SO库(音频播放功能依赖)
    # 注意: 如果系统已安装 fluidsynth 可注释掉此行，运行时会自动从系统路径加载
    # (os.path.join(SPEC_DIR, 'libfluidsynth.so.3'), '.'),
    # SoundFont 音色库文件(GTP音频播放依赖，约140MB)
    (os.path.join(SPEC_DIR, 'soundfont'), 'soundfont'),
    # 应用图标(Linux 使用 PNG 格式)
    (os.path.join(SPEC_DIR, 'icon.png'), '.'),
]

# ===== 隐藏导入配置 =====
# 原理: PyInstaller静态分析可能遗漏的动态导入模块，手动声明确保打包完整
hiddenimports = [
    # ApolloTab GTP引擎库(动态导入)
    'ApolloTab',
    'ApolloTab.parser',
    'ApolloTab.renderer',
    'ApolloTab.audio',
    'ApolloTab.models',
    'ApolloTab.utils',
    # 第三方依赖
    'pyguitarpro',
    'pyfluidsynth',
]

a = Analysis(
    [os.path.join(SPEC_DIR, 'TAB Score Viewer.py')],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型模块以减小包体积
        'matplotlib', 'numpy', 'scipy', 'pandas',
        'tkinter', 'IPython', 'jupyter',
        'pytest', 'black', 'isort', 'mypy',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TAB Score Viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,          # 启用UPX压缩(减小体积，需安装UPX: sudo apt-get install upx-ucl)
    console=False,     # 不显示控制台窗口(GUI应用)
    icon=os.path.join(SPEC_DIR, 'icon.png'),  # 可执行文件图标(Linux用PNG格式)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TAB Score Viewer',  # 输出目录名: dist/TAB Score Viewer/
)
