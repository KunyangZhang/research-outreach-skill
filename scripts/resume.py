#!/usr/bin/env python3
"""从纯文字 cv.json 生成学术简历，按需用 XeLaTeX 编译。"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "cv"
ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
           "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def escape(value):
    return "".join(ESCAPES.get(c, c) for c in str(value)).replace("\n", " ")


def render(workspace, compile_pdf=False):
    cv = json.loads((workspace / "cv.json").read_text(encoding="utf-8"))
    for key in ("name", "email", "sections"):
        if not cv.get(key):
            raise ValueError(f"cv.json 缺少 {key}")
    if cv.get("language", "zh") not in ("zh", "en"):
        raise ValueError("language 只支持 zh 或 en")
    section_lines = []
    for section in cv["sections"]:
        if not section.get("title") or not isinstance(section.get("items"), list):
            raise ValueError("简历每节需要 title 和 items 数组")
        if not section["items"]:
            continue
        section_lines.extend([r"\block{" + escape(section["title"]) + "}", r"\begin{itemize}"])
        section_lines.extend(r"\item " + escape(item) for item in section["items"])
        section_lines.append(r"\end{itemize}")
    template = (ASSETS / "resume.tex").read_text(encoding="utf-8")
    replacements = {"@@LANGUAGE@@": r"\usepackage[UTF8,fontset=fandol]{ctex}" if cv.get("language", "zh") == "zh" else "",
                    "@@NAME@@": escape(cv["name"]), "@@EMAIL@@": escape(cv["email"]),
                    "@@SUBTITLE@@": escape(cv.get("subtitle", "")),
                    "@@SECTIONS@@": "\n".join(section_lines)}
    # 单次替换避免个人资料中的标记再次被解释。
    import re
    tex = re.sub(r"@@(?:LANGUAGE|NAME|EMAIL|SUBTITLE|SECTIONS)@@", lambda m: replacements[m[0]], template)
    output = workspace / "resume"
    output.mkdir(parents=True, exist_ok=True)
    for name in ("cv.sty", "onepage.sty", "LICENSE.upstream.md", "UPSTREAM.json"):
        shutil.copy2(ASSETS / name, output / name)
    (output / "resume.tex").write_text(tex, encoding="utf-8")
    # 新源文件没有重新成功编译时不能留下看似有效的旧 PDF。
    (output / "resume.pdf").unlink(missing_ok=True)
    print(f"已生成 {output / 'resume.tex'}")
    if compile_pdf:
        engine = shutil.which("xelatex")
        if not engine:
            raise ValueError("未找到 xelatex；源文件已生成，PDF 尚未生成")
        command = [engine, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", "resume.tex"]
        try:
            result = subprocess.run(command, cwd=output, capture_output=True, text=True, timeout=90)
        except subprocess.TimeoutExpired as exc:
            (output / "resume.pdf").unlink(missing_ok=True)
            raise ValueError("编译超时；PDF 未完成") from exc
        if result.returncode:
            (output / "resume.pdf").unlink(missing_ok=True)
            raise ValueError(f"简历编译失败，查看 {output / 'resume.log'}")
        print(f"已编译 {output / 'resume.pdf'}；仍需检查文字与布局")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--compile", action="store_true", dest="compile_pdf")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    import fcntl
    with (workspace / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            render(workspace, args.compile_pdf)
        except (ValueError, OSError) as exc:
            parser.exit(1, f"简历操作失败：{exc}\n")


if __name__ == "__main__":
    main()
