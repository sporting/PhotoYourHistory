#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Produce repeatable index baselines without changing source media.

Without ``--run`` this is a read-only baseline.  With ``--run`` the SQLite
database is copied through SQLite's backup API into a temporary file and the
batch indexer is timed against that copy; the real DB and photos remain read
only throughout the benchmark.
"""

from __future__ import print_function

import argparse
import json
import os
import sqlite3
import tempfile
import time

from tools.AuditPhotoIndex import collect_database, open_read_only_database, scan_filesystem


def _copy_database(source_path, target_path):
    source = open_read_only_database(source_path)
    target = sqlite3.connect(target_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()


def baseline(database_path, roots, run=False):
    started = time.time()
    connection = open_read_only_database(database_path)
    try:
        database = collect_database(connection)
    finally:
        connection.close()
    effective_roots = list(roots or database['roots'])
    scan_started = time.time()
    filesystem, extension_counts, missing_roots, scan_errors = scan_filesystem(effective_roots)
    scan_seconds = time.time() - scan_started
    result = {
        'database_path': os.path.abspath(database_path),
        'database_size_bytes': os.path.getsize(database_path),
        'roots_scanned': effective_roots,
        'files': {
            'photos': len(filesystem['photos']),
            'unsupported_images': len(filesystem['unsupported_images']),
            'videos': len(filesystem['videos']),
            'extension_counts': dict(sorted(extension_counts.items())),
        },
        'database': {
            'photos': len(database['photos']),
            'videos': len(database['videos']),
            'meta_total_bytes': database['storage']['meta_total_bytes'],
            'page_count': database['storage']['page_count'],
            'freelist_count': database['storage']['freelist_count'],
        },
        'scan_seconds': round(scan_seconds, 6),
        'missing_roots': missing_roots,
        'scan_errors': scan_errors,
        'total_seconds': round(time.time() - started, 6),
    }
    if run:
        from db.BatchIndex import BatchIndexStore
        with tempfile.TemporaryDirectory() as temporary_directory:
            copy_path = os.path.join(temporary_directory, 'benchmark.db')
            _copy_database(database_path, copy_path)
            store = BatchIndexStore(copy_path)
            index_started = time.time()
            try:
                results = []
                if roots:
                    results = [store.index_directory(root, recursive=True)
                               for root in effective_roots]
                else:
                    for row in store.get_monitor_dirs():
                        results.append(store.index_directory(row['DIR'], bool(row['RECURSIVE'])))
            finally:
                store.close()
            result['batch_index_seconds'] = round(time.time() - index_started, 6)
            result['batch_index_results'] = results
            result['benchmark_database_was_temporary_copy'] = True
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='SaPhoto.db')
    parser.add_argument('--root', action='append', default=[])
    parser.add_argument('--run', action='store_true',
                        help='Time the batch indexer against a temporary DB copy.')
    args = parser.parse_args(argv)
    print(json.dumps(baseline(args.db, args.root, args.run), indent=2, sort_keys=True,
                     default=str))


if __name__ == '__main__':
    main()

