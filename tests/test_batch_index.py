import datetime
import os
import sqlite3
import sys
import tempfile
import types
import unittest


def _install_lightweight_dependencies():
    catalog_module = types.ModuleType('db.CatalogEncoder')

    class CatalogEncoder:
        def default(self, directory):
            return ''

    catalog_module.CatalogEncoder = CatalogEncoder
    json_module = types.ModuleType('db.JsonEncoder')

    class MyEncoder(__import__('json').JSONEncoder):
        pass

    json_module.MyEncoder = MyEncoder
    date_module = types.ModuleType('date.DateTimeHelper')

    class DateTimeHelper:
        def timestampToDateTime(self, timestamp):
            return datetime.datetime.fromtimestamp(timestamp)

        def dateTimeToTimestamp(self, value):
            return value.timestamp()

        def strToDateTime(self, value):
            return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')

    date_module.DateTimeHelper = DateTimeHelper
    timezone_module = types.ModuleType('date.TimeZoneHelper')

    class TimeZoneHelper:
        def __init__(self, name):
            self.name = name

        def getUTCTime(self, value):
            return value

        def UtcToUtcTime(self, value):
            return value

        def getTimezone(self, value):
            return None

    timezone_module.TimeZoneHelper = TimeZoneHelper
    exif_module = types.ModuleType('graph.ExifHelper')

    class ExifHelper:
        def getExif(self, filename):
            return {}

        def getGPSDateTime(self, exif):
            return None

        def getDateTimeDigitizedDateTime(self, exif):
            return None

        def getDateTimeOriginal(self, exif):
            return None

        def getDateTime(self, exif):
            return None

        def getGPS(self, exif):
            return None

    exif_module.ExifHelper = ExifHelper
    sys.modules.update({
        'db.CatalogEncoder': catalog_module,
        'db.JsonEncoder': json_module,
        'date.DateTimeHelper': date_module,
        'date.TimeZoneHelper': timezone_module,
        'graph.ExifHelper': exif_module,
    })


_install_lightweight_dependencies()
from db.BatchIndex import BatchIndexStore


class BatchIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.temp.name, 'photos')
        os.makedirs(os.path.join(self.root, 'nested'))
        self.db_path = os.path.join(self.temp.name, 'SaPhoto.db')
        connection = sqlite3.connect(self.db_path)
        connection.executescript('''
            CREATE TABLE PHOTOS (
                ID INTEGER PRIMARY KEY, FILE_NAME TEXT, ROOT_DIR TEXT, DIR TEXT,
                META TEXT, PHOTO_UTC_TS INTEGER, PHOTO_UTC_DATE DATETIME,
                CREATE_UTC_DATE DATETIME, TIME_ZONE TEXT, GPS TEXT,
                BATCH_UTC_DATE DATETIME, FACE_RECOGNITION TEXT, FILE_TYPE TEXT,
                SCENE TEXT, CATALOG TEXT, SIZE_B INTEGER
            );
            CREATE TABLE VIDEOS (
                ID INTEGER PRIMARY KEY, FILE_NAME TEXT, ROOT_DIR TEXT, DIR TEXT,
                CREATE_UTC_DATE DATETIME, TIME_ZONE TEXT, BATCH_UTC_DATE DATETIME,
                FILE_TYPE TEXT, CATALOG TEXT, SIZE_B INTEGER
            );
            CREATE TABLE PARSER_DIRECTORY (
                ID INTEGER PRIMARY KEY, DIR TEXT, ROOT_DIR INTEGER,
                RECURSIVE INTEGER, PARSER_UTC_DATE DATETIME, MONITOR INTEGER
            );
        ''')
        connection.execute(
            'INSERT INTO PARSER_DIRECTORY VALUES (1, ?, 1, 1, NULL, 1)', (self.root,))
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp.cleanup()

    def touch(self, name):
        path = os.path.join(self.root, name)
        with open(path, 'wb') as output:
            output.write(b'x')

    def test_batch_index_inserts_only_new_media_and_marks_existing_rows_once(self):
        self.touch('old.jpg')
        self.touch('nested/new.JPG')
        self.touch('nested/movie.MP4')
        connection = sqlite3.connect(self.db_path)
        connection.execute(
            'INSERT INTO PHOTOS (FILE_NAME,ROOT_DIR,DIR,BATCH_UTC_DATE) VALUES (?,?,?,?)',
            ('old.jpg', self.root, self.root, 'old'),
        )
        connection.commit()
        connection.close()

        store = BatchIndexStore(self.db_path, catalog_cls=type('Catalog', (), {
            'default': lambda self, directory: ''
        }))
        try:
            first = store.index_directory(self.root, recursive=True, batch_datetime='batch-1')
            second = store.index_directory(self.root, recursive=True, batch_datetime='batch-2')
        finally:
            store.close()

        self.assertEqual({'photos_seen': 2, 'videos_seen': 1,
                          'photos_inserted': 1, 'videos_inserted': 1},
                         {key: first[key] for key in (
                             'photos_seen', 'videos_seen', 'photos_inserted', 'videos_inserted')})
        self.assertEqual(0, second['photos_inserted'])
        self.assertEqual(0, second['videos_inserted'])
        connection = sqlite3.connect(self.db_path)
        self.assertEqual(2, connection.execute('SELECT COUNT(*) FROM PHOTOS').fetchone()[0])
        self.assertEqual(1, connection.execute('SELECT COUNT(*) FROM VIDEOS').fetchone()[0])
        self.assertEqual('batch-2', connection.execute(
            'SELECT BATCH_UTC_DATE FROM PHOTOS WHERE FILE_NAME=?', ('old.jpg',)).fetchone()[0])
        connection.close()


if __name__ == '__main__':
    unittest.main()

