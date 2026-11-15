# -*- coding: utf-8 -*-
"""全局快捷键：文本口径（``hotkey_spec``）与服务（``hotkeys``）的回归。

**不碰真实系统**：``user32`` 是注入的替身（内部维护"已占用组合"表），原生消息
由手工构造的 ``MSG`` 喂进 ``nativeEventFilter``，所以这些用例在 CI 的三个平台上
都能跑（非 Windows 走 ``supported=False`` 那条路）。
"""
from __future__ import annotations

import ctypes
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from pet import hotkey_spec as spec
from pet import hotkeys


@pytest.fixture
def qapp_():
    app = QApplication.instance() or QApplication([])
    return app


# ---------------------------------------------------------------- 文本口径
@pytest.mark.parametrize("text,expected", [
    ("Ctrl+Alt+P", (spec.MOD_CONTROL | spec.MOD_ALT, 0x50)),
    ("ctrl+shift+f9", (spec.MOD_CONTROL | spec.MOD_SHIFT, 0x78)),
    ("Alt+Space", (spec.MOD_ALT, 0x20)),
    ("Win+F1", (spec.MOD_WIN, 0x70)),
    (" Meta + num5 ", (spec.MOD_WIN, 0x65)),
])
def test_parse_accepts_common_combinations(text, expected):
    assert spec.parse(text) == expected


@pytest.mark.parametrize("text", [
    "P",            # 没有修饰键：会抢走整个系统的普通打字
    "Ctrl",         # 只有修饰键
    "Ctrl+P+Q",     # 两个普通键
    "Ctrl+",        # 残缺
    "Ctrl+Alt+😂",   # 白名单外
    "",
    None,
])
def test_parse_rejects_unsafe_or_incomplete(text):
    assert spec.parse(text) is None


def test_normalize_fixes_order_case_and_garbage():
    assert spec.normalize("alt+ctrl+p") == "Ctrl+Alt+P"
    assert spec.normalize("SHIFT+WIN+F24") == "Shift+Win+F24"
    assert spec.normalize("garbage") == ""
    assert spec.display("") == "未设置"
    # 反向：注册位（含 MOD_NOREPEAT）能解回规范写法
    assert spec.from_win32(spec.MOD_CONTROL | spec.MOD_NOREPEAT, 0x50) == "Ctrl+P"


# ---------------------------------------------------------------- 设置页接线
def test_chord_to_text_requires_a_modifier_and_known_key():
    """录入控件只收「修饰键 + 白名单按键」，其余返回空串（= 不绑）。"""
    from PySide6.QtGui import QKeySequence

    from pet import settings_hotkeys

    assert settings_hotkeys.chord_to_text(QKeySequence("Ctrl+Alt+P")) == "Ctrl+Alt+P"
    assert settings_hotkeys.chord_to_text(QKeySequence("Alt+F9")) == "Alt+F9"
    assert settings_hotkeys.chord_to_text(QKeySequence("P")) == "", "无修饰键会抢走打字"
    assert settings_hotkeys.chord_to_text(QKeySequence()) == ""


def test_hotkey_rows_exist_and_save_round_trips(tmp_path, monkeypatch):
    """「互动 · 快捷键」三行确实在页里，保存能把录入值写进配置。"""
    from PySide6.QtWidgets import QApplication

    from pet.config import Config
    from pet.modern_settings_dialog import ModernSettingsDialog
    from pet import hotkey_spec as spec

    qapp = QApplication.instance() or QApplication([])
    config = Config(base=tmp_path)
    dialog = ModernSettingsDialog(config, include_ai=False)
    try:
        for action in hotkeys.ACTIONS:
            assert dialog.findChild(object, f"hotkeyEdit_{action}") is not None
            assert dialog.findChild(object, f"hotkeyClear_{action}") is not None

        dialog._hotkey_values = {"open_chat": "Ctrl+Alt+P",
                                 "look_screen": "", "screen_capture": ""}
        from pet import settings_hotkeys

        settings_hotkeys.save_hotkey_settings(dialog)
        # 设置页用的是 SlotRoutedConfig（全局键最终落主 config.json）
        assert dialog.config.get("hotkey_open_chat") == "Ctrl+Alt+P"
        assert dialog.config.get("hotkey_look_screen") == ""
        dialog.config.save()
        assert Config(base=tmp_path).get("hotkey_open_chat") == "Ctrl+Alt+P", "要真落盘"

        dialog._hotkey_values = {"open_chat": "nonsense"}
        settings_hotkeys.save_hotkey_settings(dialog)
        assert dialog.config.get("hotkey_open_chat") == "", "脏值不许写进配置"
    finally:
        dialog.deleteLater()
        qapp.processEvents()


# ---------------------------------------------------------------- 审查补的边界
@pytest.mark.parametrize("text", ["Ctrl+ß", "Ctrl+é", "Ctrl+²", "Ctrl+中"])
def test_parse_never_raises_on_non_ascii_single_characters(text):
    """非 ASCII 单字符：``"ß".isalpha()`` 为真但 `"ß".upper() == "SS"`，`ord("SS")` 会抛
    TypeError——那异常发生在 ``Config.__init__`` 的归一化里，一条手改配置就能让主程序
    和设置页都起不来。这里断言"绝不抛、且判为不支持"。"""
    assert spec.parse(text) is None
    assert spec.normalize(text) == ""


def test_config_survives_a_unicode_hotkey_value(tmp_path):
    """手写一个非法热键进配置文件，Config 必须能构造出来并清空它。"""
    from pet.config import Config

    payload = tmp_path / "config.json"
    payload.write_text('{"hotkey_open_chat": "Ctrl+ß"}', encoding="utf-8")
    config = Config(base=tmp_path)  # 不许抛
    assert config.get("hotkey_open_chat") == ""


@pytest.mark.parametrize("text", ["Ctrl+Alt+P", "Win+F1", "Ctrl+num5",
                                  "Ctrl+PrintScreen", "Ctrl+PageUp", "Alt+Space"])
def test_our_notation_round_trips_through_the_edit_widget(text):
    """录入框回显必须走 ``(mods, vk)`` 反构造，不能 ``QKeySequence(text)``。

    后者对我们自己的写法（``Win`` / ``num5``）实测解析成空序列——控件显示"未设置"
    而配置里明明有值。这里断言"文本 → 序列 → 文本"回到同一个规范写法。
    """
    from PySide6.QtWidgets import QApplication

    from pet import settings_hotkeys

    qapp = QApplication.instance() or QApplication([])
    sequence = settings_hotkeys.text_to_sequence(text)
    assert not sequence.isEmpty(), f"{text} 必须能回显到录入框"
    assert settings_hotkeys.chord_to_text(sequence) == text
    # 小键盘数字要用小键盘的虚拟键码，不能悄悄变成主键盘数字
    if "num" in text:
        assert spec.parse(settings_hotkeys.chord_to_text(sequence))[1] >= 0x60
    del qapp


@pytest.mark.parametrize("text", [
    "Ctrl+ı", "Ctrl+ſ", "Ctrl+CapsLocK", "Ctrl+NumLocK", "Ctrl+BacKspace",
    "Ctrl+Ａ", "Ctrl+中",
])
def test_unicode_variants_never_register_another_ascii_key(text):
    """非 ASCII 变体一律不支持——包括「小写化后变成 ASCII」的那些。

    - ``"ı".upper() == "I"``、``"ſ".upper() == "S"``（单字符分支）
    - ``"K".lower() == "k"``：``"CapsLocK"`` 小写化后是纯 ASCII，会命中 CapsLock
      （多字符分支）
    两条分支都必须看**原始串**是不是 ASCII，否则这些字符会静默绑到别的键上。
    """
    assert spec.parse(text) is None, f"{text} 不许被当成合法热键"
    assert spec.normalize(text) == ""


@pytest.mark.parametrize("text", ["Ctrl+num*", "Ctrl+numplus", "Ctrl+num-",
                                  "Ctrl+num.", "Ctrl+num/", "Ctrl+num5",
                                  "Ctrl+CapsLock", "Ctrl+NumLock", "Ctrl+ScrollLock"])
def test_numpad_and_lock_keys_round_trip(text):
    """小键盘运算符与三个锁键：录入 → 保存 → 回显必须闭环。

    这些键在 Win32 侧是独立虚拟键码，在 Qt 侧是"普通键 + KeypadModifier"；任一方向
    漏映射都会变成"绑上了但框里显示空"。
    """
    from PySide6.QtWidgets import QApplication

    from pet import settings_hotkeys

    qapp = QApplication.instance() or QApplication([])
    sequence = settings_hotkeys.text_to_sequence(text)
    assert not sequence.isEmpty(), f"{text} 必须能回显"
    assert settings_hotkeys.chord_to_text(sequence) == text


def test_legacy_num_plus_spelling_still_parses():
    """旧写法 ``Ctrl+num+``（与分隔符冲突）在入口归一化后仍能解析。"""
    assert spec.parse("Ctrl+num+") == (spec.MOD_CONTROL, 0x6B)
    assert spec.normalize("ctrl+NUM+") == "Ctrl+numplus"
