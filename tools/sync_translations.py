# -*- coding: utf-8 -*-
"""
tools/sync_translations.py
i18n 三语同步校验工具

功能:
  - 以 locales/zh_CN.json 为 key 主源 (baseline)
  - 对比 en_US.json / ru_RU.json 中的翻译键
  - 输出缺失/多余键报告
  - --strict 模式下有任何差异退出码非零 (可作 CI 门禁)

Usage:
  python tools/sync_translations.py              # 仅报告
  python tools/sync_translations.py --strict     # 差异时退出码 1
  python tools/sync_translations.py --source en_US  # 指定其它语言为基线
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# 翻译文件目录 (与本脚本同级 ../locales)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = PROJECT_ROOT / "locales"
DEFAULT_SOURCE = "zh_CN"
DEFAULT_TARGETS = ["en_US", "ru_RU"]


def collect_keys(data: dict, prefix: str = "") -> List[str]:
    """递归收集嵌套 dict 中的所有点号分隔键, 跳过 _meta"""
    keys: List[str] = []
    for k, v in data.items():
        if k == "_meta":
            continue
        full_key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
        if isinstance(v, dict):
            keys.extend(collect_keys(v, full_key))
        else:
            keys.append(full_key)
    return keys


def load_locale(path: Path) -> Tuple[dict, List[str]]:
    """加载语言文件, 返回 (data, sorted_keys)"""
    if not path.exists():
        return {}, []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data, sorted(collect_keys(data))


def diff_keys(source: List[str], target: List[str]) -> Tuple[List[str], List[str]]:
    """对比 keys, 返回 (missing_in_target, extra_in_target)"""
    s = set(source)
    t = set(target)
    missing = sorted(s - t)  # 主源有, 目标没有
    extra = sorted(t - s)    # 目标有, 主源没有
    return missing, extra


def color_red(s: str) -> str:
    return f"\033[31m{s}\033[0m" if sys.stdout.isatty() else s


def color_green(s: str) -> str:
    return f"\033[32m{s}\033[0m" if sys.stdout.isatty() else s


def color_yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m" if sys.stdout.isatty() else s


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验 locales/ 下三语 JSON 的键是否对齐 (以 --source 为基线)"
    )
    parser.add_argument(
        "--source", default=DEFAULT_SOURCE,
        help=f"基线语言代码, 默认 {DEFAULT_SOURCE}"
    )
    parser.add_argument(
        "--targets", nargs="+", default=DEFAULT_TARGETS,
        help=f"目标语言代码列表, 默认 {' '.join(DEFAULT_TARGETS)}"
    )
    parser.add_argument(
        "--locales-dir", default=str(LOCALES_DIR),
        help=f"locales 目录路径, 默认 {LOCALES_DIR}"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="有任何差异时返回非零退出码 (CI 门禁用)"
    )
    args = parser.parse_args()

    locales_dir = Path(args.locales_dir)
    if not locales_dir.is_dir():
        print(color_red(f"[错误] locales 目录不存在: {locales_dir}"), file=sys.stderr)
        return 2

    source_path = locales_dir / f"{args.source}.json"
    print(f"基线语言: {args.source} ({source_path})")
    _, source_keys = load_locale(source_path)
    if not source_keys:
        print(color_red(f"[错误] 基线文件为空或不存在: {source_path}"), file=sys.stderr)
        return 2
    print(f"基线键数: {len(source_keys)}\n")

    total_problems = 0

    for target in args.targets:
        target_path = locales_dir / f"{target}.json"
        print(f"--- 目标语言: {target} ---")
        if not target_path.exists():
            print(color_red(f"  [缺失] {target_path}"), file=sys.stderr)
            total_problems += 1
            print()
            continue

        _, target_keys = load_locale(target_path)
        missing, extra = diff_keys(source_keys, target_keys)

        if not missing and not extra:
            print(color_green(f"  [通过] 键完全对齐 (共 {len(target_keys)} 个)"))
        else:
            if missing:
                print(color_yellow(f"  [缺失 {len(missing)} 个键] (主源有, 目标无):"))
                for k in missing:
                    print(f"    - {k}")
                total_problems += len(missing)
            if extra:
                print(color_yellow(f"  [多余 {len(extra)} 个键] (目标有, 主源无):"))
                for k in extra:
                    print(f"    - {k}")
                total_problems += len(extra)
        print()

    if total_problems == 0:
        print(color_green("[OK] 所有目标语言键与基线完全对齐"))
        return 0
    else:
        print(color_yellow(f"[总结] 共发现 {total_problems} 个差异"))
        if args.strict:
            print(color_red("[STRICT] 退出码 1 (CI 门禁触发)"))
            return 1
        print("[提示] 加 --strict 可使差异时返回非零退出码 (CI 用)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
