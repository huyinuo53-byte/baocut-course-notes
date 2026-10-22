# 数据交接合同 v2（兼容v1基本笔记）

Agent读完转写和画面后写notes.json；脚本不生成语义内容，不操作.bcut。所有正文是纯文本，由渲染器转义。schema_version可省略；旧版frames未声明source_type时按video_frame处理。

```json
{
  "schema_version": 2,
  "title": "课程标题",
  "source_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "limitations": ["完整阅读已导出转写；画面按换页采样，未逐秒听审；真实手机未测试"],
  "read_chunks": ["chunk-0001"],
  "omitted": [],
  "summary": ["简短摘要，指向本课核心问题和结论。"],
  "sections": [{
    "title": "实际主题转场",
    "start": 0,
    "end": 300,
    "source_ids": ["s-g1.0"],
    "paragraphs": ["教师的论证与适用边界。"],
    "examples": ["课堂案例、代码与演示细节。"],
    "editor_notes": ["标明讲义补充或整理者解释。"],
    "frames": [
      {"source_type":"video_frame", "path":"frames/120.png", "time":120, "caption":"视频此秒显示的内容"},
      {"source_type":"pdf_page", "path":"frames/slide-03.png", "source_label":"官方课程讲义", "source_url":"https://example.org/slides.pdf#page=3", "page":3, "related_time":125, "caption":"讲义内容；时间只作讲解导航"}
    ]
  }],
  "self_test": [{"question":"复习问题", "answer":"有证据支持的答案", "section":1}],
  "supplements": [{"title":"未在课堂展开的主题", "text":"补充正文", "source_label":"官方讲义，课堂未展开", "source_url":"https://example.org/slides.pdf", "pages":[3,4]}]
}
```

## 覆盖与来源

- source_ids来自chunks/index.json，每句恰好归属一个section或omitted；omitted格式为`{"id":"s-1","reason":"休息，无教学内容"}`。重复归属、缺失、同时引用和省略都报错。仍需人工判断正文是否真正保留相应知识点。
- read_chunks只能在实际读完后填写。脚本检查完整声明，不能证明真实阅读。
- 时间单位秒，区间包含引用的原句和视频帧。未知首尾/缺段在limitations写明；转写全读不等于音频无漏词。
- paragraphs/examples/editor_notes/summary均为纯文本字符串列表。summary、self_test、supplements可省略。自测section为现有章节的一基编号，可省略；不绑定虚构课堂时间。
- 补充条目有明确source_label，外部URL限http(s)，pages为正整数的PDF物理页码。旧稿`official_slide_supplements`视为supplements兼容别名，默认source_label为官方讲义，不能同时给两种字段。其他自定义内容字段不会自动排版；增加新字段前先确认渲染器和导出链支持，防止静默遗漏。

## 图片

所有图片均为run目录内PNG/JPEG/WebP，路径不能逃出run。每幅必须有caption，并在实际查看后选入。图片完整性复核另存 `image-audit.json`（见 [逐图验收](quality-delivery.md#逐图完整性验收)）；不改变既有 notes schema，也不把新字段塞进正文。

- `video_frame`：time是该帧实际截取时间，必须落在所属节区间内。
- `pdf_page`：source_label及page必填；source_url可选。不得写非空time。related_time是可选的相关讲解导航，必须在节区间内，渲染时明确说明不是同秒截图。
- 印刷页号与物理页码不同，额外印刷页号写caption，不覆盖page。
- 没有有价值画面可frames=[]，说明原因；不为凑数量制造插图。

## 运行和审查

保留原始导出、chunks/index.json、notes.json、选用图、课堂笔记.html、events.jsonl及review.json；课程批量清单放协调目录。审查差异可单独audit.json并从review引用。

```json
{
  "run_id":"视频ID-UTC时间",
  "outcome":"partial",
  "summary":"产物地址、实际完成与剩余检查",
  "validation": {
    "content":{"status":"passed", "evidence":"audit.json"},
    "html_static":{"status":"passed", "evidence":"检查范围与记录"},
    "desktop":{"status":"pending", "evidence":null},
    "narrow":{"status":"pending", "evidence":null},
    "real_phone":{"status":"not_requested", "evidence":null},
    "pdf":{"status":"not_requested", "evidence":null}
  },
  "blocker":null,
  "resume_condition":null,
  "source_hashes":{},
  "lessons":[{"status":"candidate","scope":"具体环境/阶段","finding":"实际问题","evidence":"错误或测试结果","next_action":"下次如何验证"}],
  "metrics":{"wall_seconds":null,"active_seconds":null,"tokens":null}
}
```

outcome为completed/partial/failed，validation状态为passed/pending/blocked/not_requested。未测不写passed；unknown用null。真实设备验收是否必需按本次用户目标决定，但未做不得声称“手机实测”。导出检查与内容阅读分开，哈希绑定本次实际源版本；记录实际渲染使用的证据index路径与哈希。补转写后可能使用合并索引，恢复时不能猜固定文件名或改read_chunks来迁就旧索引。失败也写review。

只有用户直接授权更新memory时才写短更新；不保存逐字稿、账号或原始会话。Skill更新与memory更新是不同操作。

## 可追溯扩展（不改变 notes v2）

课程推荐材料按 [推荐材料与论文](reading-materials.md) 保存 materials.json，补充正文仍用 editor_notes/supplements、论文图用 pdf_page。review.validation 加 reading_materials 与 material_integration，并引用实际材料 ID、阅读范围和回查证据；未读/受限不标 passed。材料原文、台账与 notes/HTML 的依赖加入 trace-spec，不要求旧任务为了新字段重读或重新生成。

完整视频笔记另存 visual-inventory.json 与 visual-coverage.json（见 [视频视觉覆盖](visual-coverage.md)），review.validation.visual_coverage 必须通过。音频/字幕齐全或 PDF 齐全不能代替此门槛；未核完用 partial。明确摘要、纯音频或纯讲义模式按范围记 not_requested。

运行入口、events v2、不可覆盖的文件依赖快照、修复与复核记录按 [可追溯运行](traceability.md)。review 可增加 `trace_snapshot`、`scope_revision`、`delivered_files` 和 `audit` 路径，保留已有 validation/metrics 语义。最终 review 与产物一起冻结；未知 token、费用、阶段耗时仍为 null。旧任务只读盘点不冒充本次生成。


## 阅读布局

详细 HTML 的阅读顺序由独立的 `reading-layout.json` 表达，合同见 [阅读布局与图文整合](editorial-layout.md)。事实与来源仍写在本合同的 notes 字段中；supplements 是资料类型，不要求在文末集中展示。布局必须绑定 notes 原始字节 SHA，完整引用每个正文与配图单位；只允许资料图跨节展示，视频帧保持真实时间归属。
