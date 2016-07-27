import os
import threading
import time
import logging


logger = logging.getLogger('filemonitor')


class FileMonitor(object):
    __name__ = "filemonitor"

    def __init__(self, logfile):
        self._filehandle = None
        self._logfile = logfile

    def get_messages(self):
        st_results = None
        st_size = None
        ino = None
        while self._filehandle is None:
            try:
                self._filehandle = open(self._logfile, 'r')
                st_results = os.stat(self._logfile)
                st_size = st_results[6]
                ino = os.stat(self._filehandle.name).st_ino
                self._filehandle.seek(st_size)
            except:
                logger.error("could not open file %s, trying again...", self._logfile)
                self._filehandle = None
                time.sleep(1)
	logger.info("opened %s", self._logfile)
        if self._filehandle is not None:
            yield 'now tracking file %s' % (self._logfile)

        while True:
            gotline = False
            test_ino = ino
            try:
                test_ino = os.stat(self._filehandle.name).st_ino
            except:
                continue

            if ino != test_ino:
                try:
                    self._filehandle.close()
                    self._filehandle = open(self._logfile, 'r')
                except:
                    continue
                st_results = os.stat(self._logfile)
                st_size = st_results[6]
                ino = os.stat(self._filehandle.name).st_ino

            where = self._filehandle.tell()
            line = self._filehandle.readline()
            if not line:
                self._filehandle.seek(where)
            else:
                gotline = True

            if gotline:
                line = line.strip()
                logger.debug("new line: %s", line)
                yield line
            else:
                time.sleep(0.1)
