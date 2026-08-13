import json
import os
import sqlite3
import tempfile
import unittest

from tools.AuditPhotoIndex import audit, open_read_only_database


class AuditPhotoIndexTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.temporary_directory.name, 'photos')
        os.makedirs(self.root)
        self.database_path = os.path.join(self.temporary_directory.name, 'SaPhoto.db')
        self.output_directory = os.path.join(self.temporary_directory.name, 'report')
        self._create_database()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _create_database(self):
        connection = sqlite3.connect(self.database_path)
        connection.executescript('''
            CREATE TABLE PHOTOS (ID INTEGER PRIMARY KEY, DIR TEXT, FILE_NAME TEXT, META TEXT, PHOTO_UTC_TS INTEGER);
            CREATE TABLE VIDEOS (ID INTEGER PRIMARY KEY, DIR TEXT, FILE_NAME TEXT);
            CREATE TABLE PARSER_DIRECTORY (DIR TEXT, ROOT_DIR INTEGER);
            INSERT INTO PARSER_DIRECTORY VALUES ('{0}', 1);
        '''.format(self.root.replace("'", "''")))
        connection.execute('INSERT INTO PHOTOS VALUES (1, ?, ?, ?, ?)', (self.root, 'indexed.jpg', '{"camera":"x"}', 1))
        connection.execute('INSERT INTO PHOTOS VALUES (2, ?, ?, ?, ?)', (self.root, 'no-date.png', '{}', None))
        connection.execute('INSERT INTO PHOTOS VALUES (3, ?, ?, ?, ?)', (self.root, 'gone.jpg', '{}', 2))
        connection.execute('INSERT INTO VIDEOS VALUES (1, ?, ?)', (self.root, 'movie.mp4'))
        connection.commit()
        connection.close()

    def _touch(self, name):
        with open(os.path.join(self.root, name), 'wb'):
            pass

    def test_audit_reports_counts_and_details_without_writing_database(self):
        for name in ('indexed.jpg', 'no-date.png', 'missing.heic', 'movie.mp4', 'missing.mov'):
            self._touch(name)
        database_mtime = os.path.getmtime(self.database_path)

        summary = audit(self.database_path, [], self.output_directory)

        self.assertEqual(3, summary['filesystem']['image_count_total'])
        self.assertEqual(1, summary['filesystem']['unsupported_image_count'])
        self.assertEqual(2, summary['filesystem']['video_count'])
        self.assertEqual(1, summary['comparison']['image_files_missing_from_db_count'])
        self.assertEqual(1, summary['comparison']['video_files_missing_from_db_count'])
        self.assertEqual(1, summary['database']['photo_utc_ts_null_count'])
        self.assertEqual(database_mtime, os.path.getmtime(self.database_path))
        with open(os.path.join(self.output_directory, 'audit_summary.json'), encoding='utf-8') as report:
            self.assertEqual(3, json.load(report)['filesystem']['image_count_total'])

    def test_database_connection_rejects_writes(self):
        connection = open_read_only_database(self.database_path)
        with self.assertRaises(sqlite3.OperationalError):
            connection.execute("INSERT INTO PHOTOS VALUES (4, 'x', 'x', 'x', 1)")
        connection.close()


if __name__ == '__main__':
    unittest.main()
