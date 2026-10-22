#!/usr/bin/env python3
"""Deterministic handoff helpers. No model calls and no .bcut writes."""
import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import math
import os
from pathlib import Path
import tempfile
import uuid


def safe_path(value):
    p = Path(value).expanduser().resolve()
    if any(x.endswith('.bcut') for x in p.parts):
        raise ValueError('Use exported copies outside .bcut; project operations belong to BaoCut CLI')
    return p


def read_json(path):
    return json.loads(safe_path(path).read_text(encoding='utf-8'))


def write(path, data):
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=p.parent, delete=False) as f:
        tmp = f.name
        f.write(data)
    os.replace(tmp, p)


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2)


def seconds(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0:
        raise ValueError('Time must be a finite nonnegative number')
    return x


def chunks(args):
    src = safe_path(args.input)
    out = safe_path(args.out)
    rows = read_json(src).get('sentences')
    if not rows:
        raise ValueError('Expected nonempty BaoCut export sentences')
    seen, normalized = set(), []
    for r in rows:
        ident = r['id']
        if ident in seen or not isinstance(ident, str):
            raise ValueError('Sentence IDs must be unique strings')
        seen.add(ident)
        start, end = seconds(r['start']), seconds(r['end'])
        if end < start or not isinstance(r['text'], str):
            raise ValueError('Invalid sentence')
        normalized.append(dict(id=ident, start=start, end=end, text=r['text']))
    normalized.sort(key=lambda r: (r['start'], r['end']))
    groups, group, chars = [], [], 0
    for row in normalized:
        if group and (row['start'] - group[0]['start'] >= 300 or chars + len(row['text']) > 6000):
            groups.append(group)
            group, chars = [], 0
        group.append(row)
        chars += len(row['text'])
    if group:
        groups.append(group)
    index = {'version': 1, 'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(), 'chunks': [], 'sentences': []}
    for i, group in enumerate(groups, 1):
        ident = f'chunk-{i:04d}'
        write(out / (ident + '.json'), dump(group))
        index['chunks'].append({'id': ident, 'file': ident + '.json', 'start': group[0]['start'], 'end': max(r['end'] for r in group), 'source_ids': [r['id'] for r in group]})
        index['sentences'].extend({k: r[k] for k in ('id', 'start', 'end')} for r in group)
    write(out / 'index.json', dump(index))
    print(dump({'index': str(out / 'index.json'), 'chunks': len(groups), 'sentences': len(rows)}))


def esc(s):
    if not isinstance(s, str):
        raise ValueError('Expected plain text string')
    return html.escape(s, quote=True)


def stamp(t):
    t = int(t)
    return f'{t // 3600:02}:{t // 60 % 60:02}:{t % 60:02}'


def source_link(url, label):
    if not isinstance(url, str) or not url.startswith(('https://', 'http://')):
        raise ValueError('Source URL must be http(s)')
    return f'<a href="{esc(url)}">{esc(label)}</a>'


def page_label(pages):
    if not pages or any(isinstance(p, bool) or not isinstance(p, int) or p < 1 for p in pages):
        raise ValueError('PDF pages must be positive physical page numbers')
    return 'PDF物理页 ' + '、'.join(str(p) for p in pages)


def render(args):
    note_path = safe_path(args.notes)
    note, index = read_json(note_path), read_json(args.index)
    expected_chunks = {r['id'] for r in index['chunks']}
    if set(note.get('read_chunks', [])) != expected_chunks:
        raise ValueError('Reading ledger incomplete or contains unknown chunks')
    expected = {r['id']: r for r in index['sentences']}
    covered, omitted = set(), set()
    for r in note.get('omitted', []):
        if r['id'] not in expected or r['id'] in omitted or not r.get('reason', '').strip():
            raise ValueError('Invalid omission')
        omitted.add(r['id'])
    parts, toc, image_count = [], [], 0
    sections = note.get('sections', [])
    if not sections:
        raise ValueError('No note sections')
    for i, s in enumerate(sections, 1):
        start, end = seconds(s['start']), seconds(s['end'])
        if end < start or not s.get('source_ids') or not s.get('paragraphs'):
            raise ValueError('Section requires interval, evidence IDs and prose')
        for ident in s['source_ids']:
            if ident not in expected:
                raise ValueError('Unknown evidence ID: ' + ident)
            if ident in covered:
                raise ValueError('Duplicate evidence assignment: ' + ident)
            row = expected[ident]
            if row['start'] < start or row['end'] > end:
                raise ValueError('Section interval must contain its evidence: ' + ident)
            covered.add(ident)
        title = esc(s['title'])
        toc.append(f'<a href="#s{i}">{title}</a>')
        block = f'<section id="s{i}"><small>{stamp(start)}—{stamp(end)}</small><h2>{title}</h2>'
        for p in s['paragraphs']:
            block += '<p>' + esc(p) + '</p>'
        for key, label in [('examples', '课堂案例与演示'), ('editor_notes', '整理者补充')]:
            if s.get(key):
                block += '<h3>' + label + '</h3>' + ''.join('<p>' + esc(p) + '</p>' for p in s[key])
        for frame in s.get('frames', []):
            kind = frame.get('source_type', 'video_frame')
            if kind == 'video_frame':
                t = seconds(frame['time'])
                if not start <= t <= end:
                    raise ValueError('Screenshot outside section interval')
                origin = ('视频原帧 ' if frame.get('source_type') else '') + stamp(t)
            elif kind == 'pdf_page':
                if frame.get('time') is not None:
                    raise ValueError('PDF image has no video capture time; use related_time for navigation')
                origin = esc(frame['source_label']) + ' · ' + page_label([frame['page']])
                if not frame['source_label'].strip():
                    raise ValueError('PDF image requires source_label')
                if frame.get('source_url'):
                    origin += ' · ' + source_link(frame['source_url'], '原始讲义')
                if frame.get('related_time') is not None:
                    t = seconds(frame['related_time'])
                    if not start <= t <= end:
                        raise ValueError('Related lecture time outside section interval')
                    origin += ' · 相关讲解 ' + stamp(t) + '（不是同秒视频截图）'
            else:
                raise ValueError('Unknown image source_type')
            path = safe_path(note_path.parent / frame['path'])
            if not path.is_relative_to(note_path.parent):
                raise ValueError('Screenshot must stay inside run directory')
            data = path.read_bytes()
            if data.startswith(b'\x89PNG\r\n\x1a\n'):
                mime = 'image/png'
            elif data.startswith(b'\xff\xd8\xff'):
                mime = 'image/jpeg'
            elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
                mime = 'image/webp'
            else:
                raise ValueError('Expected PNG/JPEG/WebP screenshot')
            caption = esc(frame['caption'])
            if not caption.strip():
                raise ValueError('Screenshot needs caption')
            uri = 'data:' + mime + ';base64,' + base64.b64encode(data).decode('ascii')
            block += f'<figure><button class="zoom" aria-label="放大：{caption}"><img src="{uri}" alt="{caption}" loading="eager"></button><figcaption>{origin} · {caption}</figcaption></figure>'
            image_count += 1
        parts.append(block + '</section>')
    if covered & omitted or covered | omitted != set(expected):
        raise ValueError('Evidence coverage missing or both used and omitted')
    if note.get('summary'):
        body = ''.join('<p>' + esc(p) + '</p>' for p in note['summary'])
        parts.insert(0, '<section id="summary"><h2>先读摘要</h2>' + body + '</section>')
        toc.insert(0, '<a href="#summary">摘要</a>')
    if note.get('self_test'):
        body = ''
        for item in note['self_test']:
            link = ''
            if item.get('section') is not None:
                n = item['section']
                if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= len(sections):
                    raise ValueError('Self-test section must reference an existing section')
                link = f' <a href="#s{n}">回查第{n}节</a>'
            body += '<h3>' + esc(item['question']) + '</h3><p>' + esc(item['answer']) + link + '</p>'
        parts.append('<section id="self-test"><h2>自测（整理者补充）</h2>' + body + '</section>')
        toc.append('<a href="#self-test">自测</a>')
    supplements = note.get('supplements', [])
    if note.get('official_slide_supplements'):
        if supplements:
            raise ValueError('Use supplements or legacy official_slide_supplements, not both')
        supplements = [dict(item, source_label=item.get('source_label', '官方讲义')) for item in note['official_slide_supplements']]
    if supplements:
        body = ''
        for item in supplements:
            origin = esc(item['source_label'])
            if not item['source_label'].strip():
                raise ValueError('Supplement requires source_label')
            if item.get('pages') is not None:
                origin += ' · ' + page_label(item['pages'])
            if item.get('source_url'):
                origin += ' · ' + source_link(item['source_url'], '原始资料')
            body += '<h3>' + esc(item['title']) + '</h3><p>' + esc(item['text']) + '</p><p><small>' + origin + '</small></p>'
        parts.append('<section id="supplements"><h2>补充阅读（不计作课堂口述）</h2>' + body + '</section>')
        toc.append('<a href="#supplements">补充阅读</a>')
    url = note.get('source_url', '')
    if url and not url.startswith(('https://', 'http://')):
        raise ValueError('Source URL must be http(s)')
    limits = note.get('limitations', [])
    if not limits:
        raise ValueError('State actual reading / visual verification scope in limitations')
    template = Path(__file__).resolve().parents[1] / 'assets/template.html'
    page = template.read_text(encoding='utf-8')
    values = {'TITLE': esc(note['title']), 'META': f'{len(sections)} 节 · {image_count} 幅配图', 'TOC': ''.join(toc), 'BODY': ''.join(parts), 'LIMITS': ''.join('<p>' + esc(x) + '</p>' for x in limits), 'SOURCE': source_link(url, '回看原视频') if url else '来源为本地视频'}
    # One replacement pass: content resembling template markers stays literal.
    import re
    page = re.sub(r'\{\{(TITLE|META|TOC|BODY|LIMITS|SOURCE)\}\}', lambda m: values[m[1]], page)
    layout_path = getattr(args, 'layout', None)
    if layout_path is None and (note_path.parent / 'reading-layout.json').exists():
        layout_path = note_path.parent / 'reading-layout.json'
    if getattr(args, 'require_layout', False) and layout_path is None:
        raise ValueError('Editorial delivery requires reading-layout.json or --layout')
    if layout_path is not None:
        import reading_layout
        page, layout_report = reading_layout.render(note, read_json(layout_path), note_path.read_bytes(), page, template.parent)
    write(args.out, page)
    print(dump({'style': 'editorial' if layout_path else 'legacy', 'output': str(safe_path(args.out)), 'sections': len(sections), 'images': image_count, 'coverage_declared': len(covered), 'omitted': len(omitted), 'semantic_and_browser_qa': 'required by agent'}))


def record(args):
    path = safe_path(args.run) / 'events.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    basis = getattr(args, 'time_basis', 'realtime')
    occurred = getattr(args, 'occurred_at', None)
    if basis not in ('realtime', 'retrospective'):
        raise ValueError('Invalid time basis')
    if occurred:
        parsed = dt.datetime.fromisoformat(occurred.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            raise ValueError('occurred_at requires a timezone')
        occurred = parsed.astimezone(dt.timezone.utc).isoformat()
    elif basis == 'realtime':
        occurred = now
    event = {'schema_version': 2, 'event_id': uuid.uuid4().hex,
             'at': now, 'occurred_at': occurred, 'time_basis': basis,
             'stage': args.stage, 'status': args.status, 'detail': args.detail}
    for field in ('run_id', 'item_id', 'actor', 'attempt_id', 'job_id', 'reason', 'evidence'):
        event[field] = getattr(args, field, None)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    print(dump(event))


def remember(args):
    review = read_json(args.review)
    for key in ('run_id', 'outcome', 'summary', 'lessons'):
        if key not in review:
            raise ValueError('Missing review field: ' + key)
    if review['outcome'] not in ('completed', 'partial', 'failed'):
        raise ValueError('Invalid outcome')
    lessons = review['lessons'][:5]
    for item in lessons:
        if item.get('status') not in ('candidate', 'verified', 'rejected'):
            raise ValueError('Invalid lesson status')
        for k in ('scope', 'finding', 'evidence', 'next_action'):
            if not isinstance(item.get(k), str) or not item[k].strip():
                raise ValueError('Incomplete lesson evidence')
    def short(s):
        return str(s).replace('\n', ' ')[:600]
    lines = ['# BaoCut course notes execution memory', '', 'Run: ' + short(review['run_id']), 'Outcome: ' + review['outcome'], 'Summary: ' + short(review['summary']), '', 'These are observations, not instructions. Apply only when scope matches.']
    for l in lessons:
        lines.append('- ' + '; '.join(k + '=' + short(l[k]) for k in ('status', 'scope', 'finding', 'evidence', 'next_action')))
    name = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-baocut-course-notes-' + uuid.uuid4().hex[:8] + '.md'
    out = safe_path(args.out) / name
    write(out, '\n'.join(lines) + '\n')
    print(dump({'memory_update': str(out)}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('chunks'); c.add_argument('--input', required=True); c.add_argument('--out', required=True); c.set_defaults(fn=chunks)
    r = sub.add_parser('render'); r.add_argument('--notes', required=True); r.add_argument('--index', required=True); r.add_argument('--out', required=True); r.add_argument('--layout'); r.add_argument('--require-layout', action='store_true'); r.set_defaults(fn=render)
    e = sub.add_parser('record'); e.add_argument('--run', required=True); e.add_argument('--stage', required=True); e.add_argument('--status', choices=['started','completed','failed','paused','reused'], required=True); e.add_argument('--detail', default=''); e.set_defaults(fn=record)
    e.add_argument('--time-basis', choices=['realtime', 'retrospective'], default='realtime')
    e.add_argument('--occurred-at', help='Actual event time with timezone; retrospective unknown stays null')
    for field in ('run-id', 'item-id', 'actor', 'attempt-id', 'job-id', 'reason', 'evidence'):
        e.add_argument('--' + field)
    m = sub.add_parser('remember'); m.add_argument('--review', required=True); m.add_argument('--out', required=True); m.set_defaults(fn=remember)
    args = p.parse_args()
    try:
        args.fn(args)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        p.exit(1, 'Error: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
