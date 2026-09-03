from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_editorial_release", ROOT / "scripts" / "build_editorial_release.py")
assert SPEC and SPEC.loader
BUILDER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BUILDER
SPEC.loader.exec_module(BUILDER)


class BuildEditorialReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "public"
        self.source = Path(self.temp.name) / "private"
        (self.root / "ja" / "articles").mkdir(parents=True)
        (self.root / "en" / "articles").mkdir(parents=True)
        (self.source / "editorial" / "drafts" / "ja").mkdir(parents=True)
        (self.source / "editorial" / "drafts" / "en").mkdir(parents=True)
        (self.root / "index.html").write_text('<section class="section" id="insights"><div class="grid"></div></section>', encoding="utf-8")
        (self.root / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>', encoding="utf-8")
        (self.source / "editorial" / "drafts" / "ja" / "fixture.md").write_text('# 日本語タイトル\n\n最初の段落です。\n\n## 判断\n\n- 選択肢A\n- 選択肢B\n', encoding="utf-8")
        (self.source / "editorial" / "drafts" / "en" / "fixture.md").write_text('# English title\n\nThis is the opening paragraph.\n\n## Decision\n\n1. First option\n2. Second option\n', encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_builder_creates_complete_idempotent_release(self) -> None:
        changes = BUILDER.expected_changes(self.root, self.source, "fixture", "2026-08-25")
        for path, value in changes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8")
        second = BUILDER.expected_changes(self.root, self.source, "fixture", "2026-08-25")
        self.assertEqual([], [path for path, value in second.items() if path.read_text(encoding="utf-8") != value])
        ja = (self.root / "ja" / "articles" / "fixture.html").read_text(encoding="utf-8")
        en = (self.root / "en" / "articles" / "fixture.html").read_text(encoding="utf-8")
        for page in (ja, en):
            self.assertEqual(1, page.count("<h1>"))
            self.assertIn('hreflang="x-default"', page)
            self.assertEqual(4, page.count('class="partner-option"'))
            self.assertEqual(4, page.count('rel="nofollow"'))
            self.assertEqual(4, page.count('referrerpolicy="no-referrer-when-downgrade"'))
        self.assertIn('href="ja/articles/fixture.html"', (self.root / "index.html").read_text(encoding="utf-8"))
        sitemap = (self.root / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn('/ja/articles/fixture.html', sitemap)
        self.assertIn('/en/articles/fixture.html', sitemap)


if __name__ == "__main__":
    unittest.main()
