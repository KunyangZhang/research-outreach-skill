# 组合方式

本包不复制 ARS 的工作流、角色提示、论文核验脚本，也不把依赖包装成自己实现的研究引擎。依赖源见 `dependencies.json`。已安装依赖的入口由当前 skill/插件目录提供；本地可执行 `scripts/dependencies.py --mode research`，额外路径用 `--skills-root <目录>`。

## 功能分工

| 工作 | 复用对象 | 本包负责的连接 |
|---|---|---|
| 找老师、核对官方邮箱/招生 | 宿主搜索与浏览工具 | 申请范围、候选表和时效 |
| 近期论文检索与比较 | `academic-research-suite` → `deep-research` → `three-way-scan` | 提供导师身份、方向、时间范围；转换成导师 dossier |
| 核验研究主张 | ARS → `deep-research` → `fact-check` | 提交要用于邮件的具体主张与来源；保留核验结论 |
| 阅读 PDF、简历版面检查 | 已有 `pdf` skill（可选）/宿主 PDF 阅读工具 | 标记阅读范围、确认最终附件 |
| 简历版式 | `pmichaillat/latex-cv` | 填充真实材料、中英文适配 |
| 发信与回复检查 | 已连接邮箱工具；无连接时本包 SMTP 辅助脚本 | 用户授权、内容哈希、发送状态和去重 |
| 安装缺失依赖 | 已有 `skill-installer` | 给出明确仓库、版本与路径，不自行另写安装器 |

## ARS 调用

先读 `academic-research-suite/SKILL.md`，按其 router 读 `ars/deep-research/WORKFLOW.md`；仅加载当前模式需要的角色资源。

论文比较使用 `three-way-scan`，根据该 workflow 加载 `bibliography_agent.md` 与 `source_verification_agent.md`。邮件主张核验使用 `fact-check` 与 `source_verification_agent.md`。不因申请任务默认启动完整论文写作、PRISMA 或所有研究角色。role 可以在当前上下文执行；是否派发独立子 agent 由当前会话授权与环境规则决定。

交接提示示例：

> 使用 $academic-research-suite 的 deep-research / three-way-scan。目标是为科研进组申请理解某位导师的近期工作，不是写论文。导师：{姓名、当前学校、官网}；申请方向：{关键词}；时间范围：{近年区间}。检索与该导师身份匹配的 2–3 篇原始论文，返回标题、作者、年份、DOI/原始链接、WHY/HOW/WHAT、实际所读范围、限制和不确定项。使用宿主浏览工具，不调用外部模型，不执行实验，不代表申请人已读论文。按用户要求使用简体中文。产物保存到 {工作区}。

> 使用 deep-research / fact-check 核对下列准备写进邮件的研究主张：{主张列表}。逐条给出来源、支持范围、核验状态和应删除/收窄的表述；不能核实的保持未知。个人经历由用户材料支持，不用互联网补造。

对 ARS 返回结果保持原来的未核实/部分阅读/不可获取标记；再增加“与个人事实 p1/p2 的关联”与“可能的入门任务”作为明确的推断。依赖 skill 的外部模型、程序化核验、人工阅读记录与额外授权边界仍适用；普通自动调研不隐含开启这些功能。

## 版本与缺失处理

已在本机 ARS 3.22.0 验证入口与路径。其它版本先检查模式和文件是否存在；路径变化时通过依赖 router 找新的入口，不默认兼容。`dependencies.py` 只检查文件/版本并报告，不执行或安装依赖，不改变模型、hooks 或权限。

若用户需要安装，在读取已有 `skill-installer` 后使用其脚本：

```bash
python3 <skill-installer目录>/scripts/install-skill-from-github.py \
  --repo Imbad0202/academic-research-skills-codex \
  --ref v3.22.0 --path skills/academic-research-suite
```

安装权限以当前用户请求为准；如用户指定 GitHub 凭据来源，遵守其凭据规则。不要让安装器生成重复已有依赖。`pdf` 是可选依赖，不需要为了默认工作流强制安装。

本包原创部分 MIT，ARS 依赖具有自己的 CC BY-NC 4.0 许可；不将依赖许可改称 MIT，也不将组合声明为可不受限制商用。ARS 不随本包分发。
