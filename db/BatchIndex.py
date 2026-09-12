# -*- coding: UTF-8 -*-
"""Transactional, set-based index updates used by the daily indexer."""

import datetime
import json
import os
import sqlite3

from db.CatalogEncoder import CatalogEncoder
from db.JsonEncoder import MyEncoder
from date.DateTimeHelper import DateTimeHelper
from date.TimeZoneHelper import TimeZoneHelper
from graph.ExifHelper import ExifHelper
from synology.FileParser import ImageFileHelper, VideoFileHelper


def _path_key(directory, filename):
    return os.path.normpath(os.path.join(directory, filename)).casefold()


class BatchIndexStore:
    """Index one monitored directory with one connection and one transaction."""

    PHOTO_COLUMNS = (
        'FILE_NAME', 'ROOT_DIR', 'DIR', 'META', 'PHOTO_UTC_TS',
        'PHOTO_UTC_DATE', 'CREATE_UTC_DATE', 'TIME_ZONE', 'GPS',
        'BATCH_UTC_DATE', 'FACE_RECOGNITION', 'FILE_TYPE', 'SCENE',
        'CATALOG', 'SIZE_B',
    )
    VIDEO_COLUMNS = (
        'FILE_NAME', 'ROOT_DIR', 'DIR', 'CREATE_UTC_DATE', 'TIME_ZONE',
        'BATCH_UTC_DATE', 'FILE_TYPE', 'CATALOG', 'SIZE_B',
    )

    def __init__(self, database_path='SaPhoto.db', timezone_name='Asia/Taipei', catalog_cls=None):
        self.database_path = database_path
        self.timezone_name = timezone_name
        self.catalog_cls = catalog_cls or self._load_catalog_cls()
        self.conn = sqlite3.connect(database_path)
        self.conn.row_factory = sqlite3.Row
        self.date_helper = DateTimeHelper()
        self.timezone_helper = TimeZoneHelper(timezone_name)
        self.exif_helper = ExifHelper()

    @staticmethod
    def _load_catalog_cls():
        try:
            from db.MyCatalogEncoder import MyCatalogEncoder
            return MyCatalogEncoder
        except ImportError:
            return CatalogEncoder

    def close(self):
        self.conn.close()

    def get_monitor_dirs(self):
        return self.conn.execute(
            'SELECT * FROM PARSER_DIRECTORY WHERE MONITOR=1 ORDER BY ID').fetchall()

    def _photo_record(self, filepath, root_dir, batch_datetime):
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        meta = self.exif_helper.getExif(filepath) or {}
        photo_datetime = None
        gps_datetime = self.exif_helper.getGPSDateTime(meta)
        date_values = (
            (gps_datetime, True),
            (self.exif_helper.getDateTimeDigitizedDateTime(meta), False),
            (self.exif_helper.getDateTimeOriginal(meta), False),
            (self.exif_helper.getDateTime(meta), False),
        )
        for value, is_gps_utc in date_values:
            if not value:
                continue
            parsed = self.date_helper.strToDateTime(value)
            if parsed:
                photo_datetime = (
                    self.timezone_helper.UtcToUtcTime(parsed)
                    if is_gps_utc else self.timezone_helper.getUTCTime(parsed)
                )
                break
        gps = self.exif_helper.getGPS(meta)
        create_datetime = self.timezone_helper.getUTCTime(
            self.date_helper.timestampToDateTime(os.path.getmtime(filepath)))
        timezone_name = self.timezone_name
        if gps:
            timezone_name = self.timezone_helper.getTimezone(gps) or timezone_name
        return (
            filename, root_dir, directory, json.dumps(meta, cls=MyEncoder),
            self.date_helper.dateTimeToTimestamp(photo_datetime) if photo_datetime else None,
            photo_datetime, create_datetime, timezone_name, gps, batch_datetime,
            '', os.path.splitext(filename)[1], '',
            self.catalog_cls().default(directory), os.path.getsize(filepath),
        )

    def _video_record(self, filepath, root_dir, batch_datetime):
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        create_datetime = self.timezone_helper.getUTCTime(
            self.date_helper.timestampToDateTime(os.path.getmtime(filepath)))
        return (
            filename, root_dir, directory, create_datetime, self.timezone_name,
            batch_datetime, os.path.splitext(filename)[1],
            self.catalog_cls().default(directory), os.path.getsize(filepath),
        )

    def index_directory(self, directory, recursive=False, batch_datetime=None):
        """Index a directory without per-file SELECT/UPDATE/COMMIT calls."""
        if not os.path.isdir(directory):
            raise ValueError('Directory does not exist: {0}'.format(directory))
        batch_datetime = batch_datetime or datetime.datetime.utcnow()
        image_files = list(ImageFileHelper().getFiles(directory, None, recursive))
        video_files = list(VideoFileHelper().getFiles(directory, None, recursive))
        photo_keys = {
            _path_key(row['DIR'], row['FILE_NAME']) for row in self.conn.execute(
                'SELECT DIR, FILE_NAME FROM PHOTOS WHERE ROOT_DIR=?', (directory,))
        }
        video_keys = {
            _path_key(row['DIR'], row['FILE_NAME']) for row in self.conn.execute(
                'SELECT DIR, FILE_NAME FROM VIDEOS WHERE ROOT_DIR=?', (directory,))
        }
        photos = [
            self._photo_record(filepath, directory, batch_datetime)
            for filepath in image_files
            if _path_key(os.path.dirname(filepath), os.path.basename(filepath)) not in photo_keys
        ]
        videos = [
            self._video_record(filepath, directory, batch_datetime)
            for filepath in video_files
            if _path_key(os.path.dirname(filepath), os.path.basename(filepath)) not in video_keys
        ]
        try:
            with self.conn:
                self.conn.execute(
                    'UPDATE PHOTOS SET BATCH_UTC_DATE=? WHERE ROOT_DIR=?',
                    (batch_datetime, directory),
                )
                self.conn.execute(
                    'UPDATE VIDEOS SET BATCH_UTC_DATE=? WHERE ROOT_DIR=?',
                    (batch_datetime, directory),
                )
                self.conn.executemany(
                    'INSERT INTO PHOTOS ({0}) VALUES ({1})'.format(
                        ','.join(self.PHOTO_COLUMNS), ','.join('?' for _ in self.PHOTO_COLUMNS)
                    ), photos,
                )
                self.conn.executemany(
                    'INSERT INTO VIDEOS ({0}) VALUES ({1})'.format(
                        ','.join(self.VIDEO_COLUMNS), ','.join('?' for _ in self.VIDEO_COLUMNS)
                    ), videos,
                )
                self.conn.execute(
                    'UPDATE PARSER_DIRECTORY SET PARSER_UTC_DATE=? WHERE DIR=?',
                    (batch_datetime, directory),
                )
        except Exception:
            self.conn.rollback()
            raise
        return {
            'directory': directory,
            'photos_seen': len(image_files),
            'videos_seen': len(video_files),
            'photos_inserted': len(photos),
            'videos_inserted': len(videos),
        }

