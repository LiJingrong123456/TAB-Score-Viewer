# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Update Checker Module

更新检查模块:
  - 查询 GitHub Releases 最新版本
  - 与本地 VERSION 比对
  - 异步执行(QThreadPool)以避免阻塞 UI
  - 网络异常容错: 超时、连接错误、非 2xx 响应均归类为网络错误

SSL 证书处理 (macOS 常见问题):
  1. 优先使用 certifi 包提供的 CA bundle (如果已安装)
  2. 其次使用系统默认 CA
  3. 验证失败时自动 fallback 到 unverified context (一次性,带警告)
  4. 最终仍失败: 在 error_message 中附带英文修复指引

API 端点:
  - GitHub REST: https://api.github.com/repos/{owner}/{repo}/releases/latest
  - 文档: https://docs.github.com/en/rest/releases/releases#get-the-latest-release

依赖:
  - 仅使用 Python 标准库(urllib, json, ssl, socket), certifi 为可选
"""

import os
import ssl
import json
import socket
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib import request as urlrequest
from urllib.error import URLError, HTTPError

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal

from constants import _APP_BASE_DIR


# ============================================================
# 常量
# ============================================================

GITHUB_OWNER: str = "Zhuwenqian"
GITHUB_REPO: str = "TAB-Score-Viewer"
# GitHub API 端点（返回 latest release 的 JSON）
GITHUB_API_LATEST: str = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
# 浏览器打开用的 release 页面 URL
GITHUB_RELEASES_PAGE: str = (
    f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
)

# 网络请求超时（秒）- 启动检查时如果网络差也不能阻塞用户太久
REQUEST_TIMEOUT: float = 5.0

# GitHub API User-Agent（必须设置，否则可能返回 403）
USER_AGENT: str = "TAB-ScoreViewer-UpdateChecker"


# ============================================================
# 数据结构
# ============================================================

class UpdateStatus(Enum):
    """更新检查结果状态"""
    NEW_VERSION = "new_version"      # 发现新版本
    UP_TO_DATE = "up_to_date"        # 已是最新
    NETWORK_ERROR = "network_error"  # 网络异常（含超时、HTTP 错误、JSON 解析失败）
    NO_RELEASE = "no_release"        # 仓库还没有 release


@dataclass
class UpdateResult:
    """更新检查结果数据类"""
    status: UpdateStatus
    current_version: str                       # 本地 VERSION（如 "2.2.0"）
    latest_version: Optional[str] = None       # 远端最新 tag（如 "v2.3.0"，去前缀 v）
    release_url: Optional[str] = None          # release 页面 URL（用于点击打开）
    error_message: Optional[str] = None        # 错误详情（仅 NETWORK_ERROR 时填充）

    @property
    def is_new_version(self) -> bool:
        return self.status == UpdateStatus.NEW_VERSION

    @property
    def is_network_error(self) -> bool:
        return self.status == UpdateStatus.NETWORK_ERROR


# ============================================================
# 版本比较工具
# ============================================================

def _normalize_version(raw: str) -> Optional[tuple]:
    """
    把版本字符串解析为可比较的元组。

    支持:
      - "2.2.0"     -> (2, 2, 0)
      - "v2.2.0"    -> (2, 2, 0)
      - "v2.2.0-rc1" -> (2, 2, 0)  (忽略预发布标签，按正式版比较)
      - "2.2"       -> (2, 2)

    解析失败返回 None。
    """
    if not raw:
        return None
    s = raw.strip()
    # 去掉前缀 v/V
    if s and s[0] in ("v", "V"):
        s = s[1:]
    # 去掉预发布后缀（如 -rc1, -beta1, +metadata）
    for sep in ("-", "+"):
        if sep in s:
            s = s.split(sep, 1)[0]
    parts = s.split(".")
    try:
        return tuple(int(p) for p in parts if p != "")
    except (ValueError, TypeError):
        return None


def is_newer(remote: str, local: str) -> Optional[bool]:
    """
    比较 remote 与 local 版本号。
    返回:
      True  - remote 更新
      False - local 相同或更新
      None  - 无法解析
    """
    r = _normalize_version(remote)
    l = _normalize_version(local)
    if r is None or l is None:
        return None
    # 用相同长度比较，避免 (2,2) vs (2,2,0) 误判
    n = max(len(r), len(l))
    r_padded = r + (0,) * (n - len(r))
    l_padded = l + (0,) * (n - len(l))
    return r_padded > l_padded


# ============================================================
# 本地版本号读取
# ============================================================

def get_local_version() -> str:
    """
    从 VERSION 文件读取本地版本号。
    失败时返回 "0.0.0"（确保首次发布时一定被识别为"有新版本"）。
    """
    try:
        version_path = os.path.join(_APP_BASE_DIR, "VERSION")
        if os.path.exists(version_path):
            with open(version_path, "r", encoding="utf-8") as f:
                v = f.read().strip()
                if v:
                    return v
    except Exception:
        pass
    return "0.0.0"


# ============================================================
# SSL 上下文构造（certifi 优先 + 系统 fallback）
# ============================================================

def _try_get_certifi_cafile() -> Optional[str]:
    """
    尝试获取 certifi 包提供的 CA bundle 路径。
    找不到则返回 None（certifi 未安装或导入失败）。
    """
    try:
        import certifi  # type: ignore
        return certifi.where()
    except Exception:
        return None


# 用于在结果中给用户的 SSL 错误修复提示（统一英文）
_SSL_HINT = (
    "\n\nSSL certificate verification failed. This is a known issue, especially on macOS.\n"
    "Try one of the following:\n"
    "  1. Run the 'Install Certificates.command' shipped with Python (macOS).\n"
    "  2. Install 'certifi' (pip install certifi) and restart the app.\n"
    "  3. Set environment variable SSL_CERT_FILE to a valid CA bundle path."
)


def _is_ssl_verify_error(err: BaseException) -> bool:
    """判断异常是否由 SSL 证书验证失败引起"""
    msg = str(err) or ""
    return (
        "CERTIFICATE_VERIFY_FAILED" in msg
        or "certificate verify failed" in msg.lower()
    )


def _build_ssl_context() -> ssl.SSLContext:
    """
    构造 SSL 上下文,优先级:
      1. certifi 包提供的 CA bundle
      2. 系统默认 CA
      3. 不验证证书 (最后兜底, 通常不会走到这里, 只在用户主动设置时)
    """
    # 1) 尝试 certifi
    cafile = _try_get_certifi_cafile()
    if cafile and os.path.exists(cafile):
        try:
            ctx = ssl.create_default_context(cafile=cafile)
            return ctx
        except Exception:
            pass
    # 2) 系统默认
    try:
        ctx = ssl.create_default_context()
        return ctx
    except Exception:
        pass
    # 3) 最后兜底 - 不验证（仅作为防御性 fallback, 正常不会触发）
    return ssl._create_unverified_context()


# ============================================================
# 同步检查接口（供非 UI 场景使用）
# ============================================================

def _do_request(ssl_ctx: Optional[ssl.SSLContext]) -> bytes:
    """
    实际发起 HTTPS 请求,返回响应 body 字节串。
    抛出各种异常由调用方捕获。
    """
    req = urlrequest.Request(
        GITHUB_API_LATEST,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
        },
    )
    if ssl_ctx is None:
        # 显式不验证证书的 fallback
        return urlrequest.urlopen(req, timeout=REQUEST_TIMEOUT, context=ssl._create_unverified_context()).read()
    return urlrequest.urlopen(req, timeout=REQUEST_TIMEOUT, context=ssl_ctx).read()


def check_for_update() -> UpdateResult:
    """
    同步执行一次更新检查。
    适用于: 在子线程中调用, 再把结果通过信号投递给 UI。

    返回 UpdateResult, 调用方根据 status 决定下一步 UI 行为。

    SSL 错误处理流程:
      1. 先用 certifi (如有) / 系统 CA 验证
      2. 失败若是 SSL 证书错误, 自动 fallback 到 unverified context 重试一次
      3. 重试成功: 控制台打印警告, error_message 仍填 None (不算错误)
      4. 重试仍失败: 错误信息附带英文 SSL 修复提示
    """
    current = get_local_version()

    # 第一次尝试: 用 certifi / 系统 CA 验证
    primary_ctx = _build_ssl_context()
    try:
        raw = _do_request(primary_ctx)
    except (HTTPError, URLError, socket.timeout, TimeoutError, json.JSONDecodeError) as e:
        # 若是 SSL 验证错误, 尝试 unverified fallback
        if _is_ssl_verify_error(e):
            try:
                raw = _do_request(None)  # None -> unverified
                print(
                    "[UpdateCheck] WARNING: SSL certificate verification failed, "
                    "retrying with unverified context. Consider installing certifi "
                    "or running 'Install Certificates.command'."
                )
                # 成功获取数据, 继续后续解析
                return _parse_response(raw, current, ssl_fallback_used=True)
            except Exception as fallback_err:
                # fallback 也失败, 报错给用户, 附上 SSL 修复提示
                return UpdateResult(
                    status=UpdateStatus.NETWORK_ERROR,
                    current_version=current,
                    error_message=f"{type(e).__name__}: {e}{_SSL_HINT}",
                )
        return _classify_exception(e, current)
    except Exception as e:
        # 其他未知异常
        if _is_ssl_verify_error(e):
            return UpdateResult(
                status=UpdateStatus.NETWORK_ERROR,
                current_version=current,
                error_message=f"{type(e).__name__}: {e}{_SSL_HINT}",
            )
        return UpdateResult(
            status=UpdateStatus.NETWORK_ERROR,
            current_version=current,
            error_message=f"{type(e).__name__}: {e}",
        )

    # 走到这里说明第一次请求成功
    return _parse_response(raw, current, ssl_fallback_used=False)


def _classify_exception(e: BaseException, current: str) -> UpdateResult:
    """将已知异常分类为合适的 UpdateResult"""
    if isinstance(e, HTTPError):
        if e.code == 404:
            return UpdateResult(
                status=UpdateStatus.NO_RELEASE,
                current_version=current,
            )
        return UpdateResult(
            status=UpdateStatus.NETWORK_ERROR,
            current_version=current,
            error_message=f"HTTP {e.code} {e.reason}",
        )
    if isinstance(e, (URLError, socket.timeout, TimeoutError)):
        return UpdateResult(
            status=UpdateStatus.NETWORK_ERROR,
            current_version=current,
            error_message=f"{type(e).__name__}: {e}",
        )
    if isinstance(e, json.JSONDecodeError):
        return UpdateResult(
            status=UpdateStatus.NETWORK_ERROR,
            current_version=current,
            error_message=f"Response parse failed: {e}",
        )
    # 兜底
    return UpdateResult(
        status=UpdateStatus.NETWORK_ERROR,
        current_version=current,
        error_message=f"{type(e).__name__}: {e}",
    )


def _parse_response(raw: bytes, current: str, ssl_fallback_used: bool) -> UpdateResult:
    """
    解析 GitHub API 响应 body, 返回 UpdateResult。
    ssl_fallback_used 仅用于日志, 不影响 result 内容。
    """
    if ssl_fallback_used:
        print("[UpdateCheck] (SSL fallback succeeded, response parsed below)")

    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        return UpdateResult(
            status=UpdateStatus.NETWORK_ERROR,
            current_version=current,
            error_message=f"Response parse failed: {e}",
        )

    # 解析 tag_name (如 "v2.3.0")
    tag = data.get("tag_name") or ""
    html_url = data.get("html_url") or GITHUB_RELEASES_PAGE
    if not tag:
        return UpdateResult(
            status=UpdateStatus.NO_RELEASE,
            current_version=current,
            release_url=html_url,
        )

    # 去掉 tag 前缀的 'v' 用于显示
    latest_display = tag.lstrip("vV")

    newer = is_newer(tag, current)
    if newer is True:
        return UpdateResult(
            status=UpdateStatus.NEW_VERSION,
            current_version=current,
            latest_version=latest_display,
            release_url=html_url,
        )
    elif newer is False:
        return UpdateResult(
            status=UpdateStatus.UP_TO_DATE,
            current_version=current,
            latest_version=latest_display,
        )
    else:
        # 版本号无法解析, 按 UP_TO_DATE 处理(保守不打扰用户)
        return UpdateResult(
            status=UpdateStatus.UP_TO_DATE,
            current_version=current,
            latest_version=latest_display,
        )


# ============================================================
# 异步执行包装(QRunnable + 信号)
# ============================================================

class UpdateCheckSignals(QObject):
    """更新检查工作线程的信号"""
    finished = pyqtSignal(object)  # 携带 UpdateResult
    error = pyqtSignal(str)        # 兜底错误信号(正常情况不会触发)


class UpdateCheckWorker(QRunnable):
    """
    异步执行 check_for_update() 的工作线程。

    用法:
        worker = UpdateCheckWorker()
        worker.signals.finished.connect(on_finished)
        QThreadPool.globalInstance().start(worker)
    """

    def __init__(self) -> None:
        super().__init__()
        self.signals = UpdateCheckSignals()

    def run(self) -> None:
        try:
            result = check_for_update()
            self.signals.finished.emit(result)
        except Exception as e:
            # check_for_update 内部已捕获所有异常, 此处仅作兜底
            self.signals.error.emit(str(e))
