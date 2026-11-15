# -*- coding: utf-8 -*-
"""全局快捷键：动作表与平台能力探测。

2026-11 macOS-only 收敛（6b-4）：Windows 系统级热键服务（``RegisterHotKey`` +
原生事件过滤器 + ``WM_HOTKEY`` 分发）整族移除——macOS 无此通路，该服务在
macOS 上本就从未生效。保留本模块的三个公开符号（设置页「互动 · 快捷键」行与
配置校验使用）；``is_supported()`` 恒 False，设置行呈禁用态加说明。
"""

from __future__ import annotations

#: 动作 → 配置键。键名与设置行的 ``key`` 同名（「已修改」标记与单项重置才会自动可比）。
ACTIONS: dict[str, str] = {
    "open_chat": "hotkey_open_chat",
    "look_screen": "hotkey_look_screen",
    "screen_capture": "hotkey_screen_capture",
}

#: 动作的中文名（日志/提示用）
ACTION_LABELS: dict[str, str] = {
    "open_chat": "AI 对话",
    "look_screen": "看看屏幕",
    "screen_capture": "截图提问",
}


def is_supported() -> bool:
    """当前平台能否注册系统级热键（macOS-only 构建恒 False）。"""
    return False
