#!/usr/bin/env python3
"""Offline source/HTML parity and course navigation guard. No third-party dependencies."""
from __future__ import annotations
import argparse, re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
COURSE_DIRS = tuple(sorted(ROOT.glob("0[1-4]_*")))
LESSON = re.compile(r"_([1-4])\.\d+_")
BANNED = ("对应的 Python 文件不存在", "讲义介绍了", "讲义指出", "本节主要讨论")

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1 = []
        self.ids = []
        self.hrefs = []
        self.source = []
        self.text = []
        self._h1 = False
        self._skip = 0
        self.has_svg_title = False
        self.has_svg_desc = False
        self.figure_caption = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a: self.ids.append(a["id"])
        if tag == "a" and a.get("href"): self.hrefs.append(a["href"])
        if tag == "h1": self._h1 = True
        if tag in ("script","style"): self._skip += 1
        if tag == "title" and self._skip == 0: self.has_svg_title = True
        if tag == "desc": self.has_svg_desc = True
        if tag == "figcaption": self.figure_caption = True
    def handle_endtag(self, tag):
        if tag == "h1": self._h1 = False
        if tag in ("script","style"): self._skip = max(0,self._skip-1)
    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)
            if self._h1: self.h1.append(data)

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def lesson_files():
    for directory in COURSE_DIRS:
        for html in sorted(directory.glob("*.html")):
            if LESSON.search(html.name): yield html

def audit(root: Path = ROOT, strict: bool = True):
    errors=[]; warnings=[]; checked=0; parity=0
    for page in lesson_files():
        checked += 1
        code=page.read_text(encoding="utf-8")
        parsed=Document();parsed.feed(code)
        if len(parsed.h1) == 0 or code.count("<h1") != 1: errors.append(f"{page}: H1 is not unique")
        if len(set(parsed.ids)) != len(parsed.ids): errors.append(f"{page}: repeated id")
        if "course-sequence" not in code: errors.append(f"{page}: missing chapter navigation")
        if "../assets/course.css" not in code: errors.append(f"{page}: missing shared CSS")
        visible=norm(" ".join(parsed.text))
        for banned in BANNED:
            if banned in visible: errors.append(f"{page}: banned placeholder {banned}")
        for link in parsed.hrefs:
            target=urlsplit(link)
            if target.scheme or link.startswith("//") or link.startswith("mailto:"): continue
            path=unquote(target.path)
            resolved=(page.parent / path).resolve() if path else page
            if path and not resolved.is_file(): errors.append(f"{page}: broken link {link}")
            if target.fragment and (not path or resolved==page):
                if unquote(target.fragment) not in parsed.ids: errors.append(f"{page}: missing anchor {link}")
        stem=page.with_suffix(".md")
        if page.parent.name.startswith("04_"):
            if not stem.exists(): errors.append(f"{page}: missing paired Markdown");continue
            md=stem.read_text(encoding="utf-8")
            paragraphs=[norm(p) for p in re.split(r"\n\s*\n",md) if p.strip()]
            paragraphs=[p.removeprefix("# ").removeprefix("## ").removeprefix("> ") for p in paragraphs]
            for block in paragraphs:
                if block not in visible:
                    errors.append(f"{page}: source paragraph not in HTML: {block[:42]}")
            if not parsed.has_svg_title or not parsed.has_svg_desc or not parsed.figure_caption:
                errors.append(f"{page}: SVG missing title/description/caption")
            if re.search(r"<script[^>]+src=['\"]https?://",code): errors.append(f"{page}: remote script in lesson")
            parity+=1
        elif stem.exists():
            markdown=stem.read_text(encoding="utf-8")
            header=markdown.splitlines()[0].lstrip("# ").strip()
            if header not in visible:
                warnings.append(f"{page.relative_to(root)}: legacy Markdown and HTML heading differ; full reconciliation not established")
    return checked,parity,errors,warnings

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--strict-legacy",action="store_true")
    args=parser.parse_args()
    checked,parity,errors,warnings=audit()
    print(f"Reviewed {checked} lessons; verified module-four Markdown/HTML content parity for {parity} lessons.")
    for msg in warnings: print("LEGACY-DRIFT:",msg)
    for msg in errors: print("ERROR:",msg,file=sys.stderr)
    if args.strict_legacy and warnings: errors.extend(warnings)
    if errors: sys.exit(1)
