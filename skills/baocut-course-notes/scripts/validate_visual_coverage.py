#!/usr/bin/env python3
"""Validate visual ledger structure/versions, not semantic coverage or actual viewing."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def validate(notes_path, coverage_path):
    notes_path = Path(notes_path).resolve()
    root = notes_path.parent
    notes = json.loads(notes_path.read_text())
    coverage = json.loads(Path(coverage_path).read_text())
    errors, hashes = [], {}

    def check_file(record, label, local=False):
        path = (root / record['path']).resolve()
        if local and not path.is_relative_to(root):
            errors.append(f'{label}: path escapes run')
        if path not in hashes:
            hashes[path] = digest(path)
        if record.get('sha256') != hashes[path]:
            errors.append(f'{label}: stale hash')
        return path

    def number(value):
        return type(value) in (int, float) and math.isfinite(value)

    if coverage.get('schema_version') != 1:
        errors.append('Unsupported schema')
    if coverage.get('notes_sha256') != digest(notes_path):
        errors.append('Stale notes hash')
    if coverage.get('status') != 'passed' or coverage.get('known_gaps') != []:
        errors.append('Pending review or known gaps')
    if not str(coverage.get('method', '')).strip():
        errors.append('Review method required')
    media = coverage['media']
    check_file(media, 'media')
    duration = media.get('duration_seconds')
    video_duration = media.get('video_duration_seconds')
    if (not number(duration) or duration <= 0 or not number(video_duration)
            or abs(duration - video_duration) > 1 or media.get('tail_decode') != 'passed'):
        errors.append('Complete video stream and successful tail decode required')
    inventory_path = check_file(coverage['inventory'], 'inventory', local=True)
    inventory = json.loads(inventory_path.read_text())
    if inventory.get('media_sha256') != media.get('sha256'):
        errors.append('Inventory/media mismatch')
    candidates = inventory['candidates']
    ids = [c['id'] for c in candidates]
    if not ids or len(ids) != len(set(ids)):
        errors.append('Empty/duplicate candidate inventory')
    for c in candidates:
        check_file(c, f"candidate {c['id']}", local=True)
        if not number(c.get('time')) or not 0 <= c['time'] <= duration:
            errors.append(f"candidate {c['id']}: invalid time")
    windows = sorted(coverage.get('reviewed_windows', []), key=lambda w: w['start'])
    edge = 0
    for w in windows:
        if (not number(w.get('start')) or not number(w.get('end'))
                or w['start'] < 0 or w['end'] <= w['start'] or w['end'] > duration + .01
                or w['start'] > edge + .01 or not str(w.get('evidence', '')).strip()):
            errors.append('Invalid/gapped review windows')
        edge = max(edge, w['end'])
    if abs(edge - duration) > .01:
        errors.append('Review windows do not cover full duration')
    states = coverage.get('states', [])
    state_ids = [s.get('candidate_id') for s in states]
    if set(state_ids) != set(ids) or len(state_ids) != len(ids):
        errors.append('Each candidate needs exactly one disposition')
    state_by_id = {s.get('candidate_id'): s for s in states}
    permitted = {'included', 'official_page', 'represented_in_text', 'duplicate', 'transition'}
    for s in states:
        label = f"state {s.get('candidate_id')}"
        kind = s.get('disposition')
        if kind not in permitted or s.get('known_gap') is not False:
            errors.append(f'{label}: unresolved disposition/gap')
        for field in ('description', 'evidence'):
            if not isinstance(s.get(field), str) or not s[field].strip():
                errors.append(f'{label}: {field} required')
        if kind == 'duplicate':
            prior = s.get('duplicate_of')
            visited = {s.get('candidate_id')}
            while prior is not None:
                if prior in visited or prior not in state_by_id:
                    errors.append(f'{label}: invalid/cyclic duplicate')
                    break
                visited.add(prior)
                prior = state_by_id[prior].get('duplicate_of')
        if kind in {'included', 'official_page', 'represented_in_text'}:
            if not s.get('targets'):
                errors.append(f'{label}: note targets required')
            for target in s.get('targets', []):
                sn = target.get('section')
                if type(sn) is not int or not 1 <= sn <= len(notes['sections']):
                    errors.append(f'{label}: invalid section target')
                    continue
                section = notes['sections'][sn - 1]
                fn = target.get('frame')
                if kind != 'represented_in_text' and (type(fn) is not int or not 1 <= fn <= len(section.get('frames', []))):
                    errors.append(f'{label}: invalid frame target')
                    continue
                if kind in {'included', 'official_page'}:
                    frame = section['frames'][fn - 1]
                    required_type = 'video_frame' if kind == 'included' else 'pdf_page'
                    if frame.get('source_type', 'video_frame') != required_type:
                        errors.append(f'{label}: wrong target source type')
    if 'pdf' in coverage:
        pdf = coverage['pdf']
        check_file(pdf, 'pdf')
        count = pdf.get('page_count')
        pages = coverage.get('pdf_pages', [])
        if type(count) is not int or count <= 0 or sorted(p.get('page') for p in pages) != list(range(1, count + 1)):
            errors.append('Each PDF page needs one disposition')
        for page in pages:
            if page.get('disposition') not in permitted | {'supplement'} or not str(page.get('reason', '')).strip():
                errors.append('Unresolved/missing PDF page disposition')
    return {'status': 'blocked' if errors else 'passed', 'candidates': len(candidates),
            'errors': errors, 'scope': 'Versions, ledger coverage, targets and declared review only; not semantic completeness.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notes', required=True)
    parser.add_argument('--coverage', required=True)
    args = parser.parse_args()
    try:
        result = validate(args.notes, args.coverage)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result = {'status': 'blocked', 'errors': [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
