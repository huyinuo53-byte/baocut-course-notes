# 保真评测：精度与召回

两个问题，两个指标：

| 指标 | 问题 | 做法 |
|---|---|---|
| 精度 | 笔记写下的东西对不对？ | 评审拿笔记条目对照它引用的原句、画面或外部来源，判断是否有支持 |
| 召回 | 课上讲的东西有没有漏？ | 出题者只看原始转写和画面出题，答题者只看笔记作答 |

评测替代了旧流程里的逐图审计台账、视觉覆盖台账和 review 验收表：那些是作者自己填写的声明，脚本只能检查格式；这里由另一个评审对照原始证据检查最终内容。

## 角色与独立性

- `reviewer`（精度）、`question_author`、`answerer`（召回）各取 `independent_agent` / `human` / `same_agent`。
- 理想做法：出题者与答题者是两个互不知情的子代理，都不是写笔记的代理。出题者看不到笔记，答题者看不到转写。
- 任何一个角色是 `same_agent` 时，结果最多是 `self_checked`，不能报告为 `passed`。

## 精度

- **全量**检查顶层：每节 `takeaway`、每张 `visual`、`map`。这些是读者最先看到、压缩最狠的内容，任何一条 `unsupported` 或 `distorted` 都判失败，不论平均分多高。
- **抽样**检查完整笔记：建议每节至少 2 条，优先数字、条件、因果和外部资料结论；写明抽样方法。
- 判定：`supported`（有支持）、`partial`（部分支持或丢了条件）、`unsupported`（找不到依据）、`distorted`（与来源相反或改变了语气，如把“我猜”写成事实）。`evidence` 写对照的原句 ID、时间、页码或链接。
- ref 写法：`s3:takeaway`、`s3:visual`、`map`、`s3:p1`、`s3:e0`、`s3:n0`、`s3:f0`、`x2`、`q4`（自测）、`summary0`。

## 召回

- 出题者通读转写并查看关键帧/讲义，出 ≥ 20 题（默认门槛），覆盖全课时间轴；题目考事实、条件、数字、因果和方法步骤，不考措辞。画面里才有的信息要单独出题（`from: visual`）。
- 每题写 `expected`（标准答案）和 `evidence`（原句 ID 或帧时间）。
- 答题者只读 notes.json 或 HTML 作答，并写 `found_in`（在哪节找到）。判定：`correct` / `partial` / `missing`（笔记里没有）/ `wrong`（笔记里的说法与标准答案冲突）。
- `missing` 是遗漏，回到转写补进完整笔记；`wrong` 先查是笔记错还是题目错，再改。

## 文件格式

```json
{
  "schema_version": 1,
  "notes_sha256": "被评测的 notes.json 原始字节 SHA-256",
  "sources": {"transcript_sha256": "...", "visual_inputs": "frames/ 下 311 张候选的联系表 + 课件第69–86页"},
  "precision": {
    "reviewer": "independent_agent",
    "method": "全部 takeaway/图解/地图 + 每节抽 2 条完整笔记",
    "items": [{"ref": "s5:visual", "verdict": "supported", "evidence": "s5:p1 / s-212–s-218", "note": ""}]
  },
  "recall": {
    "question_author": "independent_agent",
    "answerer": "independent_agent",
    "items": [{"id": "q01", "from": "transcript", "question": "讲师的均线组合是哪三条？", "expected": "EMA21、MA50、MA200", "evidence": "s-40", "answer": "EMA21、MA50、MA200", "verdict": "correct", "found_in": "s2"}]
  }
}
```

## 评分与门槛

```sh
python3 <skill>/scripts/fidelity_eval.py --notes <run>/notes.json --eval <run>/fidelity-eval.json
```

- 精度 = (supported + 0.5×partial) / 条目数；召回 = (correct + 0.5×partial) / 题数。
- 默认门槛：精度 ≥ 0.95，召回 ≥ 0.85，题数 ≥ 20，用了画面时至少一道画面题。可用参数调整，调整理由写进 manifest。
- `notes_sha256` 必须等于当前 notes；notes 改动后旧评测失效，`manifest.py freeze` 也会拒绝。
- 未达标：每个失败条目在 manifest 记 issue（问题、证据、修复、复核人），改完后重新评测。

## 它证明不了什么

- 出题者和答题者都没注意到的遗漏，评测发现不了；`source_ids` 全覆盖检查仍是底线。
- 分数复述的是评审的判断，不证明评审读完了全部材料；把方法和输入范围写清楚。
- 可读性不在这两个指标里，靠浏览器检查和读者反馈。
