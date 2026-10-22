import copy
import json
from pathlib import Path
import tempfile
import unittest

from validate_image_audit import digest, validate


class ImageAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # File bytes suffice: this validator deliberately does not certify pixels.
        (self.root / 'frame.png').write_bytes(b'image-version-1')
        (self.root / 'slides.pdf').write_bytes(b'source-version-1')
        self.notes = self.root / 'notes.json'
        self.notes.write_text(json.dumps({'sections': [{'frames': [{'path': 'frame.png'}]}]}))
        self.record = {'section': 1, 'frame': 1, 'path': 'frame.png',
                       'sha256': digest(self.root / 'frame.png'),
                       'purpose': 'Explain a three-stage process',
                       'expected_information': 'Three stages and two arrows',
                       'observed_information': 'All stages and arrows visible',
                       'comparison_evidence': 'Compared against PDF page 3',
                       'sources': [{'path': 'slides.pdf', 'sha256': digest(self.root / 'slides.pdf'),
                                    'detail': 'Physical page 3'}],
                       'status': 'passed', 'known_gap': False, 'resolution': 'Replaced and reviewed'}
        self.audit = {'schema_version': 1, 'notes_sha256': digest(self.notes),
                      'images': [self.record]}

    def check(self, passed=False):
        path = self.root / 'image-audit.json'
        path.write_text(json.dumps(self.audit))
        result = validate(self.notes, path)
        self.assertEqual(result['status'], 'passed' if passed else 'blocked', result)

    def test_complete_current_record_passes(self):
        self.check(passed=True)

    def test_stale_notes_cannot_reuse_review(self):
        self.notes.write_text(self.notes.read_text() + '\n')
        self.check()

    def test_replaced_image_requires_new_review(self):
        (self.root / 'frame.png').write_bytes(b'new-image')
        self.check()

    def test_changed_source_requires_new_comparison(self):
        (self.root / 'slides.pdf').write_bytes(b'new-source')
        self.check()

    def test_missing_record_blocks(self):
        self.audit['images'] = []
        self.check()

    def test_duplicate_record_does_not_cover_missing_image(self):
        self.notes.write_text(json.dumps({'sections': [{'frames': [{'path': 'frame.png'}, {'path': 'frame.png'}]}]}))
        self.audit['notes_sha256'] = digest(self.notes)
        self.audit['images'].append(copy.deepcopy(self.record))
        self.check()

    def test_pending_or_known_gap_blocks_even_with_hashes(self):
        for field, value in [('status', 'pending'), ('known_gap', True), ('known_gap', None)]:
            with self.subTest(field=field, value=value):
                original = self.record[field]
                self.record[field] = value
                self.check()
                self.record[field] = original

    def test_each_check_must_be_nonempty(self):
        for field in ('purpose', 'expected_information', 'observed_information', 'comparison_evidence', 'resolution'):
            with self.subTest(field=field):
                original = self.record[field]
                self.record[field] = ' '
                self.check()
                self.record[field] = original

    def test_wrong_path_and_missing_source_block(self):
        self.record['path'] = 'different.png'
        self.record['sources'] = []
        self.check()


if __name__ == '__main__':
    unittest.main()
