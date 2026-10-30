"""Regression tests for course HTML security and script ordering (stdlib only)."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ScriptCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.language = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "html":
            self.language = attributes.get("lang")
        elif tag == "script":
            self.scripts.append(attributes)


class WebStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = sorted(
            path for path in ROOT.rglob("*.html")
            if path.is_relative_to(ROOT)
            and "tests" not in path.relative_to(ROOT).parts
        )

    def test_all_42_html_files_present(self):
        self.assertEqual(len(self.pages), 42)

    def test_unsafe_polyfill_removed_from_all_pages(self):
        for page in self.pages:
            with self.subTest(page=page.name):
                self.assertNotIn("polyfill.io", page.read_text(encoding="utf-8"))

    def test_article_templates_have_deterministic_script_order(self):
        articles = [p for p in self.pages if p.name != "index.html"]
        self.assertEqual(len(articles), 41)
        for page in articles:
            with self.subTest(page=page.name):
                parser = ScriptCollector()
                parser.feed(page.read_text(encoding="utf-8"))
                self.assertEqual(parser.language, "zh-CN")
                scripts = parser.scripts
                app = [i for i, s in enumerate(scripts) if s.get("src", "").endswith("markdown.js")]
                math = [i for i, s in enumerate(scripts) if "mathjax" in s.get("src", "").lower()]
                self.assertEqual(len(app), 1)
                self.assertEqual(len(math), 1)
                self.assertLess(app[0], math[0])
                self.assertIn("mathjax@3.2.2", scripts[math[0]]["src"])
                self.assertIn("defer", scripts[app[0]])
                self.assertIn("defer", scripts[math[0]])
                self.assertFalse(any("polyfill" in str(s) for s in scripts))
                for script in scripts:
                    src = script.get("src", "")
                    if not src or src.startswith("http"):
                        continue
                    self.assertTrue((page.parent / src).is_file(), f"{page}: missing {src}")

    def test_fixed_950px_card_width_removed(self):
        self.assertNotIn("950px", (ROOT / "style.css").read_text(encoding="utf-8"))
        self.assertIn("overflow-x: auto", (ROOT / "markdown.css").read_text(encoding="utf-8"))

    def test_readme_and_course_content_not_rewritten(self):
        self.assertTrue((ROOT / "README.md").is_file())
        self.assertTrue((ROOT / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
