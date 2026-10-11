# 工作区数据

```text
outreach-workspace/
  profile.json           申请人身份、事实、邮箱和附件路径
  request.json           学校/地区、兴趣、申请阶段和调研范围
  cv.json                简历纯文字内容
  teachers.csv           入围导师与最终邮件
  sources.json           来源元数据，按 source ID 索引
  candidates.md          候选人与匹配理由
  dossiers/<id>.json     每位导师的事实、论文、匹配与缺项
  briefs/<id>.md         论文简报与起步研究建议
  mail-evidence/<id>.md  邮件研究主张 → 来源，个人经历 → 事实
  resume/               简历源文件、许可证和 PDF
  outbox/               发送草稿 JSON 与 TXT
  state.json            确认/发送状态、授权说明、Message-ID
  cache/                仅工作区保存的网页/PDF缓存
```

`profile.json` 必需字段：`name, school, major, year, email, background, availability`；`facts` 是 `{id, text, origin}` 数组，`origin` 标明用户材料或会话；`attachments` 为相对工作区或绝对文件路径数组。`background` 为事实摘要，不能添加 `facts` 或原材料没有的成果。邮箱缺失时仍可调研与准备简历，发信前必须补齐真实地址。

`request.json`：`interests`（关键词数组）、`schools`（学校数组，可空）、`regions`（地区数组，可空）、`stage`、`max_candidates`（默认 10）、`research_years`（默认 3）。没有学校或地区限制时注明跨学校探索；兴趣缺失时先补问，不随机生成研究方向。

`teachers.csv` 必需列：`name,email,research,source_url,motivation`；可选列 `subject,body`。`source_url` 指向已核实的官方联系方式来源。字段内包含逗号/换行时用 CSV 正确引用；可用 Python `csv.DictWriter` 生成，勿手工拼接多行邮件。

`sources.json` 示例结构：

```json
{
  "s1": {
    "url": "https://university.edu/faculty/name",
    "title": "Faculty page",
    "checked_at": "2026-01-01T00:00:00+00:00",
    "retrieved_by": "web",
    "evidence": "支持邮箱/研究方向的短片段"
  }
}
```

`dossiers/<id>.json` 建议结构：`name, institution, official_email, email_source_id, facts, papers, fit, unresolved`。`facts` 为 `{claim, source_ids, status}` 数组。`papers` 每条包含 `title, authors, year, url, doi, source_ids, read_scope, read_sections, summary, limitations`，`read_scope` 取 `metadata/abstract/sections/fulltext`。`fit` 指明引用的个人事实 ID、论文 ID/URL、连接理由和缺口；它是推断而非导师的录取判断。

这些 JSON 是 agent 的工作约定；脚本仅验证自己使用的必要字段，不进行语义真实性验证。缺项记录为未知，不填假事实。示例中的 `.invalid` 邮箱无法发送，用于避免误发。
