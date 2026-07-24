# -*- coding: utf-8 -*-
"""
tests/conftest.py
pytest 全局配置:
  - 将项目根目录加入 sys.path, 使 `import models` 等顶层模块导入生效
  - ApolloTab 可用性 fixture (供 difficulty_scoring 测试使用)
  - 临时目录 / 临时 SQLite / 临时 JSON 通用 fixture
"""
from __future__ import annotations

import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Iterator

import pytest


# ============================================================
# 路径: 让 `import models` / `import shortcuts` 等生效
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 必需依赖: PyQt5 + ApolloTab (difficulty_scoring)
# ============================================================
try:
    from PyQt5.QtWidgets import QApplication  # noqa: F401
    HAS_PYQT5 = True
except Exception:
    HAS_PYQT5 = False

try:
    import ApolloTab  # noqa: F401
    from ApolloTab.parser import parse_score  # noqa: F401
    HAS_APOLLOTAB = True
except Exception:
    HAS_APOLLOTAB = False


# ============================================================
# 全局 I18n signal patch
# ============================================================
# 原因: i18n.I18n 不是 QObject 子类, 但 _ensure_signal 内部尝试创建 pyqtSignal
#       在 hasattr(self, 'language_changed') 时会触发 PyQt5 metaclass 检查
#       报 "I18n cannot be converted to PyQt5.QtCore.QObject"。
#       在主程序里 _ensure_signal 只在 QApplication 已就绪且能正常创建 signal 时调用,
#       测试环境不依赖 language_changed 信号, 故 patch 为 no-op
def _noop_ensure_signal(self):
    """替换 I18n._ensure_signal, 跳过 PyQt5 signal 创建 (测试环境无 QObject 基类)"""
    pass


# 无论 PyQt5 是否可用, 都 patch (i18n 模块在 import 时就会执行 _ensure_signal 相关代码)
try:
    import i18n as _i18n_module
    _i18n_module.I18n._ensure_signal = _noop_ensure_signal
except Exception:
    pass


@pytest.fixture(scope="session")
def qapp():
    """提供 QApplication 单例 (PyQt5 widgets 需要)"""
    if not HAS_PYQT5:
        pytest.skip("PyQt5 不可用")
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # 不退出 app, 让 session 复用


@pytest.fixture
def tmp_dir() -> Iterator[Path]:
    """临时目录, 测试结束后自动清理"""
    d = Path(tempfile.mkdtemp(prefix="tabsv_test_"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def apollo_available() -> bool:
    """ApolloTab 是否可用 (供 difficulty_scoring 测试 skip 判断)"""
    return HAS_APOLLOTAB
