# -*- coding: UTF-8 -*-
from datetime import datetime

from db.BatchIndex import BatchIndexStore
from date.TimeZoneHelper import TimeZoneHelper

"""Incrementally index all monitored directories in set-based transactions."""

DefaultTimeZone = 'Asia/Taipei'


def DailyIndexingNewImageFile(database_path='SaPhoto.db'):
    store = BatchIndexStore(database_path, DefaultTimeZone)
    try:
        batch_datetime = TimeZoneHelper(DefaultTimeZone).getUTCTime(datetime.now())
        for directory in store.get_monitor_dirs():
            directory_path = directory['DIR']
            try:
                result = store.index_directory(
                    directory_path,
                    recursive=bool(directory['RECURSIVE']),
                    batch_datetime=batch_datetime,
                )
                print('{0}: {1}'.format(directory_path, result))
            except Exception as error:
                # Parser state is updated only inside a successful transaction.
                print('Indexing failed for {0}: {1}'.format(directory_path, error))
    finally:
        store.close()


if __name__ == "__main__":
    DailyIndexingNewImageFile()

