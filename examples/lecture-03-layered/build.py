#!/usr/bin/env python3
"""Rebuild lecture 3 as a notes-v3 layered page for side-by-side comparison.

Every full-note text, frame, supplement, self-test item and limitation is migrated
verbatim from notes/lecture-03/课堂笔记.html (the 2026-10-22 delivered version).
Only layer.json and visuals/*.svg are new. A migration check fails the build if any
original text block is missing from the new page.
"""
import argparse
import base64
import html
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'skills/baocut-course-notes/scripts'))
import layered  # noqa: E402

ORIGINAL = REPO / 'notes/lecture-03/课堂笔记.html'
HERE = Path(__file__).resolve().parent


def text(fragment):
    """Visible text of a generated HTML fragment (tags dropped, entities decoded)."""
    return html.unescape(re.sub(r'<[^>]+>', '', fragment))


def seconds(stamp):
    h, m, s = (int(x) for x in stamp.split(':'))
    return h * 3600 + m * 60 + s


def strongs(fragment):
    return [html.unescape(x) for x in re.findall(r'<strong>(.*?)</strong>', fragment)]


def parse(page, frame_dir):
    head = {
        'title': text(re.search(r'<title>(.*?)</title>', page).group(1)),
        'course_title': text(re.search(r'<div class="masthead"><b>(.*?)</b>', page).group(1)),
        'issue': text(re.search(r'<div class="hero-kicker">LECTURE (.*?)</div>', page).group(1)),
        'heading': text(re.search(r'<h1>(.*?)</h1>', page).group(1)),
        'subtitle': text(re.search(r'<p class="hero-subtitle">(.*?)</p>', page).group(1)),
        'source_url': html.unescape(re.search(r'<div class="hero-meta"><span>.*?</span><a href="(.*?)">', page).group(1)),
    }
    limits = [text(p) for p in re.findall(r'<p>(.*?)</p>', re.search(r'<aside>(.*?)</aside>', page, re.S).group(1))]
    summary_block = re.search(r'<section id="summary">(.*?)</section>', page, re.S).group(1)
    summary = re.findall(r'<p class="summary-item">(.*?)</p>', summary_block)
    toc = re.search(r'<nav aria-label="课程目录">(.*?)</nav>', page, re.S).group(1)
    groups, shorts, n = [], [], 0
    for item in re.findall(r'(<div class="toc-group">.*?</div>|<a href="#s\d+"><span>\d+</span>.*?</a>)', toc):
        kind, value = ('g', text(item)) if item.startswith('<div') else ('s', text(re.sub(r'<span>\d+</span>', '', item)))
        if kind == 'g':
            if value != '复习':
                groups.append({'start': n + 1, 'label': value})
        else:
            n += 1
            shorts.append(value)
    notes = {'schema_version': 3, **head, 'limitations': limits,
             'summary_title': text(re.search(r'<h2>(.*?)</h2>', summary_block).group(1)),
             'summary': [text(p) for p in summary], 'summary_terms': list(dict.fromkeys(sum((strongs(p) for p in summary), []))),
             'groups': groups, 'sections': [], 'supplements': [], 'self_test': []}
    supplements = {}
    for i, block in enumerate(re.findall(r'<section id="s\d+">.*?</section>', page, re.S), 1):
        start, end = re.search(r'<small>(\d\d:\d\d:\d\d)—(\d\d:\d\d:\d\d) · 课堂时间</small>', block).groups()
        section = {'title': text(re.search(r'<h2>(.*?)</h2>', block).group(1)), 'short': shorts[i - 1],
                   'takeaway': text(re.search(r'<div class="section-takeaway">.*?<p>(.*?)</p>', block, re.S).group(1)),
                   'start': seconds(start), 'end': seconds(end), 'terms': [], 'flow': '',
                   'paragraphs': [], 'examples': [], 'editor_notes': [], 'frames': []}
        tokens, terms = [], []
        units = re.finditer(r'<p (?:class="[^"]*" )?data-content="(s\d+:([pen])(\d+)|x(\d+))">(.*?)</p>|<figure data-frame="(\d+):(\d+)">(.*?)</figure>|<div class="inline-reading" id="supplement-(\d+)">(.*?)<p data-content="x\d+">', block, re.S)
        for m in units:
            if m.group(9) is not None:  # supplement header; its text paragraph follows
                head_html = m.group(10)
                k = int(m.group(9))
                supplements[k] = {'title': text(re.search(r'<h3>(.*?)</h3>', head_html).group(1)),
                                  'source_label': text(re.search(r'<div class="source-tag">(.*?)</div>', head_html).group(1))}
                bridge = re.search(r'<p class="bridge">整理者衔接：(.*?)</p>', head_html)
                if bridge:
                    notes.setdefault('bridges', {})[f'x{k}'] = text(bridge.group(1))
                tail = block[m.end():block.index('</div>', m.end())]
                pages = re.search(r'PDF物理页 ([\d、]+)', tail)
                if pages:
                    supplements[k]['pages'] = [int(x) for x in pages.group(1).split('、')]
                url = re.search(r'<a href="(.*?)">原始资料', tail)
                if url:
                    supplements[k]['source_url'] = html.unescape(url.group(1))
                body = re.match(r'(.*?)</p>', block[m.end():], re.S).group(1)
                supplements[k]['text'] = text(body)
                terms += strongs(body)
                tokens.append(f'x{k}')
            elif m.group(1) and m.group(1).startswith('s'):
                field = {'p': 'paragraphs', 'e': 'examples', 'n': 'editor_notes'}[m.group(2)]
                inner = m.group(5)
                inner = re.sub(r'^<span class="(source-tag|example-label)">.*?</span>(<br>)?', '', inner)
                assert int(m.group(3)) == len(section[field]), 'content order changed'
                section[field].append(text(inner))
                terms += strongs(inner)
                tokens.append(m.group(2) + m.group(3))
            elif m.group(6) is not None:
                fig = m.group(0)
                uri = re.search(r'<img src="data:(image/[a-z]+);base64,([^"]+)"', fig)
                ext = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp'}[uri.group(1)]
                path = frame_dir / f's{i:02d}-{m.group(7)}.{ext}'
                path.write_bytes(base64.b64decode(uri.group(2)))
                caption = html.unescape(re.search(r'alt="(.*?)"', fig).group(1))
                provenance = text(re.search(r'<summary>来源与时间</summary><p>(.*?)</p>', fig).group(1))
                assert provenance.startswith('视频原帧 '), 'only video frames expected in lecture 3'
                section['frames'].append({'source_type': 'video_frame', 'path': f'frames/{path.name}',
                                          'time': seconds(provenance.split()[1]), 'caption': caption})
                tokens.append(f'f{m.group(7)}')
        section['flow'] = ' '.join(tokens)
        section['terms'] = list(dict.fromkeys(terms))
        notes['sections'].append(section)
    notes['supplements'] = [supplements[k] for k in sorted(supplements)]
    for q, a in re.findall(r'<h3 id="q\d+">(.*?)</h3>.*?<div class="answer-label">.*?</div><p>(.*?)</p>', page, re.S):
        link = re.search(re.escape(q) + r'.*?回查第 (\d+) 节', page, re.S)
        notes['self_test'].append({'question': text(q), 'answer': text(a), 'section': int(link.group(1))})
    return notes


def original_blocks(page):
    """Every text unit a reader could see in the original page."""
    blocks = [text(x) for x in re.findall(r'<p (?:class="[^"]*" )?data-content="[^"]+">(.*?)</p>', page)]
    blocks = [re.sub(r'^(整理者说明|案例回扣)', '', b) for b in blocks]
    blocks += [text(x) for x in re.findall(r'<h2>(.*?)</h2>', page)]
    blocks += [text(x) for x in re.findall(r'<div class="section-takeaway">.*?<p>(.*?)</p>', page, re.S)]
    blocks += [html.unescape(x) for x in re.findall(r'<img src="data:[^"]+" alt="(.*?)"', page)]
    blocks += [text(x) for x in re.findall(r'<summary>来源与时间</summary><p>(.*?)</p>', page)]
    blocks += [text(x) for x in re.findall(r'<p class="summary-item">(.*?)</p>', page)]
    blocks += [text(x) for x in re.findall(r'<h3[^>]*>(.*?)</h3>', page)]
    blocks += [text(x) for x in re.findall(r'<div class="answer-label">.*?</div><p>(.*?)</p>', page, re.S)]
    blocks += [text(x) for x in re.findall(r'<p>(.*?)</p>', re.search(r'<aside>(.*?)</aside>', page, re.S).group(1))]
    return [b for b in blocks if b.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=str(HERE / '课堂笔记-分层样板.html'))
    args = parser.parse_args()
    page = ORIGINAL.read_text(encoding='utf-8')
    layer = json.loads((HERE / 'layer.json').read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp)
        (run / 'frames').mkdir()
        notes = parse(page, run / 'frames')
        shutil.copytree(HERE / 'visuals', run / 'visuals')
        notes['limitations'].append(layer['limitation'])
        notes['map'] = layer['map']
        for number, visual in layer['visuals'].items():
            notes['sections'][int(number) - 1]['visual'] = visual
        (HERE / 'notes.json').write_text(json.dumps(notes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result, report = layered.render(notes, run)
    new_text = text(re.sub(r'<(script|style)>.*?</\1>', '', result, flags=re.S))
    new_alts = set(html.unescape(x) for x in re.findall(r'alt="(.*?)"', result))
    missing = [b for b in original_blocks(page) if b not in new_text and b not in new_alts]
    if missing:
        sys.exit('Migration check failed; missing blocks:\n' + '\n'.join(missing[:10]))
    old_frames = re.findall(r'<img src="(data:image/[^"]+)"', page)
    new_frames = set(re.findall(r'<img src="(data:image/(?:png|jpeg|webp)[^"]+)"', result))
    if any(f not in new_frames for f in old_frames):
        sys.exit('Migration check failed: a frame image changed or went missing')
    Path(args.out).write_text(result, encoding='utf-8')
    print(json.dumps({'output': args.out, 'original_text_blocks_checked': len(original_blocks(page)),
                      'original_frames_checked': len(old_frames), **report}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
