"""Regression coverage for editorial runway replenishment after the Sep/Oct backlog."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("recover_editorial_queue_runway_test", ROOT / "scripts" / "recover_editorial_queue.py")
assert SPEC and SPEC.loader
EDITORIAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EDITORIAL)


class EditorialRunwayReplenishmentTests(unittest.TestCase):
    def load_inputs(self):
        cadence = json.loads((ROOT / "data" / "editorial_cadence.json").read_text(encoding="utf-8"))
        extension = json.loads((ROOT / "data" / "editorial_topic_extension.json").read_text(encoding="utf-8"))
        return cadence, extension

    def test_all_planned_extension_topics_are_defined(self):
        _, extension = self.load_inputs()
        missing = [article_id for article_id in extension["planned"] if article_id not in extension["topics"]]
        self.assertEqual([], missing)

    def test_backlog_release_can_replenish_at_least_four_future_business_days(self):
        cadence, extension = self.load_inputs()
        payload = deepcopy(cadence)
        simulated_today = date(2026, 10, 2)

        # Model the state immediately after every release due through Oct 2 has
        # been successfully published in one recovery run.
        for item in payload["release_queue"]:
            if item.get("status") == "queued" and date.fromisoformat(item["due_at"]) <= simulated_today:
                item["status"] = "published"
                item["published_at"] = simulated_today.isoformat()

        with mock.patch.object(EDITORIAL, "PLANNED", list(extension["planned"])):
            EDITORIAL.replenish(payload, simulated_today)

        queued = [item for item in payload["release_queue"] if item.get("status") == "queued"]
        self.assertGreaterEqual(len(queued), 4)

        due_dates = [date.fromisoformat(item["due_at"]) for item in queued]
        self.assertEqual(due_dates, sorted(due_dates))
        self.assertEqual(len(due_dates), len(set(due_dates)))
        self.assertTrue(all(value.weekday() < 5 for value in due_dates))
        self.assertTrue(all(value > simulated_today for value in due_dates))

    def test_runway_has_more_than_minimum_stock_to_avoid_immediate_recurrence(self):
        cadence, extension = self.load_inputs()
        known = {item["article_id"] for item in cadence["release_queue"]}
        unused = [article_id for article_id in extension["planned"] if article_id not in known]
        self.assertGreaterEqual(len(unused), 8)


if __name__ == "__main__":
    unittest.main()
