# macOS-only 改造 · 阶段变更记录（2026-11，分支 `OnlyMacos`）

> 活文档：按批次记录删除/收敛内容与验证数字；细节进度与未完成项见
> [`macos-only-conversion/HANDOFF.md`](macos-only-conversion/HANDOFF.md)，
> 踩坑对策见 [`LESSONS.md`](LESSONS.md)。

## 目标

把仓库从三平台收敛为 **macOS-only**（用户只在 macOS 运行）：删非 macOS 文件与
分支依赖、收敛打包/CI/文档，减小仓库与包体。唯一的平台硬门禁是
`pet/__main__.py` 顶部 darwin 检查；`proactive` 的 `win32` 判定是功能总门，保留。

## 批次清单

| 提交 | 批次 | 内容 | 验证 |
|---|---|---|---|
| `8ad8589` | 批量删除 | 92 删 + 8 改：build-windows/linux.yml、scripts/{build_linux,build_onedir.ps1,fcitx}、android/ 整树、tools/mem_probe.py、17 个 Win/Linux 测试；config/catalog/agent_link 收敛 macOS | py_compile 20 文件 |
| `847b21f` | 测试修复 | 首跑全量 3 failed 修复（lunar 表边界替身注入；ChatMemory.load 时钟同源）；删孤儿 test_mem_probe_census；ruff F401×2 | 全量 8620 passed（串行 12:08） |
| `2333d45` | 6a | winmm 音频族：删 sound_winmm.py(892)+test(1021)；click_sound 摘 11 处；conftest 打桩清理 | T2 8582 |
| `8eedeb2` | 6b-1 | WindowsPerPixelInputController 族（类 163 行 + window.py 链 + overlay_window 分支 + 3 个 win-only 测试） | T2 8571 |
| `d0ea8fd` | 6b-2 | 穿透样式族（click_through/no_activate/non_rude + 常量） | T2 8569 |
| `09480c7` | 6b-3 | 全屏探测族（probe 四函数/_set_windows_topmost/结构体）+ island 原生置顶分支；platform_win 只剩热键 | T2 8565 |
| `accec96` | 6b-4 | 热键服务整族摘除；**删除 pet/platform_win.py**；hotkeys.py 精简为动作表+`is_supported()=False` | T2 8557 |
| `0bcc30f` | 6d | 删 resources/presentmon/ + verify_presentmon.py；THIRD_PARTY_NOTICES §6 删并顺延 §7-9；game_fps 保留优雅降级 | T2 8557 |
| `5eb1a16` | 2a+2b | requirements 剪除 pywin32-ctypes/pycaw/winrt×5/linux 钉版；删 packaging/dsh-pet.iss | T2 8557 |
| `4acd5a8` | 2c | 删 android 工具脚本/测试 + notices §8 + .gitignore android 段 | T2 8541 |
| `a7aa55f` | 2d | pr-test.yml 收敛 macOS-only 单 job + push 触发 OnlyMacos；republish globs 收敛；删 ci_shards.py | T2 8500 + webm 族串行 41 |
| `463d39d` | 3 | README 768→588 行：删 Windows/Linux/Android/直播捕获/音乐路径/onefile 节 | T2 8541（含 README 守门测试） |
| `4ba6f36` | docs | HANDOFF 入库 + LESSONS 精简 + Work handoff 路径更新 | — |
| 本提交 | 4+5 | 删 docs/ANDROID.md；ONEDIR_PACKAGING 加历史警示；INDEX 登记（含已删除记录）；新增本文 | T2 8500 + webm 族串行 41 = 8541 |

## 验证口径

- **T1**（每批）：`ruff check pet/ tests/` + `pytest --collect-only -q` + 引用方焦点测试。
- **T2**（每批）：`pytest -q -n auto` 排除 webm 生命周期三文件（并行负载下 xdist worker 会原生崩溃，
  与 CI 记载同族），同三文件串行单跑；两者合计 = 全量口径（约 8500 + 41 例，~2 分钟）。
- **CI**：`pr-test.yml`（macOS-only，push/PR 自动触发）为独立环境兜底。

## 已知残留

- docstring/注释级提及（agent_link、settings_standalone、overlay_shell、sprite_sound、
  platform_passthrough、若干测试注释）：零行为，改到对应文件时顺手清理。
- 「顺手做清单」（不排期）：6e 散落死分支、6d-2 game_fps 整链、设置页快捷键页签、
  cleanup_mei_cache 工具——登记在 HANDOFF。
