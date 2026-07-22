# -*- coding: utf-8 -*-
"""
TAB Score Viewer - Internationalization Module

国际化翻译管理器（单例模式）
"""

import os
import json
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal


class I18n:
    """
    国际化翻译管理器（单例模式）

    功能:
      1. 从 locales/ 目录加载JSON翻译文件
      2. 提供 t(key, **kwargs) 方法获取翻译文本
      3. 支持运行时语言切换
      4. 缺失翻译自动回退到中文(zh_CN)
    """

    _instance = None
    _translations: dict = {}
    _current_lang: str = ""
    _locales_dir: str = ""

    # 语言切换信号 - 延迟初始化（需在QApplication之后）
    language_changed = None  # 类型: pyqtSignal(str)

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 翻译文件目录: 与本文件同级的 locales/ 文件夹
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._locales_dir = os.path.join(base_dir, "locales")

        # 默认使用中文
        self._current_lang = "zh_CN"
        self._translations = {}

        # 延迟创建信号（必须在QApplication创建后才能创建pyqtSignal）
        # 在第一次调用 t() / set_language() 时会检查并创建

        # 加载默认语言翻译
        self._load_language(self._current_lang)

    def _ensure_signal(self):
        """延迟创建language_changed信号"""
        if I18n.language_changed is None:
            try:
                I18n.language_changed = pyqtSignal(str)
                # 把信号绑定到当前实例
                self.language_changed = pyqtSignal(str)
            except Exception:
                pass
        if not hasattr(self, 'language_changed') or self.language_changed is None:
            try:
                self.language_changed = pyqtSignal(str)
            except Exception:
                pass

    @classmethod
    def t(cls, key: str, **kwargs) -> str:
        """
        获取翻译文本

        参数:
            key: 翻译键名，支持点号分隔的嵌套访问
            **kwargs: 占位符参数

        返回:
            翻译后的文本字符串
        """
        instance = cls()
        instance._ensure_signal()

        # 按点号分割key，逐级查找嵌套字典
        value = instance._translations
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                fallback = instance._get_fallback(key)
                if fallback is not None:
                    value = fallback
                else:
                    print(f"[I18n] 缺失翻译 key='{key}' (lang={instance._current_lang})")
                    return key

        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, IndexError) as e:
                print(f"[I18n] 格式化失败 key='{key}', error={e}")
                return value

        return value if isinstance(value, str) else str(value)

    @classmethod
    def set_language(cls, lang_code: str) -> bool:
        """
        切换当前语言

        参数:
            lang_code: 目标语言代码，如 "zh_CN", "en_US", "ru_RU"
        """
        instance = cls()
        instance._ensure_signal()
        if lang_code == instance._current_lang:
            return True

        success = instance._load_language(lang_code)
        if success:
            old_lang = instance._current_lang
            instance._current_lang = lang_code
            print(f"[I18n] 语言已切换: {old_lang} → {lang_code}")

            if hasattr(instance, 'language_changed') and instance.language_changed is not None:
                try:
                    instance.language_changed.emit(lang_code)
                except Exception:
                    pass
            return True
        else:
            print(f"[I18n] 语言文件不存在: {lang_code}.json")
            return False

    @classmethod
    def current_language(cls) -> str:
        """获取当前语言代码"""
        return cls()._current_lang

    @classmethod
    def available_languages(cls) -> list:
        """获取所有可用语言列表 [(code, name), ...]"""
        instance = cls()
        languages = []
        if os.path.isdir(instance._locales_dir):
            for fname in sorted(os.listdir(instance._locales_dir)):
                if fname.endswith('.json'):
                    code = fname[:-5]
                    fpath = os.path.join(instance._locales_dir, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            meta = json.load(f).get('_meta', {})
                            name = meta.get('name', code)
                            languages.append((code, name))
                    except Exception:
                        languages.append((code, code))
        return languages

    def _load_language(self, lang_code: str) -> bool:
        """加载指定语言的翻译文件"""
        filepath = os.path.join(self._locales_dir, f"{lang_code}.json")
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self._translations = json.load(f)
            self._translations.pop('_meta', None)
            return True
        except Exception as e:
            print(f"[I18n] 加载语言文件失败 '{filepath}': {e}")
            return False

    def _get_fallback(self, key: str):
        """回退到中文(zh_CN)查找翻译"""
        if self._current_lang == "zh_CN":
            return None
        filepath = os.path.join(self._locales_dir, "zh_CN.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                zh_data = json.load(f)
            zh_data.pop('_meta', None)
            value = zh_data
            for part in key.split('.'):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        except Exception:
            return None
