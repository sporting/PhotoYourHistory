import json
import os
import sqlite3
import tempfile
import unittest

from tools.AuditPhotoIndex import audit, open_read_only_database
from synology.FileParser import ImageFileHelper


class IndexIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.temp.name, 'photos')
        os.makedirs(os.path.join(self.root, 'nested', '@eaDir'))
        self.db_path = os.path.join(self.temp.name, 'SaPhoto.db')
        connection = sqlite3.connect(self.db_path)
        connection.executescript('''
            CREATE TABLE PHOTOS (
                ID INTEGER PRIMARY KEY, FILE_NAME TEXT, ROOT_DIR TEXT, DIR TEXT,
                META TEXT, PHOTO_UTC_TS INTEGER
            );
            CREATE TABLE VIDEOS (
                ID INTEGER PRIMARY KEY, FILE_NAME TEXT, ROOT_DIR TEXT, DIR TEXT
            );
            CREATE TABLE PARSER_DIRECTORY (DIR TEXT, ROOT_DIR INTEGER);
        ''')
        connection.execute('INSERT INTO PARSER_DIRECTORY VALUES (?, 1)', (self.root,))
        connection.execute(
            'INSERT INTO PHOTOS VALUES (1, ?, ?, ?, ?, ?)',
            ('indexed.jpg', self.root, self.root, '{}', 1),
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp.cleanup()

    def touch(self, relative_name):
        path = os.path.join(self.root, relative_name)
        with open(path, 'wb'):
            pass

    def test_parser_scans_nested_files_once_and_skips_synology_metadata(self):
        self.touch('indexed.jpg')
        self.touch('nested/new.JPG')
        self.touch('nested/@eaDir/ignored.jpg')
        files = list(ImageFileHelper().getFiles(self.root, None, True))
        self.assertEqual(2, len(files))
        self.assertTrue(any(path.endswith('new.JPG') for path in files))

    def test_audit_is_read_only_and_reports_files_missing_from_db(self):
        self.touch('indexed.jpg')
        self.touch('nested/new.JPG')
        before = os.stat(self.db_path).st_mtime_ns
        output = os.path.join(self.temp.name, 'audit')

        summary = audit(self.db_path, [], output)

        self.assertEqual(1, summary['comparison']['image_files_missing_from_db_count'])
        self.assertEqual(before, os.stat(self.db_path).st_mtime_ns)
        with open(os.path.join(output, 'audit_summary.json'), encoding='utf-8') as report:
            self.assertEqual(1, json.load(report)['comparison']['image_files_missing_from_db_count'])
        connection = open_read_only_database(self.db_path)
        with self.assertRaises(sqlite3.OperationalError):
            connection.execute("INSERT INTO PHOTOS VALUES (2, 'x.jpg', 'x', 'x', '{}', 1)")
        connection.close()


if __name__ == '__main__':
    unittest.main()

