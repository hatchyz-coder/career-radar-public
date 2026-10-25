"""Regression coverage for editorial runway replenishment and curated-source continuity."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
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

V2_SPEC = importlib.util.spec_from_file_location("recover_editorial_queue_v2_runway_test", ROOT / "scripts" / "recover_editorial_queue_v2.py")
assert V2_SPEC and V2_SPEC.loader
V2 = importlib.util.module_from_spec(V2_SPEC)
V2_SPEC.loader.exec_module(V2)


class EditorialRunwayReplenishmentTests(unittest.TestCase):
    def load_inputs(self):
        cadence = json.loads((ROOT / "data" / "editorial_cadence.json").read_text(encoding="utf-8"))
        extension = json.loads((ROOT / "data" / "editorial_topic_extension.json").read_text(encoding="utf-8"))
        return cadence, extension

    def test_all_planned_extension_topics_are_defined(self):
        _, extension = self.load_inputs()
        missing = [article_id for article_id in extension["planned"] if article_id not in extension["topics"]]
        self.assertEqual([], missing)

    def test_current_live_queue_is_fully_curated(self):
        cadence, extension = self.load_inputs()
        V2.validate_queued_curated_sources(extension, cadence)

    def test_at_least_two_workweeks_of_curated_inventory_exist(self):
        cadence, extension = self.load_inputs()
        known = {item["article_id"] for item in cadence["release_queue"]}
        curated = [
            article_id
            for article_id in extension["planned"]
            if article_id not in known and V2.topic_is_curated(extension["topics"][article_id])
        ]
        self.assertGreaterEqual(len(curated), 5)

    def test_replenishment_uses_only_curated_topics(self):
        cadence, extension = self.load_inputs()
        payload = deepcopy(cadence)
        simulated_today = date(2026, 10, 26)
        curated_planned = [
            article_id for article_id in extension["planned"]
            if V2.topic_is_curated(extension["topics"][article_id])
        ]
        with mock.patch.object(EDITORIAL, "PLANNED", curated_planned):
            EDITORIAL.replenish(payload, simulated_today)
        queued = [item for item in payload["release_queue"] if item.get("status") == "queued"]
        self.assertTrue(queued)
        for item in queued:
            topic = extension["topics"].get(item["article_id"])
            if topic is not None:
                self.assertTrue(V2.topic_is_curated(topic), item["article_id"])

    def test_runway_dates_remain_unique_chronological_business_days(self):
        cadence, extension = self.load_inputs()
        payload = deepcopy(cadence)
        simulated_today = date(2026, 10, 26)
        curated_planned = [
            article_id for article_id in extension["planned"]
            if V2.topic_is_curated(extension["topics"][article_id])
        ]
        with mock.patch.object(EDITORIAL, "PLANNED", curated_planned):
            EDITORIAL.replenish(payload, simulated_today)
        queued = [item for item in payload["release_queue"] if item.get("status") == "queued"]
        due_dates = [date.fromisoformat(item["due_at"]) for item in queued]
        self.assertEqual(due_dates, sorted(due_dates))
        self.assertEqual(len(due_dates), len(set(due_dates)))
        self.assertTrue(all(value.weekday() < 5 for value in due_dates))


if __name__ == "__main__":
    unittest.main()
