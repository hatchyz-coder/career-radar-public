#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNIPPET = '<script defer src="/assets/analytics.js"></script>'
SKIP_DIRS = {'.git', '.github', 'docs'}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts)


def main() -> None:
    changed = 0
    checked = 0
    for path in sorted(ROOT.rglob('*.html')):
        if should_skip(path):
            continue
        checked += 1
        text = path.read_text(encoding='utf-8')
        if SNIPPET in text:
            continue
        if '</head>' not in text:
            raise SystemExit(f'Missing </head>: {path.relative_to(ROOT)}')
        text = text.replace('</head>', f'{SNIPPET}</head>', 1)
        path.write_text(text, encoding='utf-8')
        changed += 1
    print(f'Analytics injection checked {checked} HTML files; changed {changed}.')


if __name__ == '__main__':
    main()
