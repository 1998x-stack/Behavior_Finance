#!/usr/bin/env python3
"""Build a reproducible, read-only-source course site from catalog/lessons.yaml.

No legacy HTML, Markdown, or PDF files are modified. Generated files go under
site-dist/ (gitignored) and are compared byte-for-byte in verify mode.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import posixpath
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit, urlunsplit

import yaml
from markdown_it import MarkdownIt


ASSETS = ("style.css", "markdown.css", "markdown.js")
STATUS = {"draft", "placeholder", "reviewed"}
KIND = {"lesson", "supplement"}
LEGACY_STUB = re.compile(
    r'\A(#[^\n]+\n+)\s*"""\s*\n\s*Lecture:[^\n]*\n\s*Content:[^\n]*\n\s*"""\s*\n*',
)
MD = MarkdownIt("commonmark", {"html": False, "linkify": False}).enable(
    ["table", "strikethrough"]
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path_in_root(root: Path, value: str) -> Path:
    relative = PurePosixPath(value)
    if (not value or "\\" in value or relative.is_absolute() or
            any(part in (".", "..") for part in relative.parts) or
            not value.endswith(".md")):
        raise ValueError(f"Unsafe Markdown source path: {value!r}")
    resolved_root = root.resolve()
    target = (resolved_root / value).resolve()
    if not target.is_relative_to(resolved_root):
        raise ValueError(f"Source escapes repository root: {value}")
    if not target.is_file():
        raise ValueError(f"Missing source: {value}")
    return target


def load_catalog(root: Path, manifest: Path | None = None) -> list[dict]:
    source = manifest or root / "catalog" / "lessons.yaml"
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Catalog schema_version must be 1")
    sections = data.get("sections")
    items = data.get("lessons")
    if (not isinstance(sections, list) or len(sections) != len(set(sections)) or
            not sections or not isinstance(items, list) or not items):
        raise ValueError("Catalog must have unique sections and lessons")
    ids, paths = set(), set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each lesson must be an object")
        for required in ("id", "title", "source", "section", "kind", "status"):
            if not isinstance(item.get(required), str) or not item[required]:
                raise ValueError(f"Lesson is missing {required}")
        if (not re.fullmatch(r"BF-\d{2}-\d{3}", item["id"]) or
                item["id"] in ids or item["source"] in paths):
            raise ValueError("Duplicate or malformed lesson ID/source")
        ids.add(item["id"])
        paths.add(item["source"])
        if item["section"] not in sections or not item["source"].startswith(item["section"] + "/"):
            raise ValueError("Lesson section/source mismatch")
        if item["status"] not in STATUS or item["kind"] not in KIND:
            raise ValueError("Invalid lesson kind/status")
        path_in_root(root, item["source"])

    # Fail closed on uncatalogued course Markdown files: no silent omissions.
    discovered = {
        f.relative_to(root).as_posix()
        for child in root.iterdir()
        if child.is_dir() and re.match(r"^\d\d_", child.name)
        for f in child.rglob("*.md")
        if f.is_file()
    }
    if discovered != paths:
        raise ValueError("Catalog mismatch: unlisted=" +
                         repr(sorted(discovered - paths)) + ", missing=" +
                         repr(sorted(paths - discovered)))
    return items


def rewrite_internal_markdown_links(tokens: list, source: str, known_sources: set[str]):
    for token in tokens:
        if token.type == "link_open":
            href = token.attrGet("href")
            if href:
                parsed = urlsplit(href)
                if not parsed.scheme and not parsed.netloc and parsed.path.lower().endswith(".md"):
                    relative = unquote(parsed.path)
                    combined = posixpath.normpath(posixpath.join(posixpath.dirname(source), relative))
                    if combined not in known_sources:
                        raise ValueError(f"Broken Markdown link in {source}: {href}")
                    destination = posixpath.relpath(combined[:-3] + ".html",
                                                  posixpath.dirname(source))
                    token.attrSet("href", urlunsplit(("", "", quote(destination, safe="/._-"), parsed.query, parsed.fragment)))
        if token.children:
            rewrite_internal_markdown_links(token.children, source, known_sources)


def render_markdown(text: str, source: str, known_sources: set[str]) -> str:
    match = LEGACY_STUB.match(text)
    if match:
        text = match.group(1) + text[match.end():]
    tokens = MD.parse(text)
    rewrite_internal_markdown_links(tokens, source, known_sources)
    return MD.renderer.render(tokens, MD.options, {})


def template(title: str, body: str, prefix: str = "") -> str:
    prefix = html.escape(prefix, quote=True)
    return (
        "<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n"
        "<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta name=\"generator\" content=\"Behavior_Finance static site v1\">\n"
        f"<title>{html.escape(title)}</title>\n"
        f'<link rel="stylesheet" href="{prefix}markdown.css">\n'
        f'<script defer src="{prefix}markdown.js"></script>\n'
        '<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"></script>\n'
        "</head>\n<body>\n"
        f'<main class="container">{body}</main>\n'
        "</body>\n</html>\n"
    )


def build_files(root: Path) -> dict[str, bytes]:
    lessons = load_catalog(root)
    known = {item["source"] for item in lessons}
    result: dict[str, bytes] = {}
    nav = ['<h1>行为金融学课程目录</h1>', '<p>全部课程均由源 Markdown 生成；“草稿”不代表经过学术审核。</p>']
    sections: list[str] = []
    for item in lessons:
        if item["section"] not in sections:
            sections.append(item["section"])
            nav.append(f'<h2>{html.escape(item["section"])}</h2><ul>')
        else:
            # Within one section, keep a single contiguous list.
            pass
        path = item["source"]
        output = path[:-3] + ".html"
        relative = PurePosixPath(path)
        prefix = "../" * (len(relative.parts) - 1)
        content = path_in_root(root, path).read_text(encoding="utf-8")
        rendered = render_markdown(content, path, known)
        if item["status"] == "placeholder":
            rendered += '<p class="lesson-placeholder">本章尚待编写，当前仅保留课程标题。</p>\n'
        label = {"draft": "草稿", "placeholder": "待编写", "reviewed": "已审核"}[item["status"]]
        header = (f'<nav><a href="{prefix}index.html">返回课程目录</a></nav>\n'
                  f'<p class="lesson-meta" data-lesson-id="{html.escape(item["id"], quote=True)}">'
                  f'{html.escape(label)} · {html.escape(item["id"])}</p>\n')
        result[output] = template(item["title"], header + rendered, prefix).encode("utf-8")
        nav.append(f'<li><a href="{html.escape(quote(output, safe="/._-"), quote=True)}">'
                   f'{html.escape(item["title"])}</a>（{label}）</li>')
        next_section = lessons[lessons.index(item)+1]["section"] if lessons.index(item)+1 < len(lessons) else None
        if next_section != item["section"]:
            nav.append("</ul>")
    result["index.html"] = template("行为金融学 · 课程目录", "\n".join(nav)).encode("utf-8")
    for name in ASSETS:
        source = root / name
        if not source.is_file():
            raise ValueError(f"Missing site asset: {name}")
        result[name] = source.read_bytes()
    inventory = {
        "schema_version": 1,
        "items": [{"path": path, "sha256": sha256(data), "bytes": len(data)}
                  for path, data in sorted(result.items())],
        "source_manifest_sha256": sha256((root / "catalog" / "lessons.yaml").read_bytes())
    }
    result["site-build-manifest.json"] = (
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    return result


def check_site(output: Path, files: dict[str, bytes]):
    if not output.is_dir():
        raise ValueError(f"Generated directory missing: {output}")
    existing = {p.relative_to(output).as_posix()
                for p in output.rglob("*") if p.is_file()}
    if existing != set(files):
        raise ValueError(f"Build output path mismatch: missing={sorted(set(files)-existing)}, extra={sorted(existing-set(files))}")
    for relative, data in files.items():
        if (output / relative).read_bytes() != data:
            raise ValueError(f"Non-deterministic or stale output: {relative}")
    return {"verified": True, "files": len(files), "source_pages": len(files) - len(ASSETS) - 2}


def write_site(output: Path, files: dict[str, bytes]):
    if output.exists():
        if output.is_symlink() or not output.is_dir():
            raise ValueError("Output must be a non-symlink directory")
        # The generator never overwrites a modified or foreign output tree.
        if any(output.iterdir()):
            return check_site(output, files)
    else:
        output.mkdir(parents=True)
    for relative, data in files.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(data)
    return check_site(output, files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "check", "inventory"), nargs="?", default="check")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    output = args.out or root / "site-dist"
    output = output.resolve()
    if output == root or root.is_relative_to(output):
        parser.error("Output directory cannot contain the repository root")
    generated = build_files(root)
    if args.command == "inventory":
        response = {"pages": len(generated) - len(ASSETS) - 1,
                    "lessons": len(load_catalog(root)), "out": str(output)}
    elif args.command == "build":
        response = write_site(output, generated)
    else:
        response = check_site(output, generated)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, yaml.YAMLError) as error:
        print(f"site builder failed: {error}", file=sys.stderr)
        raise SystemExit(1)
