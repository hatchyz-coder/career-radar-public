"""Regression tests for the prepublication mechanical content gate."""
from __future__ import annotations

from html import escape
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_release_quality as gate


class QualityGateTests(unittest.TestCase):
    def parse_sections(self, sections):
        markup = "".join(f"<h2>{escape(str(i))}</h2><p>{escape(text)}</p>" for i, text in enumerate(sections))
        parser = gate.Sections()
        parser.feed(markup)
        return parser

    def test_repeated_japanese_sentence_in_three_sections_is_rejected(self):
        sentence = "守秘義務がある場合は固有名詞や機密数値を伏せ、課題の構造、自分の判断、トレードオフ、結果を中心に表現すれば、機密を守りながら実績を伝えられます。"
        sections = [sentence + f"固有の内容{i}。" for i in range(8)]
        issues = gate.repetition_errors(self.parse_sections(sections), set(range(8)), "ja", "fixture")
        self.assertTrue(issues, "repeated filler must fail")

    def test_repeated_english_sentence_in_three_sections_is_rejected(self):
        sentence = ("A generic statement repeated across unrelated headings does not provide "
                    "section-specific evidence and must be detected by the release gate.")
        sections = [sentence + f" Independent idea {i}." for i in range(8)]
        issues = gate.repetition_errors(self.parse_sections(sections), set(range(8)), "en", "fixture")
        self.assertTrue(issues, "repeated filler must fail")

    def test_two_similar_sections_do_not_trigger_three_section_limit(self):
        repeated = "同じ説明が二つの節にだけ現れた場合には即座に記事全体を不合格にはしないが、個別の編集上の判断は別途必要です。" * 2
        sections = [repeated, repeated] + ["独立した文章" + str(i) for i in range(6)]
        issues = gate.repetition_errors(self.parse_sections(sections), set(range(8)), "ja", "fixture")
        self.assertFalse(issues)

    def test_unique_paragraphs_are_not_rejected_as_duplicates(self):
        sections = ["違う観点" + str(i) + "。市場の反応を比較し、次の検証事項を明らかにします。" for i in range(8)]
        self.assertFalse(gate.repetition_errors(self.parse_sections(sections), set(range(8)), "ja", "fixture"))

    def test_published_page_bilingual_metadata_and_index_are_checked(self):
        aid = "fixture"
        topic = {"sections": [(f"見出し{i}", f"Heading {i}") for i in range(8)]}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "ja" / "articles" / f"{aid}.html"
            path.parent.mkdir(parents=True)
            source = '<html><h1>Title</h1>' + "".join(
                f"<h2>見出し{i}</h2><p>固有の本文{i}</p><p>別の情報{i}</p>" for i in range(8)
            ) + '</html>'
            path.write_text(source, encoding="utf-8")
            with mock.patch.object(gate, "baseline_validate", return_value=[]):
                errors = gate.validate_article(root, topic, aid, "ja",
                                               {"release_queue": [{"article_id": aid, "status": "published"}]},
                                               "<html/>", "<urlset/>")
            self.assertTrue(any("canonical" in error for error in errors))
            self.assertTrue(any("homepage" in error for error in errors))
            self.assertTrue(any("sitemap" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
