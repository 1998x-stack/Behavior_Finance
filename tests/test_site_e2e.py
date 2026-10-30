"""Playwright smoke tests against the generated site-dist public output."""
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
DIST = ROOT / "site-dist"


class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


@unittest.skipIf(sync_playwright is None, "Install Playwright for browser E2E")
class BuiltSiteE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (DIST / "index.html").is_file():
            raise RuntimeError("Build the site-dist directory before browser E2E")
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        cls.server = ThreadedServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.runner = sync_playwright().start()
        cls.browser = cls.runner.chromium.launch(
            executable_path=os.environ.get("CHROMIUM_PATH") or None, args=["--no-sandbox"])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runner.stop()
        cls.server.shutdown()
        cls.thread.join(timeout=3)
        cls.server.server_close()

    def open_page(self, width=1280):
        page = self.browser.new_page(viewport={"width": width, "height": 800})
        # Avoid requiring a third-party CDN for internal navigation tests.
        page.route("https://cdn.jsdelivr.net/**",
                   lambda route: route.fulfill(status=200, content_type="application/javascript",
                                               body="window.MathJax=window.MathJax||{};"))
        return page

    def test_index_and_chapter_navigation(self):
        page = self.open_page()
        page.goto(self.base + "/", wait_until="domcontentloaded")
        self.assertIn("行为金融学", page.title())
        self.assertEqual(page.locator("main li a").count(), 40)
        page.locator("main li a").first.click()
        page.wait_for_url("**/*.html")
        self.assertIn("BF-00-001", page.locator(".lesson-meta").inner_text())
        self.assertTrue(page.locator("main h1").count() >= 1)
        page.get_by_role("link", name="返回课程目录").click()
        self.assertEqual(page.locator("main li a").count(), 40)
        page.close()

    def test_mobile_layout_without_horizontal_overflow(self):
        page = self.open_page(width=375)
        page.goto(self.base + "/", wait_until="domcontentloaded")
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 375)
        page.locator("main li a").first.click()
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 375)
        page.close()


if __name__ == "__main__":
    unittest.main()
