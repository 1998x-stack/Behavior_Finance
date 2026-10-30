"""Deterministic site builder tests against synthetic and real course inputs."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_site as site


class SiteBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        (self.root / "catalog").mkdir(parents=True)
        (self.root / "00_课程").mkdir()
        (self.root / "00_课程" / "00_第一章.md").write_text(
            '# 第一章\n\n正文 **重要**。\n\n| 甲 | 乙 |\n|---|---|\n| 1 | 2 |\n\n[第二章](01_第二章.md#anchor)\n',
            encoding="utf-8")
        (self.root / "00_课程" / "01_第二章.md").write_text(
            '# 第二章\n\n<script>alert("xss")</script>\n\n' + "~~~python\nprint(123)\n~~~\n",
            encoding="utf-8")
        self.write_catalog()
        for name in site.ASSETS:
            shutil.copyfile(ROOT / name, self.root / name)

    def write_catalog(self, second_path="00_课程/01_第二章.md"):
        import yaml
        items = [
            {"id": "BF-00-001", "section": "00_课程", "title": "第一章",
             "source": "00_课程/00_第一章.md", "kind": "lesson", "status": "draft"},
            {"id": "BF-00-002", "section": "00_课程", "title": "第二章",
             "source": second_path, "kind": "lesson", "status": "placeholder"},
        ]
        data = {"schema_version": 1, "sections": ["00_课程"], "lessons": items}
        (self.root / "catalog" / "lessons.yaml").write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def test_real_catalog_complete(self):
        lessons = site.load_catalog(ROOT)
        self.assertEqual(len(lessons), 40)
        self.assertEqual(sum(x["kind"] == "lesson" for x in lessons), 38)
        self.assertEqual(sum(x["kind"] == "supplement" for x in lessons), 2)
        self.assertEqual(sum(x["status"] == "placeholder" for x in lessons), 27)

    def test_determinism_and_source_integrity(self):
        initial = (self.root / "00_课程" / "00_第一章.md").read_bytes()
        first = site.build_files(self.root)
        out = self.root / "site-dist"
        site.write_site(out, first)
        self.assertEqual(initial, (self.root / "00_课程" / "00_第一章.md").read_bytes())
        self.assertEqual(first, site.build_files(self.root))
        self.assertTrue(site.check_site(out, first)["verified"])
        self.assertTrue(site.write_site(out, first)["verified"])

    def test_table_and_cross_links(self):
        result = site.build_files(self.root)
        first = result["00_课程/00_第一章.html"].decode()
        self.assertIn('<table>', first)
        self.assertIn('<strong>重要</strong>', first)
        self.assertIn('.html#anchor', first)
        self.assertNotIn("polyfill.io", first)

    def test_raw_html_escaped(self):
        page = site.build_files(self.root)["00_课程/01_第二章.html"].decode()
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;script&gt;alert", page)

    def test_broken_link_fails(self):
        (self.root / "00_课程" / "00_第一章.md").write_text(
            '# Broken\n[bad](missing.md)', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Broken Markdown link"):
            site.build_files(self.root)

    def test_uncatalogued_file_fails(self):
        (self.root / "00_课程" / "unknown.md").write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Catalog mismatch"):
            site.load_catalog(self.root)

    def test_unsafe_path_fails(self):
        self.write_catalog("../outside.md")
        with self.assertRaises(ValueError):
            site.load_catalog(self.root)

    def test_stale_output_is_not_overwritten(self):
        result = site.build_files(self.root)
        target = self.root / "site-dist"
        site.write_site(target, result)
        (target / "index.html").write_text("manual edit", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "stale"):
            site.write_site(target, result)
        self.assertEqual((target / "index.html").read_text(), "manual edit")

    def test_foreign_output_is_not_overwritten(self):
        target = self.root / "site-dist"
        target.mkdir()
        (target / "important.txt").write_text("keep me")
        with self.assertRaises(ValueError):
            site.write_site(target, site.build_files(self.root))
        self.assertEqual((target / "important.txt").read_text(), "keep me")

    def test_sha_manifest_complete(self):
        results = site.build_files(self.root)
        data = json.loads(results["site-build-manifest.json"])
        for row in data["items"]:
            self.assertEqual(site.sha256(results[row["path"]]), row["sha256"])
            self.assertEqual(len(results[row["path"]]), row["bytes"])

    def test_legacy_stub_preserves_body(self):
        original = '# 标题\n\n"""\n\nLecture: /课程\nContent: 标题\n\n"""\n\n### 内容\n正文'
        rendered = site.render_markdown(original, "00_课程/00_第一章.md", set())
        self.assertIn("正文", rendered)
        self.assertIn("<h1>标题</h1>", rendered)
        self.assertNotIn("Lecture:", rendered)


if __name__ == "__main__":
    unittest.main()
