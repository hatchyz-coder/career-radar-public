"""Regression tests for the fail-closed curated-source publication gate."""
from __future__ import annotations

from datetime import date
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "recover_editorial_queue_v2_guard_test",
    ROOT / "scripts" / "recover_editorial_queue_v2.py",
)
assert SPEC and SPEC.loader
PUBLISHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PUBLISHER)


def topic(section_copy=None):
    value = {
        "sections": [
            ["First", "First"],
            ["Second", "Second"],
        ]
    }
    if section_copy is not None:
        value["section_copy"] = section_copy
    return value


def curated_copy():
    return [
        {
            "ja": ["日本語の第一段落です。", "日本語の第二段落です。"],
            "en": ["First English paragraph.", "Second English paragraph."],
        },
        {
            "ja": ["別の日本語第一段落です。", "別の日本語第二段落です。"],
            "en": ["Another first English paragraph.", "Another second English paragraph."],
        },
    ]


def cadence(status="queued", due_at="2026-10-09"):
    return {
        "release_queue": [
            {
                "article_id": "due-article",
                "due_at": due_at,
                "locales": ["ja", "en"],
                "status": status,
            }
        ]
    }


class CuratedSourceGateTests(unittest.TestCase):
    TODAY = date(2026, 10, 9)

    def validate(self, source, queue=None):
        extension = {"topics": {"due-article": topic(source)}}
        PUBLISHER.validate_due_curated_sources(
            extension,
            cadence() if queue is None else queue,
            self.TODAY,
        )

    def test_due_article_without_section_copy_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "generic fallback publication is forbidden"):
            self.validate(None)

    def test_future_article_without_section_copy_is_not_rejected_early(self):
        self.validate(None, cadence(due_at="2026-10-12"))

    def test_published_article_without_section_copy_is_ignored(self):
        self.validate(None, cadence(status="published"))

    def test_missing_locale_paragraph_is_rejected(self):
        source = curated_copy()
        source[1]["en"] = ["Only one paragraph."]
        with self.assertRaisesRegex(SystemExit, r"section_copy\[2\]\.en"):
            self.validate(source)

    def test_section_count_mismatch_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "one bilingual entry per section"):
            self.validate(curated_copy()[:1])

    def test_complete_bilingual_source_is_accepted(self):
        self.validate(curated_copy())


if __name__ == "__main__":
    unittest.main()
