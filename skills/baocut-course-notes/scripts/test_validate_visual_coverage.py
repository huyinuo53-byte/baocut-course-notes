import json
import tempfile
import unittest
from pathlib import Path
from validate_visual_coverage import digest, validate


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('video.mp4', 'frame.png', 'slides.pdf'):
            (self.root / name).write_bytes(name.encode())
        self.notes = self.root / 'notes.json'
        self.notes.write_text(json.dumps({'sections': [{'frames': [{'path': 'frame.png', 'source_type': 'video_frame'}]}]}))
        inventory = {'media_sha256': digest(self.root / 'video.mp4'), 'candidates': [dict(id='v1', time=1, **self.file('frame.png'))]}
        (self.root / 'visual-inventory.json').write_text(json.dumps(inventory))
        self.coverage = {'schema_version': 1, 'notes_sha256': digest(self.notes), 'status': 'passed', 'known_gaps': [],
                         'inventory': self.file('visual-inventory.json'),
                         'media': dict(duration_seconds=10, video_duration_seconds=10, tail_decode='passed', **self.file('video.mp4')),
                         'method': 'test fixture only', 'reviewed_windows': [{'start': 0, 'end': 10, 'evidence': 'fixture'}],
                         'states': [{'candidate_id': 'v1', 'disposition': 'included', 'description': 'test', 'evidence': 'test', 'known_gap': False, 'targets': [{'section': 1, 'frame': 1}]}]}

    def file(self, name):
        return {'path': name, 'sha256': digest(self.root / name)}

    def result(self):
        path = self.root / 'visual-coverage.json'
        path.write_text(json.dumps(self.coverage))
        return validate(self.notes, path)['status']

    def test_valid(self):
        self.assertEqual(self.result(), 'passed')

    def test_missing_candidate(self):
        self.coverage['states'] = []
        self.assertEqual(self.result(), 'blocked')

    def test_pending_gap(self):
        self.coverage['states'][0]['disposition'] = 'known_gap'
        self.assertEqual(self.result(), 'blocked')

    def test_stale_notes(self):
        self.notes.write_text(self.notes.read_text() + ' ')
        self.assertEqual(self.result(), 'blocked')

    def test_incomplete_video(self):
        self.coverage['media']['video_duration_seconds'] = 3
        self.assertEqual(self.result(), 'blocked')

    def test_window_gap(self):
        self.coverage['reviewed_windows'][0]['start'] = 2
        self.assertEqual(self.result(), 'blocked')

    def test_invalid_target(self):
        self.coverage['states'][0]['targets'][0]['frame'] = 5
        self.assertEqual(self.result(), 'blocked')

    def test_cyclic_duplicate(self):
        self.coverage['states'][0].update(disposition='duplicate', duplicate_of='v1')
        self.assertEqual(self.result(), 'blocked')

    def test_missing_pdf_page(self):
        self.coverage['pdf'] = dict(page_count=2, **self.file('slides.pdf'))
        self.coverage['pdf_pages'] = [{'page': 1, 'disposition': 'transition', 'reason': 'title'}]
        self.assertEqual(self.result(), 'blocked')


if __name__ == '__main__':
    unittest.main()
