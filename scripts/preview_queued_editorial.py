#!/usr/bin/env python3
"""Preview each scheduled date in an isolated copy; never write to the checkout."""
from __future__ import annotations

from datetime import date
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from check_release_quality import TARGETS, evaluate
from check_content_quality import Parser

ROOT = Path(__file__).resolve().parents[1]
DAYS = ("2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25", "2026-09-28")
# Same generation/postprocessing order as the existing publication workflow.
POST = (
    "polish_generated_articles.py", "expand_generated_articles.py",
    "humanize_generated_articles.py", "build_bootstrap_search_hubs.py",
    "enhance_pv_discovery.py", "enhance_article_discovery.py",
    "enhance_affiliate_funnel.py", "optimize_conversion_ctas.py",
    "inject_analytics.py", "generate_social_pack.py",
    "build_recognition_distribution.py", "export_editorial_desk_feed.py",
    "build_traffic_dashboard.py", "localize_japanese_ui.py",
)
CHECKS = (
    "check_article_discovery.py", "check_affiliate_funnel.py",
    "check_conversion_ctas.py", "check_japanese_ui_language.py",
    "check_content_quality.py", "check_editorial_cadence.py",
)


def execute(site, args, label):
    proc = subprocess.run([sys.executable, *args], cwd=site, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=90, check=False)
    if proc.returncode:
        raise RuntimeError(f"{label}: exit={proc.returncode}; output={proc.stdout[-3000:]}")
    return proc.stdout


def main():
    errors = []
    with tempfile.TemporaryDirectory(prefix="career-radar-preview-") as td:
        site = Path(td) / "site"
        shutil.copytree(ROOT, site, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "*.pyc"))
        generated = set()
        validated_locales = set()
        for index, day in enumerate(DAYS):
            # Date override is process-local, in the ephemeral copy, and never reaches the publisher.
            code = (
                "from datetime import date\n"
                "import sys\n"
                f"sys.path.insert(0, {str(site / 'scripts')!r})\n"
                "import recover_editorial_queue as legacy\n"
                "import recover_editorial_queue_v2 as publisher\n"
                "class PreviewDate(date):\n"
                f"    @classmethod\n    def today(cls):\n        return date.fromisoformat('{day}')\n"
                "legacy.date = PreviewDate\n"
                "raise SystemExit(publisher.main())\n"
            )
            execute(site, ["-c", code], f"generator on {day}")
            for script in POST:
                execute(site, [str(site / "scripts" / script)], f"{script} on {day}")
            # A zero-error result alone is not evidence that the expected article was built.
            # Assert each scheduled ID was actually published on the simulated date.
            cadence = json.loads((site / "data" / "editorial_cadence.json").read_text(encoding="utf-8"))
            expected_id = TARGETS[index]
            rows = [row for row in cadence["release_queue"] if row.get("article_id") == expected_id]
            if len(rows) != 1 or rows[0].get("status") != "published" or rows[0].get("published_at") != day:
                errors.append(f"{day}: expected {expected_id} published on that date, got {rows}")
            for locale in ("ja", "en"):
                page_path = site / locale / "articles" / f"{expected_id}.html"
                if not page_path.is_file():
                    errors.append(f"{day}: missing rendered HTML {locale}/{expected_id}")
                    continue
                parser = Parser()
                parser.feed(page_path.read_text(encoding="utf-8"))
                visible = " ".join(parser.text)
                amount = (len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", visible)) if locale == "ja"
                          else len(re.findall(r"\b[\w’'-]+\b", visible)))
                validated_locales.add((expected_id, locale))
                print(f"Rendered {day}: {expected_id}/{locale} H2={parser.h2} paragraphs={parser.paragraphs} visible_units={amount}")
            # All five scheduled days must be covered even if the first article fails quality.
            current = evaluate(site)
            day_errors = [error for error in current if error.split("/")[0] in TARGETS]
            errors.extend(f"{day}: {error}" for error in day_errors if error not in generated)
            generated.update(day_errors)
            print(f"Preview {day}: validated postprocessed HTML; issue count={len(current)}")
        if validated_locales != {(aid, locale) for aid in TARGETS for locale in ("ja", "en")}:
            errors.append(f"Preview incomplete: validated {len(validated_locales)} of 10 required locale pages")
        for script in CHECKS:
            try:
                execute(site, [str(site / "scripts" / script)], f"{script} after last preview date")
            except RuntimeError as exc:
                errors.append(str(exc))
    if errors:
        print("PREPUBLICATION PREVIEW FAILED; CI must not approve this article copy:", file=sys.stderr)
        print("\n".join(errors[:70]), file=sys.stderr)
        return 1
    print("Prepublication preview passed all five dates and downstream checks; editorial meaning still requires review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

