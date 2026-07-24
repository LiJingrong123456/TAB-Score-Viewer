# -*- coding: utf-8 -*-
"""
tools/check_version.py
版本一致性校验工具

功能:
  - 解析 readme/功能更新.md 中形如 `## (YYYY-MM-DD) - … (vX.Y.Z)` 的版本标题
  - 取最高 (latest) 版本号
  - 与 VERSION 文件对比
  - 不一致时打印差异, --strict 模式下退出码非零 (CI 门禁)

Usage:
  python tools/check_version.py                  # 仅报告
  python tools/check_version.py --strict         # 不一致时退出码 1
  python tools/check_version.py --write-version  # 自动同步 VERSION (慎用)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = PROJECT_ROOT / "VERSION"
CHANGELOG_FILE = PROJECT_ROOT / "readme" / "功能更新.md"


# 匹配二级标题: ## (2026-07-24) - … (v2.6.0)
# 兼容: 标题在段首/段尾均可能
HEADING_RE = re.compile(
    r"^##\s+\([^)]+\)\s*[-—–]\s*.+?\(v(\d+)\.(\d+)\.(\d+)\)",
    re.MULTILINE,
)


def parse_changelog(path: Path) -> List[Tuple[int, int, int]]:
    """从功能更新.md 解析所有版本号, 返回 [(major, minor, patch), ...] (按出现顺序)"""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    versions: List[Tuple[int, int, int]] = []
    for m in HEADING_RE.finditer(text):
        major, minor, patch = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        versions.append((major, minor, patch))
    return versions


def version_to_str(v: Tuple[int, int, int]) -> str:
    return f"{v[0]}.{v[1]}.{v[2]}"


def read_version_file(path: Path) -> str:
    """读取 VERSION 文件, strip 空白"""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def write_version_file(path: Path, version_str: str) -> None:
    path.write_text(version_str + "\n", encoding="utf-8")


def color_red(s: str) -> str:
    return f"\033[31m{s}\033[0m" if sys.stdout.isatty() else s


def color_green(s: str) -> str:
    return f"\033[32m{s}\033[0m" if sys.stdout.isatty() else s


def color_yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m" if sys.stdout.isatty() else s


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验 readme/功能更新.md 中最新版本号与 VERSION 文件是否一致"
    )
    parser.add_argument(
        "--changelog", default=str(CHANGELOG_FILE),
        help=f"功能更新日志路径, 默认 {CHANGELOG_FILE}"
    )
    parser.add_argument(
        "--version-file", default=str(VERSION_FILE),
        help=f"VERSION 文件路径, 默认 {VERSION_FILE}"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="不一致时返回非零退出码 (CI 门禁用)"
    )
    parser.add_argument(
        "--write-version", action="store_true",
        help="不一致时, 用功能更新日志中的最高版本号覆盖 VERSION (慎用)"
    )
    args = parser.parse_args()

    changelog = Path(args.changelog)
    version_file = Path(args.version_file)

    # 1. 解析功能更新日志
    versions = parse_changelog(changelog)
    if not versions:
        print(color_red(f"[错误] 未能从 {changelog} 解析到任何版本号"), file=sys.stderr)
        return 2

    # 2. 取最高版本号 (按 tuple 自然排序, v2.5.3 < v2.6.0)
    latest = max(versions)
    latest_str = version_to_str(latest)
    print(f"功能更新日志最新版本: {latest_str}")
    print(f"  (共解析到 {len(versions)} 个版本号)")

    # 3. 读取 VERSION 文件
    current_str = read_version_file(version_file)
    if not current_str:
        print(color_yellow(f"[警告] VERSION 文件不存在或为空: {version_file}"))
    else:
        print(f"VERSION 文件当前值:   {current_str}")

    # 4. 对比
    if current_str == latest_str:
        print(color_green("\n[OK] 版本号一致"))
        return 0

    # 不一致
    print(color_yellow(f"\n[不一致] 功能更新日志: {latest_str}, VERSION: {current_str or '(空)'}"))

    if args.write_version:
        write_version_file(version_file, latest_str)
        print(color_green(f"[已写入] VERSION 文件更新为 {latest_str}"))
        return 0

    if args.strict:
        print(color_red("[STRICT] 退出码 1 (CI 门禁触发)"))
        print("[提示] 用 --write-version 自动同步, 或手动编辑 VERSION / 功能更新.md")
        return 1

    print("[提示] 加 --strict 可在不一致时返回非零退出码 (CI 用)")
    print("[提示] 加 --write-version 可自动用日志中的最高版本号覆盖 VERSION")
    return 0


if __name__ == "__main__":
    sys.exit(main())
