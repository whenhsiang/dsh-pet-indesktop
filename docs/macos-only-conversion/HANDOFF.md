# HANDOFF: macOS-only 改造（进度/恢复）

> 与 `docs/LESSONS.md`（教训）配套。本文件只记状态与决策，不记流水账。

## 事实
- 仓库：单远程 origin（自己的仓库，无 upstream）；`main` 只读=上游 `34d810b`。
- 分支 `OnlyMacos`（跟踪 origin/OnlyMacos），线性每批一提交：
  `34d810b → 8ad8589 批量删除 → 847b21f 全量修复 → 2333d45 6a → 8eedeb2 6b-1+docs → …`
- 目标：macOS-only（删非 macOS 文件/分支、减包体）。用户只在 macOS 运行。

## 已锁定决策（勿重开）
1. 唯一硬门禁：`pet/__main__.py` 顶部 darwin 检查；全仓仅此一处平台退出。
2. 改造轮保留死分支不混删；删死代码只走专门批次（6b-6e）、逐族进行。
3. `proactive/__init__.py` 仅恢复 docstring 原文（代码仍是 win32 守卫）。

## 进度
- ✅ `8ad8589`：92 删 + 8 改（workflows/scripts/android/tools.mem_probe/17 测试；
  config/catalog/agent_link 收敛 macOS-only；3 个测试手术仅读 build_macos.sh）。
- ✅ `847b21f`：首跑全量 3 failed 修复——balance×2（lunar 表边界用替身注入）、
  memory×1（load 时钟同源 self._clock），删孤儿 test_mem_probe_census，ruff F401×2。
- ✅ `2333d45`（6a）：winmm 族摘除（sound_winmm 892 + test_winmm_sound 1021 行删；
  click_sound 11 处；conftest 2 打桩；4 测试漏斗断言）。全量 8582 passed。
- ✅ `8eedeb2`（6b-1 + docs）：WindowsPerPixelInputController 族（类 163 行、
  window.py 链 6 处、overlay_window win32 分支、3 个 win-only 测试）+
  LESSONS/AGENTS/INDEX 入口。T2 8571 passed。

- ✅ **6b-4 + 6b 系列收尾**（本批）：热键服务整族摘除——`pet/hotkeys.py` 精简为
  ACTIONS/ACTION_LABELS/`is_supported()`（恒 False，设置页禁用态不变）；app.py 删
  `_install/_apply_global_hotkeys`、4 个回调、两处 uninstall、`_VISION_HOTKEY_ACTIONS`；
  **`pet/platform_win.py` 整体删除**（最后一个 import 消失）。测试：删 6 个服务类用例 +
  2 个 vision 热键门控用例。T2 8557 passed。

- ✅ **6c（结论：不删）**：proactive 的 `sys.platform == "win32"` 是**功能总门**
  而非死分支——`vision.foreground_window_info()` 非 Windows 恒返回 None（HWND
  抓屏架构），删门只会得到一个永远空转的定时器。按锁定决策 2 保留，这是除
  `__main__.py` darwin 门禁外唯一有功能意义的平台判断。
- ✅ **6d**：`resources/presentmon/`（exe 980KB + LICENSE）与 `scripts/verify_presentmon.py`
  删除；THIRD_PARTY_NOTICES 删 §6 并把 §7-9 顺延为 §6-8（文件内交叉引用无 §6+ 依赖）；
  .gitignore 的 presentmon 说明段清理、rapidocr 节号同步。game_fps 模块保留
  （缺二进制/非 Windows 时按「不支持」优雅降级；macOS 构建本就不含该目录）。
  T2 8557 passed。

## 未完成（每批：T1 + T2 + ruff，绿→commit→push）
- **6d-2（待定，功能级）**：game_fps / fps_monitor / fps_permission 链路是否整链移除——
  涉及灵动岛「游戏帧率」段的 UI 与状态机，属功能删减需用户拍板；当前保留优雅降级。
- **6e** 散落死分支（window.py、webm_clip、
  session_watcher、config_write_lock、chat/session_store、harness_launcher、
  frameseq_provision、updater、tts/doubao）+ test_architecture 删除守卫。
- **2a** requirements 剪除（pywin32-ctypes/pycaw/winrt×5/linux 钉版）；
  **2b** `packaging/dsh-pet.iss`；**2c** android 脚本 + 2 测试 + .gitignore 段；
  **2d** `pr-test.yml` 收敛（矩阵 macOS-only、shard 去已删文件、push 分支加
  OnlyMacos）；**3** README；**4** docs/INDEX 处理；**5** CHANGELOG。
- 可选 UX 批次：设置页「互动 · 快捷键」页签在 macOS-only 下永久禁用（`is_supported()`
  恒 False）——整页签是否移除待定（涉及 settings_interaction/搜索别名/文案 lint 多处）。
- 待办池：空（bug/功能按「用户可感知 bug 优先」，登记类型/现象/期望/批次）。

## 验证协议
- **T1 快门**（每批，~2 分钟）：`ruff check pet/ tests/` + `pytest --collect-only -q`
  + 引用方焦点测试。
- **T2 全量并行**（默认，~1:50）：`.venv/bin/python -m pytest -q -n auto`，env：
  `QT_QPA_PLATFORM=offscreen PYTHONUTF8=1 PYTHONIOENCODING=utf-8
  PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring`。
- **T3 串行全量**（~12 分钟）：仅合并前、或触及 config/生命周期/线程/平台语义。
- 全量期间禁改 .py（见 LESSONS）。

## 测试环境
- uv（`~/Library/Python/3.9/bin/uv`）+ CPython 3.13.18 + `.venv/`（gitignore）。
- 整体删除：`rm -rf .venv .pytest_cache` + `python3 -m pip uninstall -y uv` +
  `rm -rf ~/.local/share/uv/python ~/Library/Caches/uv`（勿用 git clean -fdX）。

## Git 约定
- 每批一提交带批号（`refactor(macos-only): [6b-2] …`）；T2 绿→commit→
  `git push origin OnlyMacos`（远程即备份）。
- main 只读；会话开局 `git fetch origin && git status -sb`；上游动了
  `git rebase origin/main`（线性，不 merge main 进来）。
- 合并：全部批次完 → main `--ff-only` 或走 PR（pr-test 把关）。
- 全局配置（一次性）：fetch.prune / pull.rebase / rebase.autoStash / rerere /
  conflictstyle=zdiff3 / diff.algorithm=histogram / push.autoSetupRemote。

## 已知残留（docstring/注释级，零行为，勿当缺陷）
- agent_link:3196、settings_standalone:10、overlay_shell:3981/5007、sprite_sound×4、
  bridge:612、platform_passthrough×3、application_icon:14、若干测试注释。
- test_island_topmost 模块 docstring 仍提及 `platform_win._set_windows_topmost`（文字级）。
- 有意的损失：8 个打包守卫测试（含 macOS 变体断言）随删；
  `scripts/check_frameseq_bundle.py` 本体仍在并被 build_macos.sh 调用。

## 恢复动作
```bash
cd /Users/wesley/projects/dshpet/dsh-pet-indesktop
git status -sb                # 干净 + 本地=origin 为常态
head -30 docs/LESSONS.md      # 教训速读
.venv/bin/python --version    # 3.13.18（无 .venv 则按「测试环境」重建）
# T2 全量：见「验证协议」命令
```
