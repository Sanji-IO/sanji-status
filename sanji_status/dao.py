import calendar
import logging
import os
import sqlite3
import time

from contextlib import closing
from datetime import datetime
from sqlite3 import OperationalError

from sanji_status.flock import Flock

logger = logging.getLogger(__name__)


class Database(object):
    VERSION = '0.1.0'

    def __init__(self, dbpath):
        self._dbpath = dbpath
        self._flock = Flock(dbpath + '.lock')

    def create_tables_if_needed(self):
        with self._flock:
            with closing(self._connect()) as conn:
                try:
                    version = self._get_config(conn, 'version')
                except OperationalError:
                    version = None

            if version == Database.VERSION:
                return

            logger.warning(
                'version mismatch, expecting %s, but %s: creating db again',
                Database.VERSION,
                version
            )
            os.unlink(self._dbpath)

            with closing(self._connect()) as conn:
                self._create_tables(conn)
                self._set_config(conn, 'version', Database.VERSION)
                conn.commit()

    def insert_reading(
            self,
            cpu_usage_percent,
            mem_usage_byte,
            disk_usage_byte,
            now_dt):
        with self._flock:
            with closing(self._connect()) as conn:
                conn.execute(
                    'INSERT INTO readings('
                    ' time_sec,'
                    ' cpu_usage_percent,'
                    ' mem_usage_byte,'
                    ' disk_usage_byte'
                    ' )'
                    ' VALUES(?, ?, ?, ?);',
                    (
                        Database._datetime_to_sec(now_dt),
                        cpu_usage_percent,
                        mem_usage_byte,
                        disk_usage_byte
                    )
                )

                conn.commit()

    def delete_old_readings(
            self,
            reading_count_to_keep):
        with self._flock:
            with closing(self._connect()) as conn:
                cursor = conn.cursor()
                current_count = cursor.execute(
                    'SELECT count(id) FROM readings;'
                ).fetchone()[0]

                if current_count <= reading_count_to_keep:
                    return

                conn.execute(
                    'DELETE FROM readings'
                    ' WHERE id NOT IN ('
                    '  SELECT id FROM readings'
                    '  ORDER BY id DESC'
                    '  LIMIT ?'
                    ' );',
                    (reading_count_to_keep, )
                )

                conn.commit()

    def get_latest_readings(
            self,
            count):
        '''
        Returns tuple-list like:
            [
                (time_dt, cpu_usage_percent, mem_usage_byte, disk_usage_byte),
                (datetime(2015, 5, 1), 12.5, 492983, 298389812)
            ]
        '''
        with self._flock:
            with closing(self._connect()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT'
                    ' time_sec,'
                    ' cpu_usage_percent,'
                    ' mem_usage_byte,'
                    ' disk_usage_byte'
                    ' FROM readings'
                    ' ORDER BY time_sec DESC'
                    ' LIMIT ?;',
                    (count,)
                )

                reading_list = [
                    (
                        Database._sec_to_datetime(row[0]),
                        row[1],
                        row[2],
                        row[3]
                    ) for row in cursor.fetchall()
                ]

        return reading_list

    def vacuum(self):
        with self._flock:
            with closing(self._connect()) as conn:
                conn.execute('VACUUM;')
                conn.commit()

    def _connect(self):
        '''Return sqlite3.Connection'''
        return sqlite3.connect(self._dbpath)

    def _create_tables(self, conn):
        conn.execute(
            'CREATE TABLE readings ('
            ' id                INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,'
            ' time_sec          BIGINT NOT NULL,'
            ' cpu_usage_percent FLOAT NOT NULL,'
            ' mem_usage_byte    BIGINT NOT NULL,'
            ' disk_usage_byte   BIGINT NOT NULL'
            ');'
        )

        conn.execute(
            'CREATE TABLE configs ('
            ' key   VARCHAR(64) PRIMARY KEY,'
            ' value VARCHAR(64) NOT NULL'
            ');'
        )

    def _get_config(self, conn, key):
        cursor = conn.cursor()
        cursor.execute(
            'SELECT value'
            ' FROM configs'
            ' WHERE key = ?;',
            (key, )
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return row[0]

    def _set_config(self, conn, key, value):
        conn.execute(
            'INSERT INTO configs(key, value)'
            ' VALUES(?, ?);',
            (key, value)
        )

    @classmethod
    def _datetime_to_sec(cls, time_dt):
        return calendar.timegm(time_dt.timetuple())

    @classmethod
    def _sec_to_datetime(cls, sec):
        ttuple = time.gmtime(sec)
        return datetime(
            year=ttuple.tm_year,
            month=ttuple.tm_mon,
            day=ttuple.tm_mday,
            hour=ttuple.tm_hour,
            minute=ttuple.tm_min,
            second=ttuple.tm_sec,
        )
