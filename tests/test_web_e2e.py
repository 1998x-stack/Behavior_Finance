"""Optional real browser tests; CI installs Playwright and Chromium."""
import functools
import http.server
import os
import socketserver
import threading
import unittest
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ROOT = Path(__file__).resolve().parents[1]


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


@unittest.skipIf(sync_playwright is None, "Playwright not installed; browser job runs separately")
class WebE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
        cls.server = Server(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            executable_path=os.environ.get("CHROMIUM_PATH") or None, args=["--no-sandbox"]
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.thread.join(timeout=3)
        cls.server.server_close()

    def test_notes_persist_and_export_once_without_markup_injection(self):
        page = self.browser.new_page(accept_downloads=True)
        page.goto(self.base + "/tests/fixtures/article.html")
        paragraph = page.locator("#first")
        paragraph.locator(".comment-add").click()
        payload = "<img src=x onerror=alert(1)> NOTE-M02"
        editor = page.get_by_role("textbox", name="批注内容")
        editor.fill(payload)
        editor.press("Enter")
        self.assertEqual(paragraph.locator(".comment").count(), 1)
        self.assertEqual(paragraph.locator(".comment").inner_text(), payload)
        self.assertEqual(page.locator("#first img").count(), 0)
        page.reload()
        self.assertEqual(page.locator("#first .comment").count(), 1)
        self.assertEqual(page.locator("#first .comment").inner_text(), payload)
        with page.expect_download() as event:
            page.get_by_role("button", name="导出文章与批注").click()
        saved = event.value.path().read_text(encoding="utf-8")
        self.assertEqual(saved.count("NOTE-M02"), 1)
        self.assertNotIn("<img src=x", saved)
        self.assertIn("&lt;img src=x", saved)
        self.assertNotIn("comment-add", saved)
        page.close()

    def test_esc_cancel_and_enter_do_not_double_save(self):
        page = self.browser.new_page()
        page.goto(self.base + "/tests/fixtures/article.html")
        p = page.locator("#first")
        p.locator(".comment-add").click()
        editor = page.get_by_role("textbox", name="批注内容")
        editor.fill("discard me")
        editor.press("Escape")
        self.assertEqual(p.locator(".comment").count(), 0)
        p.locator(".comment-add").click()
        editor = page.get_by_role("textbox", name="批注内容")
        editor.fill("save once")
        editor.press("Enter")
        self.assertEqual(p.locator(".comment").count(), 1)
        page.close()

    def test_mobile_375px_fixture_and_index_do_not_overflow(self):
        page = self.browser.new_page(viewport={"width": 375, "height": 700})
        page.goto(self.base + "/tests/fixtures/article.html")
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 375)
        page.goto(self.base + "/index.html")
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 375)
        page.close()


if __name__ == "__main__":
    unittest.main()
