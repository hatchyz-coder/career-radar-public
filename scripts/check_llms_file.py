#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
LLMS = ROOT / "llms.txt"


def main() -> int:
    if not LLMS.exists() or not LLMS.read_text(encoding="utf-8").strip():
        print("llms.txt is missing or empty", file=sys.stderr)
        return 1

    text = LLMS.read_text(encoding="utf-8")
    required = (
        "# CareerRadar",
        "https://career.hdnjapan.com/",
        "https://career.hdnjapan.com/sitemap.xml",
        "https://career.hdnjapan.com/privacy.html",
    )
    missing = [value for value in required if value not in text]
    if missing:
        print("llms.txt missing required references: " + ", ".join(missing), file=sys.stderr)
        return 1

    print("CareerRadar llms.txt verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
