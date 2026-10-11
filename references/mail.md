# 邮件与发送

## 写信

中文通常 250–450 字、英文通常 150–220 词，按用户要求调整。主题含身份与申请意图。正文顺序：身份 → 一个具体课题连接 → 相关经历与投入时间 → 询问交流/进组机会。研究连接引自 dossier；个人贡献引自 profile 或简历原材料。

对论文仅读摘要时写“我了解到您在……方向的工作”；若用户未确认亲自阅读，不写“我读过”。招生未确认时用“想咨询是否有适合的机会”。尽量一封邮件一个收件人，不用抄送批量群发。完整正文填入 `teachers.csv.body`，否则脚本会使用基础中文模板。

发送前核对：老师身份与官方邮箱、主题与正文称谓、研究主张来源、申请人经历、简历附件和时间承诺。与用户已有明确授权对应；授权不足时先呈现具体邮件包再询问，不将本 skill 的调用自动转换为发送许可。

## SMTP 工作流

```bash
python3 <skill目录>/scripts/mail.py --workspace <工作区> draft
python3 <skill目录>/scripts/mail.py --workspace <工作区> approve <ID> --authorization-note '<已有用户授权>'
python3 <skill目录>/scripts/mail.py --workspace <工作区> send-approved --interval 60
python3 <skill目录>/scripts/mail.py --workspace <工作区> status
```

`approve` 记录操作者提交的授权说明及邮件哈希，不验证操作者身份，也不替代对话授权判断。JSON 草稿是最终发送对象；TXT 为预览快照。修改正文/收件人/主题后旧确认失效；附件变化需重新生成草稿。重复运行 `draft` 会覆盖本地草稿，发送状态仍保留。

通过环境变量提供 `SMTP_HOST`、`SMTP_USER`、`SMTP_PASSWORD`，默认 SSL/465；可用 `SMTP_MODE=starttls` 与 `SMTP_PORT=587`。不要把实际凭据写入仓库、日志或聊天回复。脚本没有 OAuth 实现；Gmail/Outlook/学校邮箱具体是否允许密码认证，以账号与服务商当前配置为准，不推测。

批量发送默认每分钟一封，错误即停止。脚本使用文件锁、邮件哈希和落盘状态防止同一邮件重复发送。`sent` 表示服务器接受，不能作为送达/已读证据。`uncertain` 或 `sending` 表示需核查服务器侧日志或可用邮箱记录；SMTP 不保证“恰好一次”，未核实前不能重置并重发。认证失败前未进入发送状态，可修复配置后重试。

回复监测优先用已连接邮箱工具，按发信 Message-ID、会话、发件人核对，不仅凭“Re:”主题。未接入邮箱时无法判断是否回复，不自动跟进。调度只有实际安装且得到授权才算启用；本 skill 不包含常驻进程。
