#!/usr/bin/env python3
"""Freeze file/dependency fingerprints and detect changes; never certify content quality."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from course_notes import safe_path, read_json, dump


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return {'sha256': digest.hexdigest(), 'bytes': path.stat().st_size}


def graph(items):
    if not isinstance(items, list) or not items:
        raise ValueError('artifacts must be a nonempty list')
    by_id = {}
    for item in items:
        ident = item.get('id')
        if not isinstance(ident, str) or not ident or ident in by_id:
            raise ValueError('Artifact IDs must be unique nonempty strings')
        if not isinstance(item.get('path'), str) or not item['path']:
            raise ValueError('Each artifact needs a path')
        deps = item.get('depends_on')
        if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps):
            raise ValueError('Explicit depends_on list required, including [] for sources')
        if len(set(deps)) != len(deps):
            raise ValueError('Duplicate dependency')
        by_id[ident] = item
    visiting, done = set(), set()

    def visit(ident):
        if ident not in by_id:
            raise ValueError('Unknown dependency: ' + ident)
        if ident in visiting:
            raise ValueError('Dependency cycle: ' + ident)
        if ident in done:
            return
        visiting.add(ident)
        for dep in by_id[ident]['depends_on']:
            visit(dep)
        visiting.remove(ident)
        done.add(ident)

    for ident in by_id:
        visit(ident)
    return by_id


def artifact_path(root, item):
    return safe_path(root / item['path'])


def capture(spec_path, out_path):
    spec_path, out_path = safe_path(spec_path), safe_path(out_path)
    if out_path.exists():
        raise ValueError('Snapshot already exists; use a new revision filename')
    spec = read_json(spec_path)
    if spec.get('schema_version') != 1:
        raise ValueError('Expected trace spec schema_version 1')
    if not isinstance(spec.get('run_id'), str) or not spec['run_id']:
        raise ValueError('run_id required')
    if spec.get('basis') not in ('observed_build', 'historical_inventory'):
        raise ValueError('basis must be observed_build or historical_inventory')
    root = safe_path(spec_path.parent / spec.get('root', '.'))
    items = spec['artifacts']
    graph(items)
    paths = [artifact_path(root, item) for item in items]
    if len(set(paths)) != len(paths) or out_path in paths or spec_path in paths:
        raise ValueError('Duplicate paths or self-reference')
    records = []
    for item, path in zip(items, paths):
        records.append({**item, **fingerprint(path)})
    snapshot = {
        'schema_version': 1, 'run_id': spec['run_id'], 'basis': spec['basis'],
        'captured_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'root': str(root), 'spec_sha256': fingerprint(spec_path)['sha256'],
        'artifacts': records,
        'claim': 'File snapshot only; dependencies are declarations, not proof of execution or quality.'
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves earlier revisions even across concurrent writers.
    with out_path.open('x', encoding='utf-8') as stream:
        stream.write(dump(snapshot) + '\n')
    return snapshot


def check(snapshot_path, root_override=None):
    snapshot = read_json(snapshot_path)
    if snapshot.get('schema_version') != 1:
        raise ValueError('Unsupported snapshot version')
    root = safe_path(root_override or snapshot['root'])
    by_id = graph(snapshot['artifacts'])
    changed, unavailable = [], []
    for ident, item in by_id.items():
        expected = item.get('sha256')
        if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
            raise ValueError('Invalid recorded SHA256: ' + ident)
        try:
            actual = fingerprint(artifact_path(root, item))
        except OSError:
            unavailable.append(ident)
            continue
        if actual['sha256'] != expected or actual['bytes'] != item.get('bytes'):
            changed.append(ident)
    affected = set(changed + unavailable)
    while True:
        next_set = affected | {ident for ident, item in by_id.items() if affected.intersection(item['depends_on'])}
        if next_set == affected:
            break
        affected = next_set
    return {
        'run_id': snapshot['run_id'], 'basis': snapshot['basis'],
        'status': 'changed' if affected else 'unchanged',
        'changed_files': changed, 'unavailable_files': unavailable,
        'requires_revalidation': sorted(affected - set(changed + unavailable)),
        'checked_files': len(by_id),
        'claim': 'Unchanged does not mean complete, correct, visually reviewed, or generated from the declared dependencies.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    cap = sub.add_parser('capture')
    cap.add_argument('--spec', required=True)
    cap.add_argument('--out', required=True)
    chk = sub.add_parser('check')
    chk.add_argument('--snapshot', required=True)
    chk.add_argument('--root', help='Explicit relocated run root; never guessed')
    args = parser.parse_args()
    try:
        if args.command == 'capture':
            result = capture(args.spec, args.out)
            print(dump({'snapshot': str(safe_path(args.out)), 'artifacts': len(result['artifacts']), 'basis': result['basis']}))
        else:
            result = check(args.snapshot, args.root)
            print(dump(result))
            if result['status'] != 'unchanged':
                parser.exit(2)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.exit(1, 'Error: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
