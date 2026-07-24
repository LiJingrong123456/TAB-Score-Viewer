# -*- coding: utf-8 -*-
"""
tests/test_i18n.py
i18n.py 单元测试:
  - I18n 单例
  - 加载语言文件
  - t(key) 点号分隔的嵌套访问
  - 缺失键回退到 zh_CN
  - 缺失键完全找不到时返回 key 本身
  - 切换语言
  - available_languages
  - format 占位符
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import i18n
from i18n import I18n


@pytest.fixture(autouse=True)
def reset_singleton():
    """每个测试前重置 I18n 单例状态, 避免污染"""
    I18n._instance = None
    I18n._translations = {}
    I18n._current_lang = ""
    yield
    I18n._instance = None
    I18n._translations = {}
    I18n._current_lang = ""


@pytest.fixture
def fake_locales_dir(tmp_dir: Path) -> Path:
    """创建临时 locales 目录, 写三个翻译文件"""
    d = tmp_dir / "locales"
    d.mkdir()
    (d / "zh_CN.json").write_text(json.dumps({
        "_meta": {"language": "zh_CN", "name": "简体中文"},
        "app": {"title": "应用"},
        "menu": {"file": "文件", "edit": "编辑"},
        "greet": "你好 {name}",
    }, ensure_ascii=False), encoding="utf-8")
    (d / "en_US.json").write_text(json.dumps({
        "_meta": {"language": "en_US", "name": "English"},
        "app": {"title": "App"},
        "menu": {"file": "File"},
        # "edit" 故意缺失, 测试回退
        "greet": "Hello {name}",
    }, ensure_ascii=False), encoding="utf-8")
    (d / "ru_RU.json").write_text(json.dumps({
        "_meta": {"language": "ru_RU", "name": "Русский"},
        "app": {"title": "Приложение"},
        "menu": {"file": "Файл", "edit": "Редактировать"},
    }, ensure_ascii=False), encoding="utf-8")
    return d


@pytest.fixture
def use_fake_locales(fake_locales_dir: Path, monkeypatch):
    """让 I18n 使用临时 locales 目录"""
    # I18n 在 __init__ 中通过 os.path.dirname(abspath(__file__)) 定位 locales
    # 通过 monkeypatch 替换 I18n._locales_dir
    def patched_init(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._locales_dir = str(fake_locales_dir)
        self._current_lang = "zh_CN"
        self._translations = {}
        self._load_language(self._current_lang)

    monkeypatch.setattr(I18n, "__init__", patched_init)


# ============================================================
# 单例
# ============================================================
class TestSingleton:
    def test_instance_returns_same(self, use_fake_locales):
        a = I18n()
        b = I18n()
        assert a is b

    def test_current_language_default(self, use_fake_locales):
        inst = I18n()
        assert inst.current_language() == "zh_CN"


# ============================================================
# t(key) 嵌套访问
# ============================================================
class TestTranslation:
    def test_simple_key(self, use_fake_locales):
        I18n.set_language("zh_CN")
        assert I18n.t("greet") == "你好 {name}"

    def test_nested_key(self, use_fake_locales):
        I18n.set_language("zh_CN")
        assert I18n.t("app.title") == "应用"
        assert I18n.t("menu.file") == "文件"
        assert I18n.t("menu.edit") == "编辑"

    def test_format_kwargs(self, use_fake_locales):
        I18n.set_language("zh_CN")
        assert I18n.t("greet", name="小明") == "你好 小明"

    def test_format_with_missing_kwargs_returns_raw(self, use_fake_locales):
        """format 失败时 (占位符无对应 kwarg) 应返回原始字符串, 不抛异常"""
        I18n.set_language("zh_CN")
        # 缺失 name kwarg, format 会抛 KeyError, 应被捕获
        result = I18n.t("greet")
        # 实现里捕获 KeyError/IndexError, 返回 value
        assert result == "你好 {name}"

    def test_fallback_to_zh_when_key_missing(self, use_fake_locales):
        """en_US 没有 menu.edit, 应回退到 zh_CN 的 "编辑" """
        I18n.set_language("en_US")
        assert I18n.t("menu.edit") == "编辑"

    def test_returns_key_when_completely_missing(self, use_fake_locales):
        """两个语言都没有这个 key, 返回 key 本身 (约定)"""
        I18n.set_language("en_US")
        result = I18n.t("nonexistent.deeply.nested.key")
        assert result == "nonexistent.deeply.nested.key"

    def test_partial_nested_key_missing(self, use_fake_locales):
        """如 'app.subtitle' 中 subtitle 缺失"""
        I18n.set_language("zh_CN")
        result = I18n.t("app.subtitle")
        assert result == "app.subtitle"

    def test_dotted_key_with_non_dict_intermediate(self, use_fake_locales):
        """如 'app.title.foo', app.title 是字符串而非 dict"""
        I18n.set_language("zh_CN")
        result = I18n.t("app.title.foo")
        assert result == "app.title.foo"

    def test_empty_key(self, use_fake_locales):
        I18n.set_language("zh_CN")
        # 空 key: 拆分后空 parts 链, value=instance._translations (dict)
        # 走 fallback, fallback 也找不到, 返回空字符串本身
        result = I18n.t("")
        assert result == ""


# ============================================================
# 切换语言
# ============================================================
class TestSetLanguage:
    def test_switch_to_english(self, use_fake_locales):
        I18n.set_language("en_US")
        assert I18n.current_language() == "en_US"
        assert I18n.t("menu.file") == "File"

    def test_switch_to_russian(self, use_fake_locales):
        I18n.set_language("ru_RU")
        assert I18n.current_language() == "ru_RU"
        assert I18n.t("menu.file") == "Файл"

    def test_set_same_language_noop(self, use_fake_locales):
        I18n.set_language("zh_CN")
        before = I18n._translations.copy()
        result = I18n.set_language("zh_CN")
        assert result is True
        # 状态应保持一致
        assert I18n.current_language() == "zh_CN"

    def test_set_unknown_language(self, use_fake_locales):
        """不存在的语言文件 → 返回 False, 不切换"""
        I18n.set_language("zh_CN")
        result = I18n.set_language("xx_XX")
        assert result is False
        assert I18n.current_language() == "zh_CN"

    def test_after_switch_missing_key_falls_back_to_zh(self, use_fake_locales):
        """切换到 en_US 后, 缺失键应回退到 zh_CN"""
        I18n.set_language("en_US")
        # en_US 没有 menu.edit, zh_CN 有
        assert I18n.t("menu.edit") == "编辑"


# ============================================================
# available_languages
# ============================================================
class TestAvailableLanguages:
    def test_lists_three(self, use_fake_locales):
        langs = I18n.available_languages()
        codes = [c for c, _ in langs]
        assert "zh_CN" in codes
        assert "en_US" in codes
        assert "ru_RU" in codes

    def test_includes_display_name(self, use_fake_locales):
        langs = I18n.available_languages()
        d = dict(langs)
        assert d.get("zh_CN") == "简体中文"
        assert d.get("en_US") == "English"
        assert d.get("ru_RU") == "Русский"


# ============================================================
# _load_language 容错
# ============================================================
class TestLoadLanguageErrors:
    def test_corrupt_json_returns_false(self, tmp_dir: Path, monkeypatch):
        """损坏的 JSON 文件应返回 False, 不抛异常"""
        d = tmp_dir / "locales"
        d.mkdir()
        (d / "zh_CN.json").write_text("{not valid json", encoding="utf-8")

        def patched_init(self):
            if getattr(self, "_initialized", False):
                return
            self._initialized = True
            self._locales_dir = str(d)
            self._current_lang = "zh_CN"
            self._translations = {}
            self._load_language(self._current_lang)

        monkeypatch.setattr(I18n, "__init__", patched_init)
        inst = I18n()
        # _load_language 失败时 _translations 保持 {}
        assert inst._translations == {}

    def test_missing_file_returns_false(self, tmp_dir: Path, monkeypatch):
        """语言文件不存在时, _load_language 返回 False"""
        d = tmp_dir / "locales"
        d.mkdir()
        # 不写任何 json

        def patched_init(self):
            if getattr(self, "_initialized", False):
                return
            self._initialized = True
            self._locales_dir = str(d)
            self._current_lang = "zh_CN"
            self._translations = {}
            ok = self._load_language("zh_CN")
            assert ok is False
            ok = self._load_language("en_US")
            assert ok is False

        monkeypatch.setattr(I18n, "__init__", patched_init)
        I18n()  # 触发
