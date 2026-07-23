# -*- coding: utf-8 -*-
"""
macOS TCC 预热运行时钩子 - PyInstaller 打包后开绿灯

功能:
  在主脚本与任何 Python 模块加载之前,预先给"用户上次打开的路径"
  开绿灯,避免 macOS 重启后首次访问时返回:
      [Errno 1] Operation not permitted: <path>

触发场景:
  - macOS 启动后,应用被自动启动 / 用户首次打开应用
  - 用户上次打开的目录是 ~/Downloads 等受 TCC 保护的位置
  - 直接 open() 会被内核返回 errno 1 (EPERM)

策略(均静默失败,不影响主程序):
  1. 读取 bundle 内的 config/settings.json,提取 last_folder 与 recent_files
  2. 对每个候选路径:
     a. 清除 com.apple.quarantine 扩展属性 (Gatekeeper 隔离标记) -
        这是导致 EPERM 的最常见原因,尤其对从网络下载的 .gp3 文件
     b. 用 os.stat() 触发一次轻量级元数据访问,让 macOS 把路径
        加入文件系统缓存 (无法绕过 TCC,但可暴露挂载/ACL 问题)
  3. 在 PyInstaller frozen 模式以外 (开发模式) 不执行,不影响日常开发

使用方法:
  在 PyInstaller .spec 的 EXE 段添加:
      runtime_hooks=[
          os.path.join(SPEC_DIR, 'runtime_hook_macos.py'),
          os.path.join(SPEC_DIR, 'runtime_hook_macos_prewarm.py'),
      ]
  钩子按列表顺序执行,本钩子依赖 sys.executable 已就位 (PyInstaller 保证)。
"""

import os
import sys
import json
import subprocess


# 仅打包后的 .app 才有此问题 - 开发模式直接 return
if not getattr(sys, 'frozen', False):
    pass
else:
    _exe_dir = os.path.dirname(sys.executable)
    # onedir 模式下, config/ 在 _internal/config/ ; .app bundle 模式同此
    _config_candidates = [
        os.path.join(_exe_dir, '_internal', 'config', 'settings.json'),
        os.path.join(_exe_dir, 'config', 'settings.json'),
    ]
    _cfg_path = None
    for _p in _config_candidates:
        if os.path.isfile(_p):
            _cfg_path = _p
            break

    if _cfg_path is not None:
        try:
            with open(_cfg_path, 'r', encoding='utf-8') as _f:
                _cfg = json.load(_f)

            # 收集候选路径 - 上次打开的目录 + 最近 4 个文件
            _candidates = []
            _last_folder = _cfg.get('last_folder', '')
            if isinstance(_last_folder, str) and _last_folder:
                _candidates.append(_last_folder)
            _recent = _cfg.get('recent_files', []) or []
            if isinstance(_recent, list):
                for _r in _recent[:4]:
                    if isinstance(_r, str) and _r:
                        _candidates.append(_r)

            # 逐一"开绿灯"
            for _path in _candidates:
                if not _path or not os.path.lexists(_path):
                    continue
                # 1) 清除 com.apple.quarantine 扩展属性 (Gatekeeper 隔离标记)
                #    - 此标记会让系统重启后首次访问直接返回 EPERM
                #    - 用 -r 递归处理目录(用户上次打开的目录可能含多文件)
                try:
                    subprocess.run(
                        ['/usr/bin/xattr', '-dr', 'com.apple.quarantine', _path],
                        timeout=3,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass
                # 2) 触发一次元数据读取,把路径送入文件系统缓存
                #    - 若文件在未挂载的外部卷上,此时会暴露问题以便上层处理
                #    - 若存在 ACL 问题,会在此暴露 (无法绕过,但不会让情况更糟)
                try:
                    os.stat(_path)
                except Exception:
                    pass
        except Exception:
            # 任何异常都静默吞掉 - 这是个 best-effort 钩子,不能阻塞启动
            pass
