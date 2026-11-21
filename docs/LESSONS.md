# 工程教训登记（LESSONS）

> 活文档：每条 2-3 行（现象 → 对策），按日期倒序；先搜同类再追加。新会话经
> `AGENTS.md`（自动加载）触达；与 AGENTS.md 冲突时以 AGENTS.md 纪律为准。

## 2026-11-21

- **同一批 run_commands 里「写文件 + 读文件」会读到旧内容**：多条命令是并发执行的，
  `python 写文件` 与 `sed/grep 读文件` 放同一批时，读的可能是写前快照（本轮两次踩到，
  误判成"没写进去"）→ 写与回读分两批，写完单独 `git --no-pager diff --stat` 核实。
- **xdist 并行全量可能在 99% 卡死**：worker 测试跑完但不退出（控制线程停在 execnet 读、
  worker 停在 Qt/CoreAudio 信号量上），日志停在最后一个进度点、没有 summary → 改用串行
  `-p no:randomly` 全量（11:43）拿确定结论；并行 hang 不等于有失败，别拿中途进度点当结论。
- **合成鼠标事件下禁止用 `QCursor.pos()` 当手势坐标**：刷新抓取偏移若取真实光标，测试/
  自动化里会把宠物甩到无关位置（本轮首版 rebase 就这样打红 8 条拖拽/气泡/跨屏用例）→
  一律用事件自带的 `globalPos`，缺省时保持原偏移（宁可不动也不能猜）。
- **动共享拖拽语义前先跑最敏感的一组用例**：`test_overlay_hosts_multiscreen` /
  `test_overlay_seam_passage` / `test_overlay_virtual_desktop` / `test_sprite_bubble`（8 条），
  它们用合成事件断言落点；新语义要么逐位不变，要么先改用例并写清为什么。
- **删状态机的死状态要连带常量/`__all__`/测试 import**：本轮删 `STRAIGHTEN*/RETURNING`
  后 `EDGE_ENGAGE_EXPOSURE` 等仍被测试导入 → 删前 `grep -rn` 全仓，改完 `pytest
  --collect-only -q`（1.7 秒）确认没有 ImportError，再跑焦点用例。
- **macOS 首建窗会偷偷把窗口收窄 20pt/边**：`setGeometry(availableGeometry)` 在 `show()`
  之前调用时，原生 frame 被 `visibleFrame` 收进——本机实测 `(0,33,1470,923)` →
  `(0,33,1450,903)`；**show 之后**再 `setGeometry` 才生效（与 Tool/透明 flags 无关，四种
  组合都复现）→ 全屏 overlay 必须在 `showEvent` 后补一次（0ms/60ms 两拍），否则
  `host.bounds` 与真实窗口差 20px，表现为"右侧贴边留一条缝 / 贴底脚被切"且左侧正常。
  取证手段：ctypes + `CGWindowListCopyWindowInfo` 读**原生**矩形，别只信 `QWidget.geometry()`。

- **重绘闸门与命中判据必须同源**：`paintEvent` 若用未旋转的 `rect()` 判脏区、`sprite_at` 用
  `paint_bounds()`，45° 探头/抛掷旋转把像素画到 rect 外时，"只脏在溢出带"的那一拍会整只不画
  （残影/直边）→ 两处统一用 `paint_bounds()`。
- **逐只隐藏不是整窗 pause**：按 tick 推进的世界（边缘探头/行为控制器）必须自己跳过
  `sprite.visible == False` 并收掉在途会话，否则隐藏期间仍被摆姿态，重新显示即僵态。

## 2026-11-15

- **终端/heredoc 不可靠**：heredoc 会被终端集成吞掉（文件未建、后续命令不执行），
  简单命令无输出=会话卡死 → 重要文件用编辑器/脚本落盘并回读核实；卡死时重启终端，
  仅用只读工具读 `.git/` 元数据（reflog 可还原时间线）继续分析。
- **测试运行期间禁改 .py**：`inspect.getsource` 按导入时行号读源码，跑动中编辑
  （哪怕删个 import）会假报「找不到白名单元组」→ 只读侦察，改文件等收口。
- **文本替换删行会咬缩进**：8 空格 pattern 会命中 16/12 空格行的子串，制造
  Unexpected indentation → 三行锚点 + `assert count==1`；改完立即
  py_compile + ruff + collect-only（~20 秒）。
- **空 def 炸收集**：删测试留无函数体的 `def` → IndentationError 中断全部收集
  → 删完整函数（含 docstring/装饰器），删完 collect-only。
- **定时炸弹测试**：`ChatMemory.load()` 用真实墙钟无视注入 clock，冻结 NOW 后
  23 天必红 → 注入 clock 时 grep 全部 `datetime.now()`，读路径同源，生产默认值
  逐位等价。
- **上游数据边界不钉死**：lunar-python 1.4.9 已含 2027 安排，测试钉死「2027=表外」
  → 边界语义用替身注入（进出清 lru_cache），真表内稳定断言保留。
- **删模块先全仓 collect-only**：14 秒枚举全部 import 断裂（比全量便宜两个数量级）。
- **xdist 并行全量 7 倍提速**：8582 例 12:12→1:47 零失败 → 批次收口默认
  `-n auto`；时序族偶红先隔离复跑，连续 flake 才回串行；xdist 下进程级全局
  按 worker 各一份。**必排除 webm 生命周期族**（reader/clip_lifecycle/
  first_frame_lock）：并行负载下 xdist worker 会原生崩溃（`worker crashed`，
  与 CI 记载的 reader+imageio 段错误同族），T2 用 `--ignore` 三文件后串行单跑
  该族（41 例约 30 秒），合计即全量口径。
