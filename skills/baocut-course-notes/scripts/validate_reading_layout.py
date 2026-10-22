#!/usr/bin/env python3
"""Check editorial placement coverage, source version and exact emphasis terms."""
import argparse
import json
from pathlib import Path
from course_notes import safe_path
from reading_layout import validate

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--notes', required=True)
    p.add_argument('--layout', required=True)
    args = p.parse_args()
    try:
        data = safe_path(args.notes).read_bytes()
        report = validate(json.loads(data), json.loads(safe_path(args.layout).read_text(encoding='utf-8')), data)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        p.exit(1, 'Error: ' + str(exc) + '\n')
