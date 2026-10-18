import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class CareerReviewMVPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "review.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "assets" / "career-review.js").read_text(encoding="utf-8")

    def test_single_memo_progressive_ui(self):
        self.assertIn('data-review-memo', self.html)
        self.assertEqual(self.html.count('data-review-memo'), 1)
        self.assertIn('Career Memo', self.html)
        self.assertNotIn('入力機能は現在準備中', self.html)

    def test_voice_and_local_only_storage(self):
        for token in ['SpeechRecognition', 'webkitSpeechRecognition', 'speechSynthesis', 'localStorage']:
            self.assertIn(token, self.js)
        self.assertNotRegex(self.js, r'fetch\s*\(')
        self.assertNotRegex(self.js, r'XMLHttpRequest')

    def test_required_semantic_slots(self):
        for slot in ['Role','Responsibility','DecisionRights','Achievement','Evidence','Risk','Goal','Constraint']:
            self.assertIn(slot, self.js)

    def test_six_axes(self):
        for axis in ['Evidence','Decision Rights','Portability','Scarcity','Optionality','Concentration Risk']:
            self.assertIn(axis, self.js)

    def test_review_analytics(self):
        for event in [
            'career_review_view','career_review_start','career_review_step','career_review_complete',
            'career_review_result_view','career_review_article_click','career_review_market_test_click',
            'career_review_save'
        ]:
            self.assertIn(event, self.js)

    def test_assign_market_test_preserved(self):
        self.assertIn('data-partner-id="assign"', self.html)
        self.assertIn('accesstrade_1057788', self.html)
        self.assertIn('0100p83l00oxbh', self.html)
        self.assertIn('rel="nofollow"', self.html)
        self.assertIn('data-review-market-test', self.html)

if __name__ == "__main__":
    unittest.main()
