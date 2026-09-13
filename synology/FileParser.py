# -*- coding: UTF-8 -*-
"""Enumerate media files on a Synology volume.

The legacy implementation used atime as a filter and matched each case
variant separately.  atime is not a reliable signal on NAS volumes, so the
indexer now performs a complete scan of each monitored directory.
"""

import fnmatch
import os


SKIPPED_DIRECTORY_NAMES = frozenset(("@eadir", "#recycle", ".thumbnail", "_vti_cnf"))


def _iter_files(path, extensions, localtimestamp=None, recursive=False):
    if not os.path.isdir(path):
        return

    normalized_extensions = tuple(extension.casefold() for extension in extensions)
    for dir_path, dir_names, file_names in os.walk(path):
        dir_names[:] = [
            name for name in dir_names
            if name.casefold() not in SKIPPED_DIRECTORY_NAMES
        ]
        for filename in sorted(file_names, key=str.casefold):
            if not any(fnmatch.fnmatchcase(filename.casefold(), pattern)
                       for pattern in normalized_extensions):
                continue
            filepath = os.path.join(dir_path, filename)
            if localtimestamp is not None:
                try:
                    if os.path.getmtime(filepath) < localtimestamp:
                        continue
                except OSError:
                    continue
            yield filepath
        if not recursive:
            break


class DirectoryHelper:
    def listHasFilesDirectories(self, path):
        """Yield media directories while excluding Synology metadata trees."""
        if not os.path.isdir(path):
            return
        for directory, dir_names, file_names in os.walk(path):
            dir_names[:] = [
                name for name in dir_names
                if name.casefold() not in SKIPPED_DIRECTORY_NAMES
            ]
            if file_names:
                yield directory


class ImageFileHelper:
    EXTENSIONS = ("*.jpg", "*.jpeg", "*.png")

    def getFiles(self, path, localtimestamp=None, recursive=False):
        return _iter_files(path, self.EXTENSIONS, localtimestamp, recursive)


class VideoFileHelper:
    EXTENSIONS = (
        "*.avi", "*.mpg", "*.mpeg", "*.mov", "*.mp4", "*.wmv", "*.m2t",
        "*.m2ts", "*.mts", "*.asf", "*.swf", "*.3gp", "*.3gp2", "*.rm",
        "*.qt",
    )

    def getFiles(self, path, localtimestamp=None, recursive=False):
        return _iter_files(path, self.EXTENSIONS, localtimestamp, recursive)

