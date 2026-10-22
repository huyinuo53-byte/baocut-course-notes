# 可追溯运行：来源 → 尝试 → 产物 → 复核 → 交付

目标是回答“这句话依据什么、为什么复用、哪里返工、交付的是哪一版”，而不是保存所有工具输出。沿用 notes、image-audit、review 和 events，不复制正文进日志。每个视频一个写入者；批次协调者只维护批次清单和汇总。

## 最少需要记录什么

| 记录 | 位置与关键字段 | 自动还是声明 |
|---|---|---|
| 范围基线 | run.json：run_id、batch_id、item_id、视频稳定 ID/规范 URL、requested_outputs、required_checks、scope_revision、scope_changes（时间、用户要求、增加的工作） | 人工核对；新增 PDF、翻译或重审单独记范围变更 |
| 来源身份与完整性 | sources：id、path、来源 URL/项目 ID、kind、language、duration_seconds、媒体流时长/尾部解码结果、PDF 物理页数、transcript_origin（reused/generated/supplemented）、复用依据、原任务/导出 ID、known_gaps | 文件哈希自动；内容匹配、语言和复用理由须核对 |
| 执行环境 | toolchain：实际 CLI/runtime/Skill 版本、脚本和模板哈希、实际可见的转写模型/语言/参数；模型未知 null | 取实际工具输出；不推测路由、设备或模型 |
| 工作尝试 | events.jsonl：run_id、item_id、actor、stage、attempt_id、job_id、status、reason、evidence、发生/记录时间 | 阶段入口/出口及时记录；重试新 attempt_id，轮询同一 job 不算重试 |
| 文件依赖和版本 | trace-spec.json + trace-rNN.json：原文件、补转写、实际使用的合并索引、选图、notes、脚本/模板、HTML、audit/review 之间 depends_on；每个文件 sha256/bytes | 哈希自动，依赖声明；复用也须保留来源链 |
| 阅读和复核覆盖 | review 引用 audit：谁、检查方法、范围、源哈希、发现、证据、结论；逐图记录沿用 image-audit | 阅读/视觉核对是人工声明；结构覆盖不能替代 |
| 问题与修复 | audit.issues：稳定 issue_id、严重度、关联章节/原句/时间或页码、问题证据、修复前后哈希、修复动作、复验人/方法/结果、状态 | 每次修复保留历史；未解决项不能因重新生成而消失 |
| 交付及资源 | review：本次交付路径、快照、质量状态/阻塞、范围版本；metrics 记录实测耗时、媒体小时、页数、选图数、重试/返工、实际 token/费用及其数据来源 | 汇总从当前文件/复核生成；无法可靠取得一律 null |

run.json 是薄的元数据入口，可用已有 manifest.json 承担上述字段；不要复制维护两份。events 是执行历史，review 是验收事实，冻结快照是交付版本依据。批次首页/汇总从逐课 review 和当前产物生成，不手写另一份“完成数量”。课程完整覆盖应核对预期视频清单与逐课产物，文件快照本身无法发现漏列视频。

## 时间和并行必须说清楚

保留 `at` 为记录入日志的 UTC 时间；v2 的 `occurred_at` 才是所声明的实际发生时间。实时记录默认相同。事后补录用 `--time-basis retrospective`，实际时间未知就不传 occurred-at，保持 null；已知时必须带时区并在 evidence 引用原始日志。旧 events 无 time_basis 时按历史证据解释，不能自动当精确阶段计时。

```sh
python3 <skill>/scripts/course_notes.py record --run <run> --stage asr --status started \
  --run-id RUN --item-id part-02 --actor coordinator --attempt-id asr-01 \
  --job-id ACTUAL_JOB_ID --evidence logs/asr.jsonl
python3 <skill>/scripts/course_notes.py record --run <run> --stage asr --status failed \
  --run-id RUN --item-id part-02 --actor coordinator --attempt-id asr-01 \
  --reason network_timeout --evidence logs/asr.jsonl
```

started/终态按 `(run_id,item_id,stage,attempt_id)` 配对；后台 job_id 必须来自实际返回，没有则 null。paused 不是 failed；reused 表示复用证据，不等于本次重新运行。失败后重试另起 attempt，detail 引用前次 attempt 和新证据。CLI 返回并不等于后台作业完成，started/completed 需描述其测量边界，例如 download_client 与 asr_backend 分开。

阶段建议区分：下载、服务排队、ASR 推理、读转写、选图、写笔记、渲染、内容复核、UI 验证、修复和等待用户。没有后台阶段时间则 queue/compute 保持 null，不由百分比反推。并行总墙钟用真实起止；计算活跃时间必须给出定义、按时间区间并集计，不把各代理耗时相加当用户等待。进程可用单调时钟测持续时间；跨主机不能直接相减当精确计时。本工具记录事件，不自动推算 active_seconds 或费用。

性能比较同时标明：范围版本、视频小时/语言、讲义页数、实际阅读覆盖、独立复核范围、衍生产物、复用比例、失败与返工。按课程总耗时或 token 数直接排序都可能误导；先区分工作量、范围变化与真正吞吐改进。代理数不是后台实际并发数。实际 token/费用需附宿主统计或账单来源及计量范围，没有则 null；日志不存 Cookie、令牌、签名下载 URL、完整环境变量或带密钥的命令。

## 文件快照与失效传播

在各阶段完成时保存必要快照；最终交付前冻结一份完整快照。SHA256 分块计算，不把视频读入内存。脚本不调用模型，不改 BaoCut 项目。

准备 spec（JSON，以下为最小例子；实际加入所有使用的图片、分块、补转写、模板、审查证据和必要外部文件）：

```json
{
  "schema_version": 1,
  "run_id": "VIDEO-UTC",
  "basis": "observed_build",
  "root": ".",
  "artifacts": [
    {"id":"run", "path":"run.json", "depends_on":[]},
    {"id":"transcript", "path":"transcript.json", "depends_on":[]},
    {"id":"index", "path":"chunks/index.json", "depends_on":["transcript"]},
    {"id":"notes", "path":"notes.json", "depends_on":["index"]},
    {"id":"renderer", "path":"/absolute/skill/scripts/course_notes.py", "depends_on":[]},
    {"id":"template", "path":"/absolute/skill/assets/template.html", "depends_on":[]},
    {"id":"html", "path":"课堂笔记.html", "depends_on":["notes","index","renderer","template"]},
    {"id":"review", "path":"review.json", "depends_on":["run","notes","html"]}
  ]
}
```

```sh
python3 <skill>/scripts/trace_artifacts.py capture --spec <run>/trace-spec.json --out <run>/trace-r01.json
python3 <skill>/scripts/trace_artifacts.py check --snapshot <run>/trace-r01.json
```

- root 相对 spec 所在目录；artifact path 相对 root，明确声明的绝对路径也可用（例如工具脚本）。跨机移动需显式 `check --root <new-run-root>`；外部绝对路径丢失将报告 unavailable，不猜替代文件。需要长期可重放时保留授权范围内的脚本/模板副本。
- capture 只记录当下字节和声明的依赖，**不能证明生成器真的消费了这些输入**。observed_build 仅用于亲自执行并观察过依赖链的本次生成；旧资料补录必须 historical_inventory，不能借新时间戳宣称历史构建已验证。
- check 的 unchanged 仅表示所列文件未变，不表示完整、正确、已读、已视验。changed_files 是直接变化；unavailable_files 是缺失/不可读；requires_revalidation 是未列入前两项、但受依赖变化影响的下游（文件本身未变也会列出）；待处理范围取三个列表的并集。发现变化返回退出码 2；格式/运行错误为 1；unchanged 为 0。
- 修改转写/讲义/图片/notes/模板后，先检查旧快照确定受影响范围，重新生成并实际复核，才保存新 revision。禁止只重录哈希消除告警。旧快照不覆盖；capture 拒绝覆盖已有路径。新文件名和 review 的 revision/变更原因串起修复历史。
- 最终 review 先写将要生成的快照路径，再 capture；快照可以绑定 review，但不要让 review 反向嵌入该快照哈希，避免循环。动态 events 可以在交付快照前复制冻结，或者不列入最终快照并明确它是持续追加的日志。
- 脚本不验证依赖声明是否齐全，也不是防篡改签名。snapshot/spec 均保留；重要交付可把快照哈希写入独立交付回执。禁止用文件 mtime 代替内容版本或执行耗时。

## 复核粒度与后向兼容

继续使用 notes schema v2，事件扩展保留旧的 at/stage/status/detail。section 没有稳定 ID 时，使用“notes_sha256 + 一基章节序号 + source_ids”定位，不能把改稿后的同一序号误当同一内容。每个关键结论/问题要可追到原句 ID、视频秒数或 PDF 物理页，图像还要有对应图片哈希。

复核记录至少分开：转写全读、音频回听（区间）、PDF 阅读（页集合）、视频画面抽查（秒数）、入选图逐图检查、结论回查（章节/句 ID）、静态校验、桌面/窄屏/真实手机。抽样要写分母、选择方法和未覆盖范围，不能把 read_chunks 齐全当成语义内容完整率。独立性也要诚实：作者自查、同一代理二次审查、另一代理审查分别标注，不统称独立人工复核。

历史任务按需做只读盘点；保留原交付与原事件，不补造发生时间、模型、token、重试或“全量验证”记录。无需为了新字段重转写或重生成一门已完成的课。当前无证据的字段留 null，未来运行从阶段入口开始记录。
