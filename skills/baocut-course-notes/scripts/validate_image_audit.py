#!/usr/bin/env python3
"""Validate review declarations and versions, never image semantics or actual viewing."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def validate(notes_path, audit_path):
    notes_path = Path(notes_path).resolve()
    note = json.loads(notes_path.read_text())
    audit = json.loads(Path(audit_path).read_text())
    errors = []
    if audit.get('schema_version') != 1:
        errors.append('Unsupported audit schema_version')
    if audit.get('notes_sha256') != digest(notes_path):
        errors.append('Stale notes hash')
    expected = {(s, f): frame for s, section in enumerate(note['sections'], 1)
                for f, frame in enumerate(section.get('frames', []), 1)}
    seen, hashes = set(), {}
    rows = audit.get('images')
    if not isinstance(rows, list):
        raise ValueError('images must be a list')
    for number, row in enumerate(rows, 1):
        label = f'Image record {number}'
        key = (row.get('section'), row.get('frame'))
        if any(type(i) is not int for i in key):
            errors.append(f'{label}: section/frame must be integer indices')
            continue
        if key not in expected or key in seen:
            errors.append(f'{label}: unknown or duplicate section/frame')
            continue
        seen.add(key)
        frame = expected[key]
        if row.get('path') != frame['path']:
            errors.append(f'{label}: path differs from notes')
        for field in ('purpose', 'expected_information', 'observed_information',
                      'comparison_evidence', 'resolution'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f'{label}: missing {field}')
        if row.get('status') != 'passed' or row.get('known_gap') is not False:
            errors.append(f'{label}: pending or known gap; cannot complete')
        image_path = (notes_path.parent / frame['path']).resolve()
        if not image_path.is_relative_to(notes_path.parent):
            errors.append(f'{label}: image escapes run directory')
            continue
        sources = row.get('sources')
        if not isinstance(sources, list) or not sources:
            errors.append(f'{label}: source comparison evidence required')
            sources = []
        checks = [(image_path, row.get('sha256'), 'image')]
        for source in sources:
            if not source.get('path') or not str(source.get('detail', '')).strip():
                errors.append(f'{label}: source path/detail required')
                continue
            checks.append(((notes_path.parent / source['path']).resolve(),
                           source.get('sha256'), 'source'))
        for path, claimed, kind in checks:
            try:
                if path not in hashes:
                    hashes[path] = digest(path)
                if claimed != hashes[path]:
                    errors.append(f'{label}: stale {kind} hash')
            except OSError:
                errors.append(f'{label}: missing/unreadable {kind} file')
    if seen != set(expected):
        errors.append(f'Missing image records: {sorted(set(expected) - seen)}')
    return {'status': 'blocked' if errors else 'passed', 'images': len(expected),
            'errors': errors,
            'scope': 'Record coverage, file versions and declared checks only; '
                     'no semantic image recognition or browser/PDF acceptance.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notes', required=True)
    parser.add_argument('--audit', required=True)
    args = parser.parse_args()
    try:
        result = validate(args.notes, args.audit)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result = {'status': 'blocked', 'errors': [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
