# 工程教训登记（LESSONS）

> 活文档：每条 2-3 行（现象 → 对策），按日期倒序；先搜同类再追加。新会话经
> `AGENTS.md`（自动加载）触达；与 AGENTS.md 冲突时以 AGENTS.md 纪律为准。

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
