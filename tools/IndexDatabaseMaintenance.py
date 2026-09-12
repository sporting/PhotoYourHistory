#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report and safely maintain SQLite index storage.

No maintenance operation touches source photos/videos.  ``--vacuum`` is
explicit, requires ``--backup``, and runs only after making a SQLite backup.
It is intentionally not part of the daily indexing schedule.
"""

from __future__ import print_function

import argparse
import json
import os
import sqlite3

from tools.AuditPhotoIndex import collect_database, open_read_only_database


def report(database_path):
    connection = open_read_only_database(database_path)
    try:
        database = collect_database(connection)
    finally:
        connection.close()
    return {
        'database_path': os.path.abspath(database_path),
        'database_size_bytes': os.path.getsize(database_path),
        'photos': len(database['photos']),
        'videos': len(database['videos']),
        'meta_total_bytes': database['storage']['meta_total_bytes'],
        'allocated_bytes': database['storage']['allocated_bytes'],
        'freelist_bytes': database['storage']['freelist_bytes'],
        'object_bytes': database['storage']['object_bytes'],
    }


def backup_database(database_path, backup_path):
    source = open_read_only_database(database_path)
    destination = sqlite3.connect(backup_path)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()


def vacuum(database_path, backup_path):
    if not backup_path:
        raise ValueError('--vacuum requires --backup so the original DB is recoverable.')
    if os.path.abspath(database_path) == os.path.abspath(backup_path):
        raise ValueError('Backup path must differ from the database path.')
    backup_database(database_path, backup_path)
    connection = sqlite3.connect(database_path)
    try:
        connection.execute('PRAGMA optimize')
        connection.execute('VACUUM')
    finally:
        connection.close()
    return report(database_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='SaPhoto.db')
    parser.add_argument('--vacuum', action='store_true',
                        help='Backup first, then compact the SQLite DB in place.')
    parser.add_argument('--backup', help='Backup path required by --vacuum.')
    args = parser.parse_args(argv)
    if args.vacuum:
        result = vacuum(args.db, args.backup)
    else:
        result = report(args.db)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == '__main__':
    main()

