# 视频视觉覆盖：先盘点，再选图

适用于完整视频课堂笔记及其质量复核；纯音频、明确只要摘要或只整理讲义不强加视频要求。历史成品按本次范围修复，保留旧版验收，不追补虚构历史过程。

## 采集与判断

- 复用同一 video ID 的完整本地视频与 fresh 转写，不重复 ASR。只有音频时单独补视频轨，保留来源与时间对齐依据。检查 per-stream 时长及尾部解码；容器时长不能证明完整。无法合法取得完整视频时记录缺口，继续不受影响阶段，视觉检查不得 passed。
- 对全时长做变化检测，结合定时兜底、相似帧去重、讲义匹配。保留原始候选清单和参数，去重/裁切前保留全画幅定位证据。单一 scene 阈值或每五分钟一帧不能假定完整；小字变化、渐进动画和代码演示加密检查，疑似区间回看前后状态。
- 逐项看候选，按内容而非图片配额判断。静态页用官方完整页；动画保留必要中间阶段与最终结果；板书、注释、命令/输出和操作链补真实帧与解释。最终页不一定覆盖中间论证。讲师、过场和重复状态可省略，但记录理由。
- 官方 PDF 做页级盘点：已讲且承载新知识的图表/公式不能因章节已有一图而丢弃；未讲内容归补充，不绑定虚构口述时间。保留视频与 PDF 不同版本的差异。
- 联系表只用于导航；关键公式、细小图表、代码、差异及入选图按可读分辨率查看。不得由脚本自动把未执行的目视检查填成 passed。

## 台账与门槛

visual-inventory.json 是自动候选清单，含媒体哈希、时长、检测/采样/去重方法及所有 candidates（id、time、path、sha256）。去重前后的映射或扫描记录另存并绑定哈希。visual-coverage.json 是审查台账，不改变 notes v2：

```json
{
  "schema_version": 1,
  "notes_sha256": "当前notes哈希",
  "inventory": {"path":"visual-inventory.json","sha256":"清单哈希"},
  "media": {"path":"../media/video.mp4","sha256":"媒体哈希","duration_seconds":3600,"video_duration_seconds":3600,"tail_decode":"passed"},
  "method": "全时长变化检测+定时兜底；候选逐项看图；动画区间加密回查，非逐秒观看",
  "reviewed_windows": [{"start":0,"end":3600,"evidence":"review/contact-01.jpg及区间回查记录"}],
  "states": [{"candidate_id":"v001","disposition":"included","description":"板书补充推导","evidence":"与PDF第3页及转写比较","targets":[{"section":1,"frame":2}],"known_gap":false}],
  "pdf_pages": [{"page":1,"disposition":"transition","reason":"标题页，无新增教学信息"}],
  "known_gaps": [],
  "status":"passed"
}
```

每个 candidate 恰有一项处置：included（入选帧）、official_page（成品讲义页覆盖）、represented_in_text（图像无独立信息且正文明确保留）、duplicate（指向已审状态）、transition（讲师/过场无教学新增）、unreadable、known_gap、pending。前三者给 notes 章节或帧 targets；duplicate 给 duplicate_of。后三者阻止完成。描述与比较证据来自实际审查，不按章节平均分配或批量模板声明。

reviewed_windows 覆盖全时长，表示所述方法的审查范围，**不是逐秒观看证明**。说明阈值、兜底间隔、去重和可能漏检边界；结构校验不能证明所有独特状态已找到。PDF 台账附源哈希与总页数，逐页说明入选、正文覆盖、重复、未讲补充或缺口。

运行 `python3 <skill>/scripts/validate_visual_coverage.py --notes <run>/notes.json --coverage <run>/visual-coverage.json`。它检查文件版本、候选逐项处置、审查时间轴、目标引用和缺口；不识别语义，不替代逐图或浏览器验收。review.validation 增加 visual_coverage；新完整视频任务必须 passed 才可 completed。没有可靠统计仍记 tokens=null，耗时仅记实测范围，不由帧数猜实际计费。

整批流程变更先用一课验证：确实发现/补齐遗漏、证据与时间正确、缺口能阻止完成、HTML 双视口通过，再推广。可复用媒体/转写准备，样板未通过前不批量覆盖成品。
