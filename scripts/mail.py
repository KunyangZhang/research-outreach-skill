#!/usr/bin/env python3
"""科研进组邮件工作流；仅使用 Python 标准库。"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import formataddr, make_msgid, parseaddr, formatdate
import mimetypes
import math
from datetime import datetime, timezone


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def email_address(value):
    value = value.strip()
    if "\n" in value or "\r" in value or parseaddr(value)[1] != value or "@" not in value:
        raise ValueError(f"邮箱格式不正确：{value!r}")
    return value


def digest(draft):
    return hashlib.sha256(json.dumps(draft, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def attachments(base, profile):
    result = []
    for name in profile.get("attachments", []):
        path = (base / name).resolve()
        if not path.is_file():
            raise ValueError(f"附件不存在：{path}")
        result.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return result


def draft_all(base):
    profile = read_json(base / "profile.json")
    for key in ("name", "school", "major", "year", "background", "availability", "email"):
        if not str(profile.get(key, "")).strip():
            raise ValueError(f"请填写 profile.json 的 {key}")
    sender = email_address(profile["email"])
    files = attachments(base, profile)
    with (base / "teachers.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    planned, seen = [], set()
    for row in rows:
        for key in ("name", "email", "research", "source_url", "motivation"):
            if not str(row.get(key, "")).strip():
                raise ValueError(f"导师记录缺少 {key}：{row.get('name', '')}")
        recipient = email_address(row["email"])
        if recipient.lower() in seen:
            raise ValueError(f"导师邮箱重复：{recipient}")
        seen.add(recipient.lower())
        identifier = hashlib.sha256(recipient.lower().encode()).hexdigest()[:16]
        body = (
            f"{row['name']}老师您好：\n\n"
            f"我是{profile['school']}{profile['major']}{profile['year']}的{profile['name']}，"
            "希望咨询是否有机会加入您的课题组参与科研。\n\n"
            f"我了解到您从事{row['research']}方向的研究。{row['motivation']}\n\n"
            f"我的相关背景是：{profile['background']}\n\n"
            f"我可以投入的时间是：{profile['availability']}。"
            "如果课题组有适合我的科研机会，希望能与您进一步交流。"
            + ("随信附上个人材料，供您参考。" if files else "")
            + f"\n\n感谢您的时间！\n{profile['name']}\n{sender}\n"
        )
        if row.get("body", "").strip():
            body = row["body"]
        draft = {"id": identifier, "sender": sender, "sender_name": profile["name"],
                 "recipient": recipient, "teacher": row["name"],
                 "subject": row.get("subject", "").strip() or f"科研进组咨询｜{profile['school']}{profile['name']}",
                 "body": body, "source_url": row["source_url"], "attachments": files}
        # 先校验全部记录，再写入，避免一半成功一半失败。
        make_message(draft)
        planned.append(draft)
    for draft in planned:
        identifier = draft["id"]
        write_json(base / "outbox" / f"{identifier}.json", draft)
        (base / "outbox" / f"{identifier}.txt").write_text(
            f"ID: {identifier}\n收件人: {draft['recipient']}\n主题: {draft['subject']}\n"
            f"导师信息来源: {draft['source_url']}\n\n{draft['body']}", encoding="utf-8")
        print(f"已生成 {identifier}：{draft['teacher']} <{draft['recipient']}>")


def load_draft(base, identifier):
    if len(identifier) != 16 or any(c not in "0123456789abcdef" for c in identifier):
        raise ValueError("请使用 draft 输出的 16 位邮件 ID")
    return read_json(base / "outbox" / f"{identifier}.json")


def state_for(base):
    path = base / "state.json"
    return read_json(path) if path.exists() else {}


def make_message(draft):
    message = EmailMessage()
    message["From"] = formataddr((draft["sender_name"], email_address(draft["sender"])))
    message["To"] = email_address(draft["recipient"])
    message["Subject"] = draft["subject"]
    message["Message-ID"] = make_msgid()
    message["Date"] = formatdate(localtime=True)
    message.set_content(draft["body"])
    for attachment in draft["attachments"]:
        path = Path(attachment["path"])
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != attachment["sha256"]:
            raise ValueError(f"附件已修改，请重新生成草稿：{path.name}")
        kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        main, sub = kind.split("/", 1)
        message.add_attachment(data, maintype=main, subtype=sub, filename=path.name)
    return message


def approve(base, identifier, authorization_note):
    if not authorization_note.strip():
        raise ValueError("请记录本次发送对应的用户授权说明")
    draft = load_draft(base, identifier)
    make_message(draft)
    state = state_for(base)
    previous = state.get(identifier, {})
    if previous.get("status") in ("sent", "sending", "uncertain"):
        raise ValueError("此邮件已发送或发送结果待核对，请查看 state.json")
    state[identifier] = {"status": "approved", "digest": digest(draft),
                         "authorization_note": authorization_note,
                         "approved_at": datetime.now(timezone.utc).isoformat()}
    write_json(base / "state.json", state)
    print(f"已确认 {identifier}，修改草稿后需要重新确认。")


def send(base, identifier):
    draft = load_draft(base, identifier)
    state = state_for(base)
    record = state.get(identifier, {})
    if record.get("status") != "approved" or record.get("digest") != digest(draft):
        raise ValueError("请先检查当前草稿，并运行 approve 确认")
    if draft["sender"].lower().endswith(".invalid") or draft["recipient"].lower().endswith(".invalid"):
        raise ValueError("请先替换示例邮箱")
    message = make_message(draft)
    host = os.environ.get("SMTP_HOST", "")
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    mode = os.environ.get("SMTP_MODE", "ssl").lower()
    if not all((host, user, password)):
        raise ValueError("请设置 SMTP_HOST、SMTP_USER、SMTP_PASSWORD 环境变量")
    if mode not in ("ssl", "starttls"):
        raise ValueError("SMTP_MODE 只支持 ssl 或 starttls")
    port = int(os.environ.get("SMTP_PORT", "465" if mode == "ssl" else "587"))
    context = ssl.create_default_context()
    if mode == "ssl":
        connection = smtplib.SMTP_SSL(host, port, timeout=30, context=context)
    else:
        connection = smtplib.SMTP(host, port, timeout=30)
    try:
        if mode == "starttls":
            connection.starttls(context=context)
        connection.login(user, password)
        # 发信前落盘。网络中断后不自动重发，以免同一导师收到重复邮件。
        record.update(status="sending", message_id=message["Message-ID"])
        write_json(base / "state.json", state)
        try:
            connection.send_message(message)
        except Exception:
            record["status"] = "uncertain"
            write_json(base / "state.json", state)
            raise
        record.update(status="sent", sent_at=datetime.now(timezone.utc).isoformat())
        write_json(base / "state.json", state)
    finally:
        connection.close()
    print(f"SMTP 服务器已接受邮件：{draft['recipient']}（不代表已送达或已读）")


def main():
    parser = argparse.ArgumentParser(description="科研进组邮件：生成 → 确认 → 发送")
    parser.add_argument("--workspace", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("draft")
    sub.add_parser("status")
    batch = sub.add_parser("send-approved", help="依次自动发送已确认的邮件")
    batch.add_argument("--interval", type=float, default=60, help="两封邮件之间的秒数，默认 60")
    for command in ("approve", "send"):
        child = sub.add_parser(command)
        child.add_argument("id")
        if command == "approve":
            child.add_argument("--authorization-note", required=True)
    args = parser.parse_args()
    base = args.workspace.resolve()
    # 防止多个发送进程同时读取同一状态并重复发送。
    import fcntl
    base.mkdir(parents=True, exist_ok=True)
    with (base / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            if args.command == "draft":
                draft_all(base)
            elif args.command == "status":
                print(json.dumps(state_for(base), ensure_ascii=False, indent=2))
            elif args.command == "approve":
                approve(base, args.id, args.authorization_note)
            elif args.command == "send-approved":
                if not math.isfinite(args.interval) or args.interval < 0:
                    raise ValueError("发送间隔必须是非负有限秒数")
                identifiers = [key for key, value in state_for(base).items()
                               if value.get("status") == "approved"]
                # 批量发送之前检查整批草稿，避免第二封已修改而第一封先发出去。
                for identifier in identifiers:
                    draft = load_draft(base, identifier)
                    if state_for(base)[identifier]["digest"] != digest(draft):
                        raise ValueError(f"草稿 {identifier} 已修改，请重新确认")
                    make_message(draft)
                for index, identifier in enumerate(identifiers):
                    if index:
                        time.sleep(args.interval)
                    send(base, identifier)
                if not identifiers:
                    print("没有待发送的已确认邮件。")
            else:
                send(base, args.id)
        except (ValueError, OSError, smtplib.SMTPException) as exc:
            parser.exit(1, f"操作失败：{exc}\n")


if __name__ == "__main__":
    main()
