#!/usr/bin/env python3
"""Chromium file:// QA at mobile, tablet and desktop; screenshots are CI artifacts."""
import json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
ARTIFACTS=ROOT / "reports" / "browser-qa"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
LESSON=re.compile(r"_[1-4]\.\d+_")
pages=sorted(p for d in ROOT.glob("0[1-4]_*") for p in d.glob("*.html") if LESSON.search(p.name))
failures=[]; summary=[]
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True)
    for page_file in pages:
        for width in (360,390,768,1440):
            page=browser.new_page(viewport={"width":width,"height":860},device_scale_factor=1,offline=True)
            errors=[]
            page.on("pageerror",lambda error: errors.append(str(error)))
            page.goto(page_file.as_uri(),wait_until="load")
            page.wait_for_timeout(100)
            state=page.evaluate("""() => ({
              scroll: document.documentElement.scrollWidth,
              viewport: window.innerWidth,
              h1: document.querySelectorAll('h1').length,
              links: [...document.querySelectorAll('nav.course-sequence a')].length,
              styles: [...document.styleSheets].length
            })""")
            entry={"lesson":page_file.relative_to(ROOT).as_posix(),"viewport":width,**state,"js_errors":errors}
            if state["scroll"]>width+2: failures.append(f"{page_file.name} {width}px overflow ({state['scroll']})")
            if state["h1"]!=1 or state["links"]!=3 or state["styles"]==0:
                failures.append(f"{page_file.name} {width}px invalid page structure: {state}")
            if errors: failures.append(f"{page_file.name} {width}px JS: {errors}")
            if width in (360,1440):
                page.screenshot(path=str(ARTIFACTS / f"{page_file.stem[:7]}-{width}.png"),full_page=True)
            summary.append(entry)
            page.close()
    browser.close()
(ARTIFACTS/"results.json").write_text(json.dumps({"checks":summary,"failures":failures},ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Checked {len(pages)} lessons across 4 viewports: {len(summary)} page checks.")
if failures:
    for x in failures: print("ERROR:",x)
    raise SystemExit(1)
