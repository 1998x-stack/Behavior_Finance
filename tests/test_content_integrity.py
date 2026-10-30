"""Isolated regression tests for lossless course management."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import main


class ContentIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_existing_course_is_never_overwritten(self):
        relative = next(main.expected_lessons())
        target = self.root / relative
        target.parent.mkdir(parents=True)
        original = '# Original\nPRIVATE NOTES MUST SURVIVE\n'
        target.write_text(original, encoding='utf-8')
        previous = hashlib.sha256(target.read_bytes()).hexdigest()
        main.initialize(self.root)
        main.initialize(self.root)
        self.assertEqual(previous, hashlib.sha256(target.read_bytes()).hexdigest())
        self.assertEqual(original, target.read_text(encoding='utf-8'))

    def test_audit_is_read_only_and_classifies_placeholders(self):
        main.initialize(self.root)
        first = self.root / next(main.expected_lessons())
        first.write_text('# Title\n' + ('Useful explanation. ' * 10), encoding='utf-8')
        before = {p.relative_to(self.root).as_posix(): p.read_bytes()
                  for p in self.root.rglob('*.md')}
        report = main.audit(self.root)
        self.assertEqual(report['expected'], len(list(main.expected_lessons())))
        self.assertEqual(report['substantive'], 1)
        self.assertEqual(len(report['placeholders']), report['expected'] - 1)
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): p.read_bytes()
                                  for p in self.root.rglob('*.md')})

    def test_dry_run_creates_nothing(self):
        result = main.initialize(self.root, dry_run=True)
        self.assertEqual(len(result['created']), len(list(main.expected_lessons())))
        self.assertFalse(list(self.root.iterdir()))

    def test_backup_roundtrip_and_no_overwrite(self):
        main.initialize(self.root)
        (self.root / 'README.md').write_text('README is protected', encoding='utf-8')
        archive = self.root / 'snapshot.zip'
        result = main.backup(self.root, archive)
        self.assertTrue(result['verified'])
        self.assertEqual(result['files'], len(list(main.expected_lessons())) + 1)
        self.assertTrue(main.verify_backup(archive)['valid'])
        with self.assertRaises(FileExistsError):
            main.backup(self.root, archive)

    def test_corrupt_backup_is_rejected(self):
        archive = self.root / 'corrupt.zip'
        manifest = {'schema_version': 1, 'files': [{'path': 'a.md', 'bytes': 3,
                        'sha256': hashlib.sha256(b'abc').hexdigest()}]}
        with ZipFile(archive, 'w', ZIP_DEFLATED) as output:
            output.writestr('a.md', b'abd')
            output.writestr('backup-manifest.json', json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'integrity'):
            main.verify_backup(archive)

    def test_archive_path_traversal_is_rejected(self):
        archive = self.root / 'invalid.zip'
        manifest = {'schema_version': 1, 'files': [{'path': '../escape.md', 'bytes': 1,
                        'sha256': hashlib.sha256(b'x').hexdigest()}]}
        with ZipFile(archive, 'w', ZIP_DEFLATED) as output:
            output.writestr('../escape.md', b'x')
            output.writestr('backup-manifest.json', json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            main.verify_backup(archive)

    def test_existing_readme_is_preserved(self):
        readme = self.root / 'README.md'
        readme.write_text('# Hand-written README', encoding='utf-8')
        main.initialize(self.root)
        self.assertEqual(readme.read_text(encoding='utf-8'), '# Hand-written README')


if __name__ == '__main__':
    unittest.main()
