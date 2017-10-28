import logging
import time

import os

logger = logging.getLogger('filemonitor')


class FileMonitor(object):
    __name__ = "filemonitor"

    def __init__(self, logfile):
        self._file_handler = None
        self._logfile = logfile

    def get_messages(self):
        ino = None
        while self._file_handler is None:
            try:
                self._file_handler = open(self._logfile, 'r')
                st_results = os.stat(self._logfile)
                st_size = st_results[6]
                ino = os.stat(self._file_handler.name).st_ino
                self._file_handler.seek(st_size)
            except Exception:
                logger.error("could not open file %s, trying again...", self._logfile)
                self._file_handler = None
                time.sleep(1)
        logger.info("opened %s", self._logfile)
        yield 'now tracking file %s' % (self._logfile)
        while True:
            got_line = False
            try:
                test_ino = os.stat(self._file_handler.name).st_ino
            except Exception:
                continue
            if ino != test_ino:
                try:
                    self._file_handler.close()
                    self._file_handler = open(self._logfile, 'r')
                except Exception:
                    continue
                ino = os.stat(self._file_handler.name).st_ino
            where = self._file_handler.tell()
            line = self._file_handler.readline()
            if not line:
                self._file_handler.seek(where)
            else:
                got_line = True
            if got_line:
                try:
                    proper_line = line.decode('utf-8', errors='ignore').strip()
                except Exception:
                    proper_line = line.strip()
                logger.debug("new line: %s", proper_line)
                yield proper_line
            else:
                time.sleep(0.1)


__plugin_class__ = FileMonitor
