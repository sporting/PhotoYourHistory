#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Safely add filesystem media that is absent from the SQLite index.

The default is a report-only dry run.  ``--apply`` writes missing rows in one
transaction and never removes or moves a source file or an existing DB row.
"""

from __future__ import print_function

import argparse
import datetime
import json
import os
import sqlite3

from db.CatalogEncoder import CatalogEncoder
from db.JsonEncoder import MyEncoder
from graph.ExifHelper import ExifHelper
from date.DateTimeHelper import DateTimeHelper
from date.TimeZoneHelper import TimeZoneHelper
from synology.FileParser import ImageFileHelper, VideoFileHelper
from tools.AuditPhotoIndex import path_key


def _catalog_encoder():
    try:
        from db.MyCatalogEncoder import MyCatalogEncoder
        return MyCatalogEncoder
    except ImportError:
        return CatalogEncoder


def _photo_record(filepath, root, batch_datetime, timezone_name='Asia/Taipei'):
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    exif_helper = ExifHelper()
    date_helper = DateTimeHelper()
    timezone_helper = TimeZoneHelper(timezone_name)
    meta = exif_helper.getExif(filepath) or {}
    photo_datetime = None
    gps_datetime = exif_helper.getGPSDateTime(meta)
    values = (
        (gps_datetime, True),
        (exif_helper.getDateTimeDigitizedDateTime(meta), False),
        (exif_helper.getDateTimeOriginal(meta), False),
        (exif_helper.getDateTime(meta), False),
    )
    for value, is_gps_utc in values:
        if not value:
            continue
        parsed = date_helper.strToDateTime(value)
        if parsed:
            photo_datetime = (timezone_helper.UtcToUtcTime(parsed)
                              if is_gps_utc else timezone_helper.getUTCTime(parsed))
            break
    gps = exif_helper.getGPS(meta)
    file_datetime = timezone_helper.getUTCTime(
        date_helper.timestampToDateTime(os.path.getmtime(filepath)))
    ts = date_helper.dateTimeToTimestamp(photo_datetime) if photo_datetime else None
    return {
        'FILE_NAME': filename,
        'ROOT_DIR': root,
        'DIR': directory,
        'META': json.dumps(meta, cls=MyEncoder),
        'PHOTO_UTC_TS': ts,
        'PHOTO_UTC_DATE': photo_datetime,
        'CREATE_UTC_DATE': file_datetime,
        'TIME_ZONE': timezone_name,
        'GPS': gps,
        'BATCH_UTC_DATE': batch_datetime,
        'FACE_RECOGNITION': '',
        'FILE_TYPE': os.path.splitext(filename)[1],
        'SCENE': '',
        'CATALOG': _catalog_encoder()().default(directory),
        'SIZE_B': os.path.getsize(filepath),
    }


def _video_record(filepath, root, batch_datetime, timezone_name='Asia/Taipei'):
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    date_helper = DateTimeHelper()
    timezone_helper = TimeZoneHelper(timezone_name)
    file_datetime = timezone_helper.getUTCTime(
        date_helper.timestampToDateTime(os.path.getmtime(filepath)))
    return {
        'FILE_NAME': filename,
        'ROOT_DIR': root,
        'DIR': directory,
        'CREATE_UTC_DATE': file_datetime,
        'TIME_ZONE': timezone_name,
        'BATCH_UTC_DATE': batch_datetime,
        'FILE_TYPE': os.path.splitext(filename)[1],
        'CATALOG': _catalog_encoder()().default(directory),
        'SIZE_B': os.path.getsize(filepath),
    }


def _roots(connection, requested_roots):
    if requested_roots:
        return list(requested_roots)
    return [row[0] for row in connection.execute(
        'SELECT DIR FROM PARSER_DIRECTORY WHERE ROOT_DIR=1') if row[0]]


def backfill(database_path, roots=None, apply=False, timezone_name='Asia/Taipei'):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        scan_roots = _roots(connection, roots or [])
        if not scan_roots:
            raise ValueError('No roots supplied and PARSER_DIRECTORY has no ROOT_DIR=1 entries.')
        photo_keys = {
            path_key(row['DIR'], row['FILE_NAME'])
            for row in connection.execute('SELECT DIR, FILE_NAME FROM PHOTOS')
        }
        video_keys = {
            path_key(row['DIR'], row['FILE_NAME'])
            for row in connection.execute('SELECT DIR, FILE_NAME FROM VIDEOS')
        }
        missing_photos = []
        missing_videos = []
        image_helper = ImageFileHelper()
        video_helper = VideoFileHelper()
        batch_datetime = datetime.datetime.utcnow()
        for root in scan_roots:
            for filepath in image_helper.getFiles(root, None, True):
                if path_key(os.path.dirname(filepath), os.path.basename(filepath)) not in photo_keys:
                    missing_photos.append(_photo_record(filepath, root, batch_datetime, timezone_name))
            for filepath in video_helper.getFiles(root, None, True):
                if path_key(os.path.dirname(filepath), os.path.basename(filepath)) not in video_keys:
                    missing_videos.append(_video_record(filepath, root, batch_datetime, timezone_name))

        summary = {
            'database_path': os.path.abspath(database_path),
            'roots_scanned': scan_roots,
            'would_insert_photos': len(missing_photos),
            'would_insert_videos': len(missing_videos),
            'applied': bool(apply),
        }
        if apply:
            photo_values = [tuple(row[name] for name in (
                'FILE_NAME', 'ROOT_DIR', 'DIR', 'META', 'PHOTO_UTC_TS',
                'PHOTO_UTC_DATE', 'CREATE_UTC_DATE', 'TIME_ZONE', 'GPS',
                'BATCH_UTC_DATE', 'FACE_RECOGNITION', 'FILE_TYPE', 'SCENE',
                'CATALOG', 'SIZE_B')) for row in missing_photos]
            video_values = [tuple(row[name] for name in (
                'FILE_NAME', 'ROOT_DIR', 'DIR', 'CREATE_UTC_DATE', 'TIME_ZONE',
                'BATCH_UTC_DATE', 'FILE_TYPE', 'CATALOG', 'SIZE_B'))
                            for row in missing_videos]
            with connection:
                connection.executemany(
                    'INSERT INTO PHOTOS (FILE_NAME,ROOT_DIR,DIR,META,PHOTO_UTC_TS,'
                    'PHOTO_UTC_DATE,CREATE_UTC_DATE,TIME_ZONE,GPS,BATCH_UTC_DATE,'
                    'FACE_RECOGNITION,FILE_TYPE,SCENE,CATALOG,SIZE_B) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', photo_values)
                connection.executemany(
                    'INSERT INTO VIDEOS (FILE_NAME,ROOT_DIR,DIR,CREATE_UTC_DATE,'
                    'TIME_ZONE,BATCH_UTC_DATE,FILE_TYPE,CATALOG,SIZE_B) '
                    'VALUES (?,?,?,?,?,?,?,?,?)', video_values)
        return summary
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='SaPhoto.db')
    parser.add_argument('--root', action='append', default=[])
    parser.add_argument('--timezone', default='Asia/Taipei')
    parser.add_argument('--apply', action='store_true',
                        help='Insert missing DB rows; never changes source files.')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(backfill(args.db, args.root, args.apply, args.timezone),
                         indent=2, sort_keys=True, default=str))
    except (OSError, sqlite3.DatabaseError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()

