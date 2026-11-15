# -*- coding: utf-8 -*-
"""
Win32 平台层 —— 从 pet/window.py 剥离（结构优化批 6-3）。

纯搬移：逐行搬移不改逻辑；ctypes 调用约定、argtypes 声明与搬移前逐字符一致。
这些是直接触碰原生 API 的代码，任何一处改动都可能造成真实崩溃。

2026-11 macOS-only 收敛：全屏探测 / 置顶 / 穿透样式族已删；本文件仅剩热键
原语，下批（6b-4）随热键族移除而整体删除。
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes


def _register_windows_hotkey(hotkey_id: int, modifiers: int, vk: int,
                             hwnd: int = 0, user32=None) -> bool:
    """注册一个**系统级**热键：``RegisterHotKey(hwnd, id, modifiers, vk)``。

    ``hwnd=0`` 表示绑到本线程的消息队列——本进程的 Qt 消息循环会把它转成
    ``WM_HOTKEY`` 送给原生事件过滤器（见 ``pet/hotkeys.py``）。

    为什么必须走 Win32：桌宠的合成窗是「不接受焦点」的置顶窗，Qt 的
    ``QShortcut``/``QKeySequence`` 只在窗口有焦点时有效，对桌宠等于永远不触发。
    返回 API 是否成功：``False`` 绝大多数情况是**这个组合已被别的程序占用**
    （Windows 的全局热键表是独占的），要如实报给用户，不能静默。

    ``user32=None`` 时取真实 user32 并声明 argtypes——口径同
    :func:`_set_windows_topmost`（64 位下 HWND 不声明会被截断）。
    """
    if user32 is None:
        user32 = ctypes.windll.user32
        user32.RegisterHotKey.argtypes = [
            wintypes.HWND, ctypes.c_int, ctypes.c_uint, ctypes.c_uint,
        ]
        user32.RegisterHotKey.restype = wintypes.BOOL
    return bool(user32.RegisterHotKey(hwnd, int(hotkey_id), int(modifiers), int(vk)))


def _unregister_windows_hotkey(hotkey_id: int, hwnd: int = 0, user32=None) -> bool:
    """注销热键：``UnregisterHotKey(hwnd, id)``（幂等，未注册时返回 False）。"""
    if user32 is None:
        user32 = ctypes.windll.user32
        user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.UnregisterHotKey.restype = wintypes.BOOL
    return bool(user32.UnregisterHotKey(hwnd, int(hotkey_id)))
