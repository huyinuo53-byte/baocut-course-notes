#!/usr/bin/env python3
"""Verify package inventory and SHA-256; this is not a digital signature."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root/'PACKAGE-MANIFEST.json').read_text(encoding='utf-8'))
    expected = {row['path']: row for row in manifest['files']}
    actual = set()
    errors = []
    for p in root.rglob('*'):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            errors.append('Unexpected symlink: '+rel)
        elif p.is_file() and rel != 'PACKAGE-MANIFEST.json':
            if p.relative_to(root).parts[0] in ('build', '.git') or '__pycache__' in p.parts or p.suffix == '.pyc':
                continue
            actual.add(rel)
            row = expected.get(rel)
            if row is None:
                errors.append('Unlisted: '+rel)
            elif p.stat().st_size != row['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest() != row['sha256']:
                errors.append('Changed: '+rel)
    errors.extend('Missing: '+rel for rel in sorted(set(expected)-actual))
    print(json.dumps({'status':'failed' if errors else 'passed', 'files_checked':len(actual), 'errors':errors},indent=2))
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
