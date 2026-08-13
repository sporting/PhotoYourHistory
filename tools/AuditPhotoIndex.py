#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only consistency and storage audit for a PhotoYourHistory index."""

from __future__ import print_function

import argparse
import csv
import json
import os
import sqlite3
import sys


SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
SUPPORTED_VIDEO_EXTENSIONS = {
    '.avi', '.mpg', '.mpeg', '.mov', '.mp4', '.wmv', '.m2t', '.m2ts',
    '.mts', '.asf', '.swf', '.3gp', '.3gp2', '.rm', '.qt',
}
UNSUPPORTED_IMAGE_EXTENSIONS = {
    '.heic', '.heif', '.webp', '.tif', '.tiff', '.dng', '.cr2', '.cr3',
    '.nef', '.arw', '.raf', '.orf', '.rw2', '.pef', '.srw',
}
SKIPPED_DIRECTORY_NAMES = {'@eadir', '#recycle', '.thumbnail'}


def path_key(directory, filename):
    """Match the case-insensitive path comparison used on common NAS volumes."""
    return os.path.normcase(os.path.normpath(os.path.join(directory, filename)))


def open_read_only_database(database_path):
    absolute_path = os.path.abspath(database_path)
    if not os.path.isfile(absolute_path):
        raise ValueError('Database does not exist: {0}'.format(absolute_path))
    return sqlite3.connect('file:{0}?mode=ro'.format(absolute_path.replace('\\', '/')), uri=True)


def fetch_rows(connection, table, columns):
    query = 'SELECT {0} FROM {1}'.format(', '.join(columns), table)
    return [dict(zip(columns, row)) for row in connection.execute(query)]


def collect_database(connection):
    photos = fetch_rows(connection, 'PHOTOS', ['ID', 'DIR', 'FILE_NAME', 'PHOTO_UTC_TS'])
    videos = fetch_rows(connection, 'VIDEOS', ['ID', 'DIR', 'FILE_NAME'])
    root_rows = list(connection.execute('SELECT DIR FROM PARSER_DIRECTORY WHERE ROOT_DIR=1'))
    roots = [row[0] for row in root_rows if row[0]]

    meta_total_bytes, meta_average_bytes = connection.execute(
        'SELECT COALESCE(SUM(LENGTH(CAST(META AS BLOB))), 0), '
        'COALESCE(AVG(LENGTH(CAST(META AS BLOB))), 0) FROM PHOTOS'
    ).fetchone()
    page_size = connection.execute('PRAGMA page_size').fetchone()[0]
    page_count = connection.execute('PRAGMA page_count').fetchone()[0]
    freelist_count = connection.execute('PRAGMA freelist_count').fetchone()[0]

    index_sizes = {}
    try:
        for name, page_bytes in connection.execute(
                'SELECT name, SUM(pgsize) FROM dbstat GROUP BY name ORDER BY name'):
            index_sizes[name] = page_bytes
    except sqlite3.DatabaseError:
        index_sizes = None

    return {
        'photos': photos,
        'videos': videos,
        'roots': roots,
        'storage': {
            'meta_total_bytes': meta_total_bytes,
            'meta_average_bytes': meta_average_bytes,
            'page_size': page_size,
            'page_count': page_count,
            'freelist_count': freelist_count,
            'allocated_bytes': page_size * page_count,
            'freelist_bytes': page_size * freelist_count,
            'used_bytes_estimate': page_size * (page_count - freelist_count),
            'object_bytes': index_sizes,
        },
    }


def scan_filesystem(roots):
    files = {'photos': {}, 'videos': {}, 'unsupported_images': {}}
    extension_counts = {}
    missing_roots = []
    for root in roots:
        if not os.path.isdir(root):
            missing_roots.append(root)
            continue
        for directory, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if name.lower() not in SKIPPED_DIRECTORY_NAMES]
            for filename in filenames:
                extension = os.path.splitext(filename)[1].lower()
                if extension in SUPPORTED_IMAGE_EXTENSIONS:
                    category = 'photos'
                elif extension in SUPPORTED_VIDEO_EXTENSIONS:
                    category = 'videos'
                elif extension in UNSUPPORTED_IMAGE_EXTENSIONS:
                    category = 'unsupported_images'
                else:
                    continue
                key = path_key(directory, filename)
                files[category][key] = {'DIR': directory, 'FILE_NAME': filename, 'EXTENSION': extension}
                extension_counts[extension] = extension_counts.get(extension, 0) + 1
    return files, extension_counts, missing_roots


def rows_by_key(rows):
    result = {}
    duplicates = []
    for row in rows:
        key = path_key(row['DIR'], row['FILE_NAME'])
        if key in result:
            duplicates.append(row)
        else:
            result[key] = row
    return result, duplicates


def comparison_rows(filesystem_rows, database_rows, label):
    filesystem_keys = set(filesystem_rows)
    database_keys = set(database_rows)
    missing_from_db = []
    for key in sorted(filesystem_keys - database_keys):
        row = dict(filesystem_rows[key])
        row['REASON'] = label
        missing_from_db.append(row)
    missing_from_filesystem = []
    for key in sorted(database_keys - filesystem_keys):
        row = dict(database_rows[key])
        row['REASON'] = label
        missing_from_filesystem.append(row)
    return missing_from_db, missing_from_filesystem


def write_csv(path, rows, fields):
    with open(path, 'w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def audit(database_path, roots, output_directory):
    connection = open_read_only_database(database_path)
    try:
        database = collect_database(connection)
    finally:
        connection.close()
    effective_roots = roots or database['roots']
    if not effective_roots:
        raise ValueError('No roots supplied and PARSER_DIRECTORY has no ROOT_DIR=1 entries.')

    filesystem, extension_counts, missing_roots = scan_filesystem(effective_roots)
    photo_rows, duplicate_photos = rows_by_key(database['photos'])
    video_rows, duplicate_videos = rows_by_key(database['videos'])
    indexed_images = filesystem['photos']
    all_images = dict(indexed_images)
    all_images.update(filesystem['unsupported_images'])
    images_missing, photos_missing = comparison_rows(all_images, photo_rows, 'image')
    videos_missing, db_videos_missing = comparison_rows(filesystem['videos'], video_rows, 'video')
    null_dates = [row for row in database['photos'] if row['PHOTO_UTC_TS'] is None]

    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    write_csv(os.path.join(output_directory, 'missing_from_db.csv'), images_missing + videos_missing,
              ['DIR', 'FILE_NAME', 'EXTENSION', 'REASON'])
    write_csv(os.path.join(output_directory, 'unsupported_extensions.csv'),
              list(filesystem['unsupported_images'].values()), ['DIR', 'FILE_NAME', 'EXTENSION'])
    write_csv(os.path.join(output_directory, 'null_photo_date.csv'), null_dates,
              ['ID', 'DIR', 'FILE_NAME', 'PHOTO_UTC_TS'])
    write_csv(os.path.join(output_directory, 'db_missing_from_filesystem.csv'), photos_missing + db_videos_missing,
              ['ID', 'DIR', 'FILE_NAME', 'PHOTO_UTC_TS', 'REASON'])

    summary = {
        'database_path': os.path.abspath(database_path),
        'roots_scanned': effective_roots,
        'roots_not_found': missing_roots,
        'filesystem': {
            'supported_image_count': len(filesystem['photos']),
            'unsupported_image_count': len(filesystem['unsupported_images']),
            'image_count_total': len(all_images),
            'video_count': len(filesystem['videos']),
            'extension_counts': dict(sorted(extension_counts.items())),
        },
        'database': {
            'photos_count': len(database['photos']),
            'videos_count': len(database['videos']),
            'photo_utc_ts_null_count': len(null_dates),
            'duplicate_photo_key_count': len(duplicate_photos),
            'duplicate_video_key_count': len(duplicate_videos),
        },
        'comparison': {
            'image_files_missing_from_db_count': len(images_missing),
            'video_files_missing_from_db_count': len(videos_missing),
            'photo_db_rows_missing_from_filesystem_count': len(photos_missing),
            'video_db_rows_missing_from_filesystem_count': len(db_videos_missing),
        },
        'storage': database['storage'],
        'reports': {
            'missing_from_db': 'missing_from_db.csv',
            'unsupported_extensions': 'unsupported_extensions.csv',
            'null_photo_date': 'null_photo_date.csv',
            'db_missing_from_filesystem': 'db_missing_from_filesystem.csv',
        },
    }
    with open(os.path.join(output_directory, 'audit_summary.json'), 'w', encoding='utf-8') as output:
        json.dump(summary, output, indent=2, sort_keys=True)
        output.write('\n')
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='SaPhoto.db', help='Path to SaPhoto.db (opened read-only).')
    parser.add_argument('--root', action='append', default=[], help='Filesystem root to scan; repeat as needed.')
    parser.add_argument('--output-dir', default='audit-report', help='Directory for CSV and JSON reports.')
    args = parser.parse_args(argv)
    try:
        summary = audit(args.db, args.root, args.output_dir)
    except (OSError, sqlite3.DatabaseError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
