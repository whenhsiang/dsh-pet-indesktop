# HANDOFF: macOS-only 改造（进度/恢复）

> 与 `docs/LESSONS.md`（教训）配套。本文件只记状态与决策，不记流水账。

## 交接速查（2026-11-21 收尾：**新会话先读这一节**）

**分支 / 工作区**（`git status -sb` 实测）
- 分支 `OnlyMacos`，本地与 `origin/OnlyMacos` 一致（`git status -sb` 无 ahead/behind）；
  远程 `origin` = `https://github.com/whenhsiang/dsh-pet-indesktop.git`（无 upstream remote）。
  推送会触发 `pr-test.yml`（push 到 main/OnlyMacos 都跑）；`build-macos`/`republish-assets` 仅手动触发，
  所以 push 不会出包、不会发版。
- 本批改动**已提交**（`git log -1` 即本批：`fix(overlay): macOS 首建窗 20pt 收窄 + 边缘探头点击脱困/拖拽 rebase`）；
  收尾后 `git status -sb` 应为干净。`main` 只读（= 上游 `34d810b`）。
- 提交内容：9 个文件（4 个产品文件 + 3 个测试 + 2 个文档），详见下一段。

**本批改了什么**（全部已验证，细节见文末「2026-11-21 收口」）
- `pet/overlay_window.py`：show 后补 `setGeometry`（0/60ms）+ `resizeEvent` 兜底（macOS 首建窗收窄 20pt）；
  `paintEvent` 闸门改 `paint_bounds()`。
- `pet/sprite_edge_probe.py`：点击 = `cancel("click_out")` 且不消费点击；`EDGE_IDLE_SECONDS` 后自动缩回；
  删 `STRAIGHTEN*/RETURNING` 死状态；不可见 sprite 不参与探头；新增姿态/稳态取证日志。
- `pet/pet_sprite.py`：`rebase_drag_offset()`（拖拽跟手）+ `visible_local_rect()`（alpha 外接框）。
- `pet/overlay_shell.py`：拖拽升级只在"探头取消真的挪了位置"时 rebase（事件 `globalPos`，不用 `QCursor`）；
  `[overlay 几何]` 日志。
- `tests/*`：新增 4 条回归（点击脱困/重进推后、拖拽 rebase、重绘闸门、不可见 sprite）。
- `docs/LESSONS.md`：2026-11-21 共 7 条。

**验收 / 复现**（源码跑；`/Applications/DshPet.app` 是 10-22 旧构建，不含本批）
1. `cd /Users/wesley/projects/dshpet/dsh-pet-indesktop && .venv/bin/python -m pet`
   （先退出正在跑的实例：单实例门；源码跑用 `dsh-pet-standalone` 配置，需在设置里打开「边缘探头」）
2. 贴右边缘 → 停 2s（45° 探头，右缘应"被屏幕裁掉"而非留白）；
   点一下 → 整只回屏内 + 有点击动画/音效；不动 5s → 自动缩回探头；左边缘同样。
3. 贴底/「回到右下角」的脚不应被切（同一个 20pt 问题）。

**取证入口**
- 日志：`~/Library/Application Support/dsh-pet-standalone/pet-<PID>.log`
  （打包 webm-chat 变体在 `dsh-pet-standalone-webm-chat/`；INFO 级、1MB×2 滚动、启动清 >7 天）。
- 关键行：`[overlay 几何] …`、`overlay: show 后重设窗口矩形 …`、`[边缘探头] 稳态/点击脱困 …`;
  `左/右缘差` **正 = 留白（缝）**，**负 = 越出屏外（正常）**。
- 原生窗口矩形（Qt 的 `geometry()` 会说谎）：ctypes + `CGWindowListCopyWindowInfo` 过滤 `kCGWindowOwnerPID`，
  读 `kCGWindowBounds` 的 X/Y/Width/Height；本机正常值必须是 `(0, 33, 1470, 923)`。

**验证命令**
- T1：`ruff check pet/ tests/` + `pytest --collect-only -q` + 焦点用例。
- T3（串行全量，本轮 11:45 / 8506 passed）：见下方「验证协议」的 T2 命令但去掉 `-n auto`、加 `-p no:randomly`；
  三个 webm 生命周期文件单独串行跑（41 passed）。

**未决隐患**：见文末「2026-11-21 收口」的 5 条（legacy 探头语义、20pt 对其他浮动窗、1px 口径差、
`active` 口径、`body_box` 不做镜像归一化）。

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

- ✅ **2a+2b**（本批）：requirements.txt 剪除 Windows/Linux 专属（pywin32-ctypes /
  pycaw / winrt-*×5 / PySide6 linux 钉版），收敛为单条 `PySide6>=6.5`；删
  `packaging/dsh-pet.iss`（Windows 安装器）。测试守卫确认：平台不可导入的模块在
  test_runtime_dependencies 里跳过，psutil 有 net_monitor/sys_monitor 等跨平台消费者故保留。
  T2 8557 passed。

- ✅ **2c**（本批）：android 工具尾巴删除——`scripts/build_android.ps1`、`setup_android.ps1`、
  `export_android_assets.py`、`android_acceptance.py` + 两个对应测试；`.gitignore`
  的 android/keystore 段清理；`THIRD_PARTY_NOTICES` 删 §8（Android 第三方声明）
  与导言的 Android 两句。T2 8541 passed（−16 与删除测试对账一致）。

- ✅ **2d**（本批）：`pr-test.yml` 收敛——删三平台矩阵（单 macos-latest + Python 3.13）、
  Windows 分片步骤、Linux tee-sys/前缀诊断步骤；push 分支加 OnlyMacos（此后推送
  即跑 CI）；保留 bridge 零依赖门/webm/frameseq 隔离步骤/崩溃面包屑。
  `republish-assets.yml` 默认 globs 收敛为 macOS 资产；删 `scripts/ci_shards.py`。
  YAML 校验通过。T2 8500 + webm 族串行 41 = 8541 passed，0 failed。

- ✅ **3**（本批）：README 768→~580 行收敛为 macOS-only——删 Windows 安装/绿色版、
  Linux 节、Android 段、onefile 清理节、主动识屏节、音乐播放器路径节、直播捕获节；
  下载表/数据目录/角色扫描表/已知限制/反馈/开发者命令同步改写。守门测试要求快捷键
  小节保留「默认全空/修饰键/只有 Windows/三动作点名」——已按「本构建不注册」口径重写。
  T2 8500 + webm 族串行 41 = 8541 passed。

- ✅ **4+5**（本批，主线收尾）：删 `docs/ANDROID.md`（android 整树已删）；
  `ONEDIR_PACKAGING.md` 顶部加历史警示（Windows 时期流水线，构建门设计保留）；
  INDEX 删 ANDROID 行、THIRD_PARTY 行去 APK 措辞、ONEDIR 行加基线警示、新增
  「已删除（macOS-only 收敛）」小节；新增 `docs/CHANGELOG-MACOS-ONLY.md`（批次清单
  + 验证口径 + 已知残留）并在 INDEX「变更汇总」登记。T2 8541 passed。

## 未完成
- **主线批次全部完成。** 剩余工作全部在下方「顺手做清单」（不排期）。
- 待办池：空（bug/功能按「用户可感知 bug 优先」，登记类型/现象/期望/批次）。
  - **2026-11-20 用户登记（只留记录，暂不实施）**：删除「生小肥鱼」相关功能。
    范围：右键「生小肥鱼 / 退出子肥鱼」两项、`context_menus` 的 `spawn_pet` /
    `clear_spawned_pets`、`slot_manager` 的 spawn 大小/灵动岛策略、设置页「生小肥鱼」组、
    `overlay_shell.spawn_pet` 与子宠身份/档案链。动手前先确认多宠身份链已可安全摘除、
    slot0 主宠不受影响。
  - **2026-11-20 用户登记（只留记录，暂不实施）**：删除碰撞相关功能。
    范围：`pet/collision.py`、`pet/sprite_collision.py`、三路碰撞监听
    （`_on_collision_squash` / `_on_collision_probe` / `_on_collision_sound`）、
    `collision_enabled` / `collision_sound_*` 设置项；连带决策：抛掷反弹、
    岛屿 stadium clamp（`sprite_collision.capsule_circles` 经 `island/bridge.py`）、
    边缘探头「被撞飞 → 重进倒计时」三条依赖要一并给出替代或一并删除。
    两项均为功能级删除：单独批次 + 独立提交，先跑 `pytest --collect-only -q` 枚举 import 断点。

## 顺手做清单（2026-11-15 用户决定：不单独排期；改到对应功能时一并做，
## 独立提交 + T1/T2 验证，不与功能改动混 diff）
- 6e 散落 if/else 死分支：window.py、webm_clip.py、session_watcher.py、
  config_write_lock.py、chat/session_store.py、harness_launcher.py、
  frameseq_provision.py、updater.py、tts/doubao.py（改到哪个顺手删哪个）。
- 6d-2 game_fps / fps_monitor / fps_permission 整链（涉岛屿「游戏帧率」段 UI，功能级决策）。
- 设置页「互动 · 快捷键」页签永久禁用——动设置页时评估整页移除。
- 被删模块的 test_architecture 删除守卫，随各自顺手批补。
- `scripts/cleanup_mei_cache.py` + `test_cleanup_mei_cache_cli.py`（Windows onefile 时代的
  临时目录清理工具，README 章节已删）——下次动 scripts/ 时一并评估删除。

## 边缘探头唤醒语义（2026-11-21，**本地改动未提交**）
- 用户反馈：贴左右边隐藏后点击唤醒，仍有一小截身体在屏外且**不能点击互动**；只能整只拖进屏幕。
- 根因：`EDGE_ENGAGE_EXPOSURE=0.82 < 1` → `probe_active` 不收（`_enter_acts`/`_plan_move` 闸门一直关着）；
  `on_sprite_clicked` 在 STRAIGHTENED 只重置倒计时却 `return True`，壳层据此吞掉点击动画/音效/气泡；
  唯一能真正退出的是 `cancel`（真拖拽/碰撞/关功能/回角落）。
- 修法（用户选的 A）：点击 = `cancel("click_out")` + 返回 **False**（点击交回普通链路，整只经常规钳制回屏内），
  仍静止在原边则 `EDGE_IDLE_SECONDS` 后自动缩回探头（期间再点击把倒计时推后）；
  拖拽升级时**只有探头取消真的挪了位置**才用事件全局坐标重设抓取偏移（修「拖很久才跟手」）；
  `STRAIGHTENING/STRAIGHTENED/RETURNING` 三个死状态与 `EDGE_ENGAGE_EXPOSURE` 一并删除。
- 验证：T3 串行全量 **8503 passed / 64 skipped / 0 failed** + webm 族串行 **41 passed**（合计 8544）；
  新增回归用例：点击退出后整只回屏内且 `probe_active=False`、重进倒计时可被点击推后、
  拖拽 rebase 后第一帧 1:1 跟手、壳层只在探头挪位时 rebase（普通拖拽逐位不变）。
- 诊断日志（为右侧「贴边留一条缝」准备）：`[overlay 几何] 建宿主/几何重算 overlay=… bounds=… screen=… geometry=… available=… dpr=…`，
  以及 `[边缘探头] 姿态 side=… 目标x=… 实际x=… 投影框=… 身体框=… 可用区=…`（0.5s 节流）。
- **右侧「贴边留一条缝」根因（已修）**：macOS **首次原生建窗前**的 `setGeometry` 会被
  `visibleFrame` 收窄——实机用 `CGWindowListCopyWindowInfo` 读原生矩形：Qt 报
  `(0,33,1470,923)`，原生实际 `(0,33,1450,903)`（右/下各少 **20pt**）；**show 之后**再
  `setGeometry` 才被接受（本机四种 flags 组合都能复现：与 Tool/透明无关）。
  后果：壳的 `host.bounds` 是请求矩形（1470×923），sprite 坐标系比真实窗口大 20px →
  贴右边缘的角色被窗口裁掉 20px（用户看到的就是"离屏幕还有段距离"），贴底时脚同样被切；
  左侧因窗口左缘 x=0 对齐所以看不出来。
  修法：`OverlayWindow.showEvent` 里补 `_reassert_geometry_after_show()`，并排 `0ms/60ms`
  两拍延迟对账（Cocoa 的收窄晚于 showEvent；只在 cocoa 平台执行，offscreen 测试零影响）。
  验证：同一脚本 show 后 Qt 与原生矩形都变成 `(0,33,1470,923)`。
- 遗留：legacy `pet/edge_probe.py` 仍是旧的「拉直 0.82」语义（只有 `stream_capture_mode` 直播捕获走那条）。
  右侧留缝的根因与修法见「右侧贴边留一条缝·根因（已修）」及文末「2026-11-21 收口」——**已修并由用户实机确认**。

## 2026-11-21 收口（**用户已实机确认**）
- **20pt 收窄修复确认通过**：右贴边真的贴住、点击唤醒整只回屏内、5 秒后自动缩回探头；左右一致。
- 顺手修掉的两个隐患（均带回归用例）：
  1. `overlay_window.paintEvent` 的重绘闸门由 `region.intersects(sprite.rect())` 改为
     `paint_bounds()`——45° 探头/抛掷旋转把像素画到 `rect()` 之外，"只脏在溢出带"的那一拍
     会被整只跳过（该擦的没擦、该画的没画 → 残影/直边）。用例
     `test_paint_gate_uses_paint_bounds_for_rotated_overflow`。
  2. 逐只隐藏（`sprite.visible == False`）的 sprite 仍会被探头继续摆姿态 → 重新显示时
     留下"半身在屏外 + 点击只脱困"的僵态。`SpriteEdgeProbeWorld.tick` 现在跳过不可见
     sprite 并收掉在途会话（`cancel("hidden")`）。用例
     `test_invisible_sprite_never_peeks_and_hidden_session_is_cancelled`。
- 清理（零行为）：`_visible_rect_cache` 改显式初始化；`mouseReleaseEvent` 删掉"探头消费点击"
  的死分支；`showEvent` 的延迟对账改 `for delay_ms in (0, 60)`；新增 `resizeEvent` 兜底
  （原生重建/切屏导致的收窄也自动补回）。
- 验证：**T3 串行全量 8506 passed / 64 skipped / 0 failed（11:45）** + webm 族串行 41（合计 8547）；冒烟改动后再跑焦点 89 绿。
- **遗留隐患（登记，本次未处理）**：
  - legacy `pet/edge_probe.py` 仍是旧「点击拉直 0.82」语义（只有 `stream_capture_mode` 直播捕获走）。
  - macOS 首建窗 20pt 收窄是**平台行为**：`OverlayWindow` 已补正，但将来若加别的全屏窗口
    （全屏气泡/调试窗）必须自己补 `showEvent`/`resizeEvent` 那一次 `setGeometry`，否则同样差 20pt。
  - `probe_target_x` 右缘用 `bounds.right()`（含端点），`edge_side_at_rest` 用 `right()-1` —— 1px 口径差，
    无观测影响，改到该函数时一并统一。
  - `SpriteEdgeProbeWorld.active` = 任意 `mode != OFF`（含重进倒计时态），壳层若拿它当"正在探头"
    门禁需注意这一口径（当前壳层只用它做快捷判断）。
  - `catalog._body_box_scaled` 的 docstring 写"已镜像对称化"，但代码只读 manifest、**不做镜像归一化**；
    而 `pet_sprite._body_local_rect` 在 `facing == "right"` 时画的是镜像帧。左右不对称的角色包会因此
    出现"一侧贴边、另一侧留缝/钳制偏差"（shenshen 的 box 左右各 212px，所以看不出来）。改到该函数时
    要么按 `_mirror_frame()` 翻转 box，要么改掉那句 docstring。
  - macOS 的 20pt 窗口收窄是**所有窗口**都会遇到的（`constrainFrameRect`）：贴屏幕右/下缘的浮动窗
    （气泡、快速对话、灵动岛）若将来改成"贴边"定位，也要预期被让 20pt；本次只补了 OverlayWindow。

## 验证协议
- **T1 快门**（每批，~2 分钟）：`ruff check pet/ tests/` + `pytest --collect-only -q`
  + 引用方焦点测试。
- **T2 全量并行**（默认，~1:50 + 串行族 30 秒）：`.venv/bin/python -m pytest -q -n auto
  --ignore=tests/test_webm_reader_lifecycle.py --ignore=tests/test_webm_clip_lifecycle.py
  --ignore=tests/test_webm_first_frame_lock.py`（webm 族在并行负载下会原生崩溃，
  单独串行跑这三文件），env：
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
