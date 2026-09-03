#!/usr/bin/env python3
"""Fast deterministic regression tests for the Traffic Engine scoring rules."""
from score_search_demand import classify, expected_ctr, score


def assert_category(row: dict, expected: str) -> None:
    actual = score(row)["category"]
    if actual != expected:
        raise AssertionError(f"expected {expected}, got {actual}: {row}")


def main() -> None:
    assert expected_ctr(1.2) == 0.28
    assert expected_ctr(15) == 0.015

    assert_category(
        {"query": "40代 転職 年収", "page": "https://career.hdnjapan.com/ja/articles/a.html", "impressions": 120, "clicks": 1, "ctr": 0.0083, "position": 7.0},
        "ctr_fix",
    )
    assert_category(
        {"query": "pmo 高単価", "page": "https://career.hdnjapan.com/ja/articles/a.html", "impressions": 80, "clicks": 1, "ctr": 0.0125, "position": 13.0},
        "quick_win",
    )
    assert_category(
        {"query": "人材紹介 依存しない", "page": "https://career.hdnjapan.com/", "impressions": 50, "clicks": 0, "ctr": 0.0, "position": 31.0},
        "content_gap",
    )
    assert_category(
        {"query": "career radar", "page": "https://career.hdnjapan.com/", "impressions": 100, "clicks": 35, "ctr": 0.35, "position": 1.0},
        "defend",
    )
    assert_category(
        {"query": "業務委託 戻る 正社員", "page": "https://career.hdnjapan.com/ja/articles/a.html", "impressions": 18, "clicks": 0, "ctr": 0.0, "position": 42.0},
        "long_term",
    )
    assert_category(
        {"query": "rare query", "page": "https://career.hdnjapan.com/ja/articles/a.html", "impressions": 2, "clicks": 0, "ctr": 0.0, "position": 60.0},
        "observe",
    )

    ranked = score({"query": "test", "page": "/", "impressions": 100, "clicks": 0, "ctr": 0.0, "position": 9})
    if not 0 <= ranked["priority_score"] <= 100:
        raise AssertionError("priority score outside 0-100")
    print("Traffic Engine regression tests passed.")


if __name__ == "__main__":
    main()
