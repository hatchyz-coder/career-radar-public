"""Regression tests for safe, all-articles-first editorial release validation."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("recover_editorial_queue_guard_test", ROOT / "scripts" / "recover_editorial_queue.py")
assert SPEC and SPEC.loader
EDITORIAL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = EDITORIAL
SPEC.loader.exec_module(EDITORIAL)


def queued(article_id, due_at="2020-01-01", locales=None):
    return {"article_id": article_id, "due_at": due_at, "locales": ["ja", "en"] if locales is None else locales, "status": "queued"}


class EditorialReleasePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for locale in ("ja", "en"):
            (self.root / locale / "articles").mkdir(parents=True)
        self.cadence = self.root / "data" / "editorial_cadence.json"
        self.cadence.parent.mkdir()
        self.index = self.root / "index.html"
        self.sitemap = self.root / "sitemap.xml"
        self.index.write_text("ORIGINAL INDEX", encoding="utf-8")
        self.sitemap.write_text("ORIGINAL SITEMAP", encoding="utf-8")
        self.topics = {"first": {}, "second": {}}
        self.page_mock = mock.Mock(side_effect=lambda aid, loc, when: f"RENDERED {aid} {loc}")
        self.card_mock = mock.Mock(side_effect=lambda src, aid: src + "|CARD:" + aid)
        self.sitemap_mock = mock.Mock(side_effect=lambda src, aid, when: src + "|URL:" + aid)
        replacements = {
            "ROOT": self.root, "CADENCE": self.cadence, "INDEX": self.index,
            "SITEMAP": self.sitemap, "TOPICS": self.topics,
            "page": self.page_mock, "add_card": self.card_mock,
            "update_sitemap": self.sitemap_mock,
            "replenish": mock.Mock(),
        }
        self.patches = [mock.patch.object(EDITORIAL, name, value) for name, value in replacements.items()]
        for patcher in self.patches:
            patcher.start()
        self.write_queue([queued("first")])

    def tearDown(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temp.cleanup()

    def write_queue(self, items):
        self.cadence.write_text(json.dumps({"release_queue": items}, ensure_ascii=False), encoding="utf-8")

    def snapshot(self):
        return (self.index.read_bytes(), self.sitemap.read_bytes(), self.cadence.read_bytes())

    def path(self, aid, locale):
        return self.root / locale / "articles" / (aid + ".html")

    def assert_stopped_unchanged(self):
        before = self.snapshot()
        with self.assertRaises(SystemExit):
            EDITORIAL.main()
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.path("first", "ja").exists())
        self.assertFalse(self.path("first", "en").exists())
        self.page_mock.assert_not_called()

    def test_01_normal_queued_release_is_written_in_both_languages(self):
        self.assertEqual(0, EDITORIAL.main())
        for locale in ("ja", "en"):
            self.assertEqual(f"RENDERED first {locale}", self.path("first", locale).read_text(encoding="utf-8"))
        self.assertEqual("published", json.loads(self.cadence.read_text(encoding="utf-8"))["release_queue"][0]["status"])

    def test_02_existing_japanese_html_blocks_before_writing(self):
        self.path("first", "ja").write_text("PRESERVE JAPANESE", encoding="utf-8")
        before = self.snapshot()
        with self.assertRaises(SystemExit):
            EDITORIAL.main()
        self.assertEqual(before, self.snapshot())
        self.assertEqual("PRESERVE JAPANESE", self.path("first", "ja").read_text(encoding="utf-8"))
        self.assertFalse(self.path("first", "en").exists())
        self.page_mock.assert_not_called()

    def test_03_existing_english_html_blocks_before_writing(self):
        self.path("first", "en").write_text("PRESERVE ENGLISH", encoding="utf-8")
        before = self.snapshot()
        with self.assertRaises(SystemExit):
            EDITORIAL.main()
        self.assertEqual(before, self.snapshot())
        self.assertEqual("PRESERVE ENGLISH", self.path("first", "en").read_text(encoding="utf-8"))
        self.assertFalse(self.path("first", "ja").exists())
        self.page_mock.assert_not_called()

    def test_04_later_article_html_blocks_earlier_due_article(self):
        self.write_queue([queued("first"), queued("second")])
        self.path("second", "en").write_text("PRESERVE LATER", encoding="utf-8")
        self.assert_stopped_unchanged()
        self.assertEqual("PRESERVE LATER", self.path("second", "en").read_text(encoding="utf-8"))

    def test_05_future_queued_html_blocks_current_release(self):
        self.write_queue([queued("first"), queued("second", due_at="2999-01-01")])
        self.path("second", "ja").write_text("PRESERVE FUTURE", encoding="utf-8")
        self.assert_stopped_unchanged()

    def test_06_published_html_is_untouched_and_not_rendered(self):
        original = {"article_id": "second", "due_at": "2020-01-01", "locales": ["ja", "en"], "status": "published", "published_at": "2020-01-01"}
        self.write_queue([original, queued("first")])
        self.path("second", "ja").write_text("PUBLISHED", encoding="utf-8")
        self.assertEqual(0, EDITORIAL.main())
        self.assertEqual("PUBLISHED", self.path("second", "ja").read_text(encoding="utf-8"))
        self.assertEqual(["first", "first"], [call.args[0] for call in self.page_mock.call_args_list])

    def test_07_missing_later_topic_blocks_before_earlier_article(self):
        self.write_queue([queued("first"), queued("second")])
        del self.topics["second"]
        self.assert_stopped_unchanged()

    def test_08_later_render_failure_does_not_write_earlier_article(self):
        self.write_queue([queued("first"), queued("second")])
        before = self.snapshot()
        def failing_render(aid, locale, when):
            if aid == "second" and locale == "en":
                raise ValueError("injected later render failure")
            return f"RENDERED {aid} {locale}"
        self.page_mock.side_effect = failing_render
        with self.assertRaisesRegex(ValueError, "later render failure"):
            EDITORIAL.main()
        self.assertEqual(before, self.snapshot())
        for aid in ("first", "second"):
            for locale in ("ja", "en"):
                self.assertFalse(self.path(aid, locale).exists())

    def test_09_later_sitemap_failure_does_not_write_earlier_article(self):
        self.write_queue([queued("first"), queued("second")])
        before = self.snapshot()
        def failing_sitemap(src, aid, when):
            if aid == "second":
                raise ValueError("injected sitemap failure")
            return src + aid
        self.sitemap_mock.side_effect = failing_sitemap
        with self.assertRaisesRegex(ValueError, "sitemap failure"):
            EDITORIAL.main()
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.path("first", "ja").exists())

    def test_10_duplicate_queued_ids_stop_before_generation(self):
        self.write_queue([queued("first"), queued("first")])
        self.assert_stopped_unchanged()

    def test_11_invalid_locales_stop_before_generation(self):
        for locales in ([], ["ja", "ja"], ["de"]):
            with self.subTest(locales=locales):
                self.write_queue([queued("first", locales=locales)])
                self.page_mock.reset_mock()
                self.assert_stopped_unchanged()

    def test_12_english_html_blocks_even_if_queue_lists_japanese_only(self):
        self.write_queue([queued("first", locales=["ja"])])
        self.path("first", "en").write_text("PRESERVE PEER", encoding="utf-8")
        before = self.snapshot()
        with self.assertRaises(SystemExit):
            EDITORIAL.main()
        self.assertEqual(before, self.snapshot())
        self.assertEqual("PRESERVE PEER", self.path("first", "en").read_text(encoding="utf-8"))
        self.assertFalse(self.path("first", "ja").exists())
        self.page_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
