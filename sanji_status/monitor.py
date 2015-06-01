import logging
import threading
import time

from datetime import (
    datetime,
    timedelta,
)

import psutil

from sanji_status.dao import Database

logger = logging.getLogger(__name__)


class MonitorThread(threading.Thread):
    # routine to get status info, and save to db

    def __init__(self, dbpath, log_interval_sec, log_count):
        super(MonitorThread, self).__init__()

        self._log_interval_sec = log_interval_sec
        self._log_count = log_count

        self.stoprequest = threading.Event()

        self._database = Database(dbpath)

        self._next_poll = datetime.utcnow()

    def run(self):
        while not self.stoprequest.isSet():
            time_dt = datetime.utcnow()
            if time_dt < self._next_poll:
                time.sleep(0.5)
                continue

            cpu_percent, memory, disk = MonitorThread._get_readings()

            self._database.delete_old_readings(self._log_count)
            self._database.insert_reading(
                cpu_percent,
                memory,
                disk,
                time_dt
            )

            self._next_poll = (
                self._next_poll +
                timedelta(seconds=self._log_interval_sec)
            )

    def join(self):
        # set event to stop while loop in run
        self.stoprequest.set()
        super(MonitorThread, self).join()

    @classmethod
    def _get_readings(cls):
        '''Returns a tuple like:
            (cpu_usage_percent, memory_usage_byte, disk_usage_byte)
        '''
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return (
            cpu_percent,
            memory.total - memory.available,
            disk.used
        )
