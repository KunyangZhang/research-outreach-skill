# 研究简历

## 模板来源

来源：[pmichaillat/latex-cv](https://github.com/pmichaillat/latex-cv)，MIT License，上游 commit 见 `assets/cv/UPSTREAM.json`。本包保留 `cv.sty`、`onepage.sty` 与许可证；`cv.sty` 的字体分支为中英文 XeLaTeX 做了适配，原版可从该 commit 获取。内容模板为本 skill 编写，不包含上游示例人物资料。

## 填写

在工作区创建 `cv.json`：

```json
{
  "name": "真实姓名",
  "email": "student@school.edu",
  "language": "zh",
  "subtitle": "学校 · 专业 · 年级",
  "sections": [
    {"title": "教育背景", "items": ["学校、专业、时间；仅列已确认的成绩或排名"]},
    {"title": "科研与项目", "items": ["项目名称、个人贡献、使用方法、可核实结果"]},
    {"title": "技能", "items": ["能够解释和实际使用的技能"]}
  ]
}
```

脚本会将字段作为纯文字转义，不能注入自定义 LaTeX 命令。需要复杂版式时由 agent 编辑生成的 `.tex`；再次运行生成器会覆盖它。每项经历对应 `profile.json.facts` 中的事实或用户已提供材料。针对不同导师可以重排真实经历，但不得改变事实。

```bash
python3 <skill目录>/scripts/resume.py --workspace <申请工作区> --compile
```

默认使用 XeLaTeX；中文加载 ctex 的 Fandol 字体集，英文使用 TeX 自带字体。依赖：TeX Live/MiKTeX 中的 xelatex、ctex、geometry、enumitem、titlesec 等宏包。未安装时保留 `.tex`、样式与许可证，报告缺项。中文模板需 XeLaTeX，不能用 pdfLaTeX。

输出 `resume/resume.tex`、`resume/resume.pdf`。编译后提取文字核对姓名、邮箱与主要经历，检查页数和布局溢出。样式偏向一页，但内容过多时可生成多页；通过删去低相关内容和精炼句子调整，不把字号无限缩小。

默认不加入照片、身份证、家庭住址或不必要的个人信息。出版物只列真实作者身份和状态，课程项目与正式研究分开描述。
