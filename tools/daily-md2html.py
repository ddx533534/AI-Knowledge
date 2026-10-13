#!/usr/bin/env python3
"""把 04-Daily 的 markdown 日报转成单文件浅色 HTML（无外部依赖）。

用法：
    python3 tools/daily-md2html.py                    # 默认转当天日期的 04-Daily/<今天>.md
    python3 tools/daily-md2html.py 2026-10-13         # 指定日期
    python3 tools/daily-md2html.py path/to/x.md       # 指定文件（输出同名 .html）

只支持日报用到的 markdown 子集：标题、段落、无序/有序列表、引用、围栏代码、
分隔线、表格、图片，以及行内的 `code`、**加粗**、[文字](链接)。

图片按相对路径解析（相对 md 文件所在目录）。SVG 直接把源码内联进 HTML；
png/jpg/gif/webp/avif 转成 base64 data URI 内联。两种都不产生外部依赖，
HTML 仍是单文件。可用 `![说明](assets/x.png "w=440")` 限制最大显示宽度。
"""
import base64
import datetime
import html
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY_DIR = os.path.join(REPO, "04-Daily")

LINK_RE = re.compile(r"\[([^\]\n]+)\]\((https?://[^)\s]+)\)")
IMG_RE = re.compile(r"^!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+\"([^\"]*)\")?\s*\)$")
WIDTH_RE = re.compile(r"w=(\d+)")
MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".avif": "image/avif",
}
PH = "\x00%d\x00"


def render_figure(alt, src, hint, base_dir):
    """把一张图片转成 <figure>。SVG 内联，位图 base64 内联。"""
    cap = "<figcaption>%s</figcaption>" % inline(alt) if alt else ""
    path = os.path.normpath(os.path.join(base_dir, src))
    if not os.path.isfile(path):
        return '<figure class="fig fig-missing"><figcaption>图片缺失：%s</figcaption></figure>' % esc(src)
    m = WIDTH_RE.search(hint or "")
    style = ' style="max-width:%spx"' % m.group(1) if m else ""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        with open(path, encoding="utf-8") as f:
            svg = f.read()
        svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
        svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg, flags=re.I).strip()
        return '<figure class="fig"><div class="fig-box"%s>%s</div>%s</figure>' % (style, svg, cap)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return '<figure class="fig"><img src="data:%s;base64,%s" alt="%s"%s>%s</figure>' % (
        MIME.get(ext, "application/octet-stream"),
        b64,
        html.escape(alt, quote=True),
        style,
        cap,
    )


def esc(t: str) -> str:
    return html.escape(t, quote=False)


def inline(t: str) -> str:
    """行内元素：先摘出链接，再转义，最后回填 <a>。"""
    links = []

    def stash(m):
        links.append((m.group(1), m.group(2)))
        return PH % (len(links) - 1)

    t = LINK_RE.sub(stash, t)
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    for i, (text, url) in enumerate(links):
        a = '<a href="%s" target="_blank" rel="noopener">%s</a>' % (
            html.escape(url, quote=True),
            esc(text),
        )
        t = t.replace(PH % i, a)
    return t


def is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def render_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head = cells[0]
    body = cells[2:] if len(cells) > 1 else []
    out = ['<div class="tw"><table>', "<thead><tr>"]
    for c in head:
        out.append("<th>%s</th>" % inline(c))
    out.append("</tr></thead>")
    if body:
        out.append("<tbody>")
        for row in body:
            out.append("<tr>")
            for c in row:
                out.append("<td>%s</td>" % inline(c))
            out.append("</tr>")
        out.append("</tbody>")
    out.append("</table></div>")
    return "\n".join(out)


def convert(md: str, base_dir: str = ".") -> str:
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()

        if s.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % esc("\n".join(buf)))
            continue

        if s == "---":
            out.append("<hr>")
            i += 1
            continue

        if s.startswith("#"):
            m = re.match(r"^(#+)\s+(.*)$", s)
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2)), lvl))
            i += 1
            continue

        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(
                "<blockquote>%s</blockquote>" % "<br>".join(inline(b) for b in buf)
            )
            continue

        if is_table_row(line):
            buf = []
            while i < n and is_table_row(lines[i]):
                buf.append(lines[i])
                i += 1
            out.append(render_table(buf))
            continue

        if s.startswith("- "):
            buf = []
            while i < n and lines[i].strip().startswith("- "):
                buf.append(inline(lines[i].strip()[2:]))
                i += 1
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % b for b in buf))
            continue

        if re.match(r"^\d+\.\s", s):
            buf = []
            while i < n and re.match(r"^\d+\.\s", lines[i].strip()):
                buf.append(inline(re.sub(r"^\d+\.\s", "", lines[i].strip())))
                i += 1
            out.append("<ol>%s</ol>" % "".join("<li>%s</li>" % b for b in buf))
            continue

        if s == "":
            i += 1
            continue

        img = IMG_RE.match(s)
        if img:
            out.append(render_figure(img.group(1), img.group(2), img.group(3), base_dir))
            i += 1
            continue

        out.append("<p>%s</p>" % inline(s))
        i += 1
    return "\n".join(out)


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 日报 · __DATE__</title>
<style>
  :root {
    --bg: #fbfbfc;
    --panel: #ffffff;
    --ink: #1c1f24;
    --ink-soft: #4a5158;
    --line: #e5e7eb;
    --line-soft: #eef0f3;
    --accent: #2f5d8a;
    --accent-soft: #eef3f8;
    --code-bg: #f4f5f7;
    --quote-bg: #f7f8fa;
  }
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font: 16px/1.8 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
          "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  }
  .wrap { max-width: 880px; margin: 0 auto; padding: 40px 22px 96px; }
  h1 { font-size: 30px; line-height: 1.35; margin: 0 0 18px; letter-spacing: .2px; }
  h2 {
    font-size: 22px; line-height: 1.45; margin: 52px 0 18px;
    padding-top: 20px; border-top: 1px solid var(--line);
  }
  h3 { font-size: 18px; line-height: 1.5; margin: 34px 0 12px; color: #14171b; }
  p { margin: 12px 0; }
  strong { color: #10131a; font-weight: 600; }
  a { color: var(--accent); text-decoration: none; border-bottom: 1px solid rgba(47,93,138,.28); }
  a:hover { border-bottom-color: var(--accent); }
  hr { border: 0; border-top: 1px solid var(--line); margin: 40px 0; }
  blockquote {
    margin: 0 0 8px; padding: 14px 18px; background: var(--quote-bg);
    border-left: 3px solid #c9d4e0; border-radius: 4px;
    color: var(--ink-soft); font-size: 15px;
  }
  code {
    background: var(--code-bg); border: 1px solid var(--line-soft);
    border-radius: 4px; padding: 1px 5px; font-size: 13.5px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    word-break: break-word;
  }
  pre {
    background: var(--code-bg); border: 1px solid var(--line-soft);
    border-radius: 6px; padding: 14px 16px; overflow-x: auto; margin: 16px 0;
  }
  pre code { background: none; border: 0; padding: 0; font-size: 13.5px; line-height: 1.7; }
  ul, ol { margin: 12px 0; padding-left: 24px; }
  li { margin: 8px 0; }
  .tw { overflow-x: auto; margin: 18px 0; }
  table { border-collapse: collapse; width: 100%; font-size: 14.5px; background: var(--panel); }
  th, td { border: 1px solid var(--line); padding: 9px 11px; text-align: left; vertical-align: top; }
  th { background: var(--accent-soft); color: #1b3a56; font-weight: 600; white-space: nowrap; }
  tbody tr:nth-child(even) { background: #fafbfc; }
  .fig { margin: 24px 0; }
  .fig-box, .fig img { display: block; width: 100%; max-width: 680px; margin: 0 auto; }
  .fig img { height: auto; }
  .fig svg { display: block; width: 100%; height: auto; }
  .fig figcaption {
    margin-top: 9px; text-align: center; font-size: 13.5px; color: var(--ink-soft);
  }
  .fig-missing {
    border: 1px dashed #d9a3a3; border-radius: 6px; padding: 12px; color: #a32d2d;
  }
  @media (max-width: 620px) {
    body { font-size: 15.5px; }
    .wrap { padding: 26px 16px 72px; }
    h1 { font-size: 25px; }
    h2 { font-size: 20px; }
    th, td { padding: 7px 9px; font-size: 13.5px; }
  }
</style>
</head>
<body>
<div class="wrap">
__BODY__
</div>
</body>
</html>
"""


def resolve(arg: str | None) -> tuple[str, str]:
    if not arg:
        date = datetime.date.today().isoformat()
        src = os.path.join(DAILY_DIR, date + ".md")
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", arg):
        src = os.path.join(DAILY_DIR, arg + ".md")
    else:
        src = os.path.abspath(arg)
    if not os.path.isfile(src):
        raise SystemExit("找不到源文件：%s" % src)
    dst = os.path.splitext(src)[0] + ".html"
    return src, dst


def main() -> None:
    src, dst = resolve(sys.argv[1] if len(sys.argv) > 1 else None)
    with open(src, encoding="utf-8") as f:
        md = f.read()
    body = convert(md, os.path.dirname(src))
    date = os.path.splitext(os.path.basename(src))[0]
    with open(dst, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.replace("__BODY__", body).replace("__DATE__", date))
    print("wrote", dst, len(body), "chars body")


if __name__ == "__main__":
    sys.exit(main())
