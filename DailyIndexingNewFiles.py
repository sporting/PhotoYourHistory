# -*- coding: UTF-8 -*-
import os
from datetime import datetime

from db.SaPhotoDB import dbPhotoHelper
from date.TimeZoneHelper import TimeZoneHelper
from date.DateTimeHelper import DateTimeHelper
from graph.ExifHelper import ExifHelper
from synology.FileParser import ImageFileHelper
from synology.FileParser import VideoFileHelper

from db.MyCatalogEncoder import MyCatalogEncoder

"""Parse all photos/videos in the monitored folders into the index."""

DefaultTimeZone = 'Asia/Taipei'
dbh = dbPhotoHelper()
tzh = TimeZoneHelper(DefaultTimeZone)
dth = DateTimeHelper()


def VideoProcess(DIR, BatchProcessDateTime, recursiveFalg):
    videofh = VideoFileHelper()
    inserted = 0
    updated = 0
    for f in videofh.getFiles(DIR, None, recursiveFalg):
        dd = os.path.dirname(f)
        fname = os.path.basename(f)
        ext = os.path.splitext(fname)[1]
        try:
            if not dbh.videoExists(dd, fname):
                cdate = os.path.getmtime(f)
                createDT = tzh.getUTCTime(dth.timestampToDateTime(cdate))
                size_b = os.stat(f).st_size
                log = (fname, DIR, dd, createDT, DefaultTimeZone,
                       BatchProcessDateTime, ext, size_b)
                if dbh.insertVideo(log, cls=MyCatalogEncoder):
                    inserted += 1
            else:
                if dbh.updateVideo(dd, fname, BatchProcessDateTime):
                    updated += 1
        except (OSError, ValueError, TypeError) as error:
            print('VideoProcess failed for {0}: {1}'.format(f, error))
    return inserted, updated


def ImagesProcess(DIR, BatchProcessDateTime, recursiveFalg):
    imgfh = ImageFileHelper()
    exifh = ExifHelper()
    inserted = 0
    updated = 0
    for f in imgfh.getFiles(DIR, None, recursiveFalg):
        dd = os.path.dirname(f)
        fname = os.path.basename(f)
        ext = os.path.splitext(fname)[1]
        try:
            if not dbh.photoExists(dd, fname):
                meta = exifh.getExif(f)
                photoUtcDT = exifh.getGPSDateTime(meta)
                if photoUtcDT:
                    photoUtcDT = dth.strToDateTime(photoUtcDT)
                    photoUtcDT = None if not photoUtcDT else tzh.UtcToUtcTime(photoUtcDT)
                else:
                    photoUtcDT = exifh.getDateTimeDigitizedDateTime(meta)
                    photoUtcDT = None if not photoUtcDT else dth.strToDateTime(photoUtcDT)
                    if not photoUtcDT:
                        photoUtcDT = exifh.getDateTimeOriginal(meta)
                        photoUtcDT = None if not photoUtcDT else dth.strToDateTime(photoUtcDT)
                        if not photoUtcDT:
                            photoUtcDT = exifh.getDateTime(meta)
                            photoUtcDT = None if not photoUtcDT else dth.strToDateTime(photoUtcDT)
                    if photoUtcDT:
                        photoUtcDT = tzh.getUTCTime(photoUtcDT)
                ts = dth.dateTimeToTimestamp(photoUtcDT) if photoUtcDT else None

                cdate = os.path.getmtime(f)
                createDT = tzh.getUTCTime(dth.timestampToDateTime(cdate))
                gps = exifh.getGPS(meta)
                tz = DefaultTimeZone
                if gps:
                    tz = tzh.getTimezone(gps) or DefaultTimeZone
                size_b = os.stat(f).st_size
                log = (fname, DIR, dd, meta or {}, ts, photoUtcDT, createDT,
                       tz, gps, BatchProcessDateTime, '', ext, '', size_b)
                if dbh.insertPhoto(log, cls=MyCatalogEncoder):
                    inserted += 1
            else:
                if dbh.updatePhoto(dd, fname, BatchProcessDateTime):
                    updated += 1
        except (OSError, ValueError, TypeError) as error:
            print('ImagesProcess failed for {0}: {1}'.format(f, error))
    return inserted, updated


def DailyIndexingNewImageFile():
    """Scan every monitored directory; do not rely on directory mtime.

    A directory mtime is not a completeness signal for nested files or NAS
    synchronization.  Obsolete-row deletion is deliberately not performed
    here: a partial scan must never be mistaken for a deletion event.  The
    read-only audit and explicit repair tools handle reconciliation safely.
    """
    currentDT = tzh.getUTCTime(datetime.now())
    for directory in dbh.getMonitorDirs() or []:
        directory_path = directory['DIR']
        if not os.path.isdir(directory_path):
            print(str(directory_path) + ' folder is not exists')
            continue
        recursive = bool(directory['RECURSIVE'])
        try:
            ImagesProcess(directory_path, currentDT, recursive)
            VideoProcess(directory_path, currentDT, recursive)
            dbh.updateDir(currentDT, directory_path)
        except Exception as error:
            # Do not update parser state after an incomplete directory scan.
            print('Indexing failed for {0}: {1}'.format(directory_path, error))


if __name__ == "__main__":
    DailyIndexingNewImageFile()

