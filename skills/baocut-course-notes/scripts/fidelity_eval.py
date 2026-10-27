#!/usr/bin/env python3
"""Score a fidelity eval: precision (what the notes say is supported) and recall
(what the lecture taught can be answered from the notes). The judgments come from
reviewers; this script checks binding, coverage and arithmetic, never the semantics."""
import argparse
import hashlib
import re

from course_notes import dump, read_json, safe_path
from reading_layout import FIELDS, supplements

PRECISION = {'supported': 1.0, 'partial': 0.5, 'unsupported': 0.0, 'distorted': 0.0}
RECALL = {'correct': 1.0, 'partial': 0.5, 'missing': 0.0, 'wrong': 0.0}
ROLES = ('independent_agent', 'human', 'same_agent')
DEFAULTS = {'min_precision': 0.95, 'min_recall': 0.85, 'min_questions': 20}


def refs_in(notes):
    """Every reference a precision item may point at."""
    refs = set()
    if notes.get('map'):
        refs.add('map')
    for i, s in enumerate(notes['sections'], 1):
        refs.update({f's{i}:takeaway', f's{i}:title'})
        if s.get('visual'):
            refs.add(f's{i}:visual')
        for kind, field in FIELDS.items():
            refs.update(f's{i}:{kind}{j}' for j in range(len(s.get(field, []))))
    refs.update(f'x{j}' for j in range(len(supplements(notes))))
    refs.update(f'q{j}' for j in range(1, len(notes.get('self_test', [])) + 1))
    refs.update(f'summary{j}' for j in range(len(notes.get('summary', []))))
    return refs


def score(report, notes, limits=None):
    limits = {**DEFAULTS, **(limits or {})}
    if report.get('schema_version') != 1:
        raise ValueError('Expected fidelity eval schema_version 1')
    problems = []
    known = refs_in(notes)
    precision = report.get('precision') or {}
    p_items = precision.get('items') or []
    for item in p_items:
        if item.get('ref') not in known:
            raise ValueError('Precision item points at unknown ref: ' + str(item.get('ref')))
        if item.get('verdict') not in PRECISION:
            raise ValueError('Invalid precision verdict for ' + item['ref'])
        if not isinstance(item.get('evidence'), str) or not item['evidence'].strip():
            raise ValueError('Precision item needs the source evidence it was checked against: ' + item['ref'])
    checked = {i['ref'] for i in p_items}
    top_layer = {r for r in known if r == 'map' or re.fullmatch(r's\d+:(takeaway|visual)', r)}
    unchecked = sorted(top_layer - checked)
    if unchecked:
        problems.append('Every takeaway and explainer must be checked; missing: ' + ', '.join(unchecked))
    bad_top = sorted(i['ref'] for i in p_items if i['ref'] in top_layer and i['verdict'] in ('unsupported', 'distorted'))
    if bad_top:
        problems.append('Unsupported or distorted takeaway/explainer: ' + ', '.join(bad_top))
    recall = report.get('recall') or {}
    r_items = recall.get('items') or []
    for item in r_items:
        for key in ('id', 'question', 'expected', 'evidence'):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError('Recall item needs id, question, expected answer and transcript/frame evidence')
        if item.get('verdict') not in RECALL or item.get('from') not in ('transcript', 'visual'):
            raise ValueError('Invalid recall verdict/from for ' + item['id'])
    if len(r_items) < limits['min_questions']:
        problems.append(f'Only {len(r_items)} recall questions; need at least {limits["min_questions"]}')
    if any(s.get('frames') for s in notes['sections']) and not any(i['from'] == 'visual' for i in r_items):
        problems.append('Notes use frames but no recall question was drawn from the visuals')
    p_score = round(sum(PRECISION[i['verdict']] for i in p_items) / len(p_items), 4) if p_items else None
    r_score = round(sum(RECALL[i['verdict']] for i in r_items) / len(r_items), 4) if r_items else None
    if p_score is None or p_score < limits['min_precision']:
        problems.append(f'Precision {p_score} below {limits["min_precision"]}')
    if r_score is None or r_score < limits['min_recall']:
        problems.append(f'Recall {r_score} below {limits["min_recall"]}')
    roles = [precision.get('reviewer'), recall.get('question_author'), recall.get('answerer')]
    if any(r not in ROLES for r in roles):
        raise ValueError('reviewer, question_author and answerer must each be one of ' + ', '.join(ROLES))
    if problems:
        status = 'failed'
    elif 'same_agent' in roles:
        status = 'self_checked'
    else:
        status = 'passed'
    misses = [i['id'] for i in r_items if i['verdict'] in ('missing', 'wrong')]
    return {'status': status, 'precision': p_score, 'recall': r_score,
            'precision_items': len(p_items), 'recall_items': len(r_items),
            'recall_misses': misses, 'problems': problems, 'roles': roles,
            'claim': 'Scores restate reviewer judgments; they do not prove the reviewers read everything.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notes', required=True)
    parser.add_argument('--eval', required=True)
    for key, value in DEFAULTS.items():
        parser.add_argument('--' + key.replace('_', '-'), type=type(value), default=value)
    args = parser.parse_args()
    try:
        notes_path = safe_path(args.notes)
        report = read_json(args.eval)
        if report.get('notes_sha256') != hashlib.sha256(notes_path.read_bytes()).hexdigest():
            raise ValueError('Eval is bound to a different notes.json; rerun it on the current notes')
        result = score(report, read_json(notes_path), {k: getattr(args, k) for k in DEFAULTS})
        print(dump(result))
        if result['status'] == 'failed':
            parser.exit(2)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.exit(1, 'Error: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
