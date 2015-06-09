#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import os
import psutil
import subprocess
import socket
import re

from subprocess import CalledProcessError

from sanji.core import Sanji
from sanji.core import Route
from sanji.model_initiator import ModelInitiator
from sanji.connection.mqtt import Mqtt

from voluptuous import Schema
from voluptuous import Required
from voluptuous import REMOVE_EXTRA
from voluptuous import Length
from voluptuous import All
from voluptuous import MultipleInvalid

from sanji_status.dao import Database
from sanji_status.monitor import MonitorThread

_logger = logging.getLogger("sanji.status")

HOSTNAME_REGEX = re.compile("[^a-zA-Z\d\-]")


def is_valid_hostname(hostname):
    if hostname[:1] != "-" and all(map(
            lambda x: len(x) and not
            HOSTNAME_REGEX.search(x), hostname.split("."))):
        return hostname
    raise MultipleInvalid("Invaild Hostname")


class Status(Sanji):

    DB_PATH = os.path.join(
        '/', 'dev', 'shm', 'sanji-bundle-status', 'history.sqlite3'
    )
    LOG_COUNT = 300
    LOG_INTERVAL_SEC = 1

    HOSTNAME_SCHEMA = Schema({
        Required("hostname"): All(is_valid_hostname, Length(1, 255))
    }, extra=REMOVE_EXTRA)

    def init(self, *args, **kwargs):
        path_root = os.path.abspath(os.path.dirname(__file__))
        self.model = ModelInitiator("status", path_root, backup_interval=1)

        subprocess.call(['mkdir', '-p', os.path.dirname(Status.DB_PATH)])

        database = Database(Status.DB_PATH)
        database.create_tables_if_needed()

        # init thread pool
        self.thread_pool = []

        # start a thread to get status
        self.start_thread()

    @Route(methods="get", resource="/system/status/cpu")
    def get_cpu(self, message, response):
        database = Database(Status.DB_PATH)
        reading_list = database.get_latest_readings(Status.LOG_COUNT)
        _logger.debug('get_cpu(): len(reading_list) = %d', len(reading_list))

        return response(
            code=200,
            data=[
                {
                    'time': str_from_datetime(reading[0]),
                    'percent': reading[1]
                }
                for reading in reading_list
            ]
        )

    @Route(methods="get", resource="/system/status/memory")
    def get_memory(self, message, response):
        """
        get MAX_RETURN_CNT memory data from memory table and then response
        """

        database = Database(Status.DB_PATH)
        reading_list = database.get_latest_readings(Status.LOG_COUNT)

        total_byte = psutil.virtual_memory().total

        return response(
            code=200,
            data=[
                {
                    'time': str_from_datetime(reading[0]),
                    'totalByte': total_byte,
                    'usedByte': reading[2],
                    'usedPercent': reading[2] * 100.0 / total_byte
                }
                for reading in reading_list
            ]
        )

    @Route(methods="get", resource="/system/status/disk")
    def get_disk(self, message, response):
        """
        get MAX_RETURN_CNT disk data from disk table and then response
        """

        database = Database(Status.DB_PATH)
        reading_list = database.get_latest_readings(Status.LOG_COUNT)

        total_byte = psutil.disk_usage('/').total

        return response(
            code=200,
            data=[
                {
                    'time': str_from_datetime(reading[0]),
                    'totalByte': total_byte,
                    'usedByte': reading[3],
                    'usedPercent': reading[3] * 100.0 / total_byte
                }
                for reading in reading_list
            ]
        )

    @Route(methods="get", resource="/system/status/showdata")
    def get_system_data(self, message, response):
        # Tcall SystemStatus class to get data
        hostname = socket.gethostname()
        firmware = subprocess.check_output(['kversion', '-a'])[:-1]

        mxcloud_version = self._get_mxcloud_version()

        with open('/proc/uptime', 'r') as f:
            uptime_sec = int(float(f.readline().split()[0]))

        disk_free_byte = psutil.disk_usage('/').free

        return response(
            code=200,
            data={
                'hostname': hostname,
                'firmware': firmware,
                'mxcloudVersion': mxcloud_version,
                'uptimeSec': uptime_sec,
                'diskFreeByte': disk_free_byte
            }
        )

    @Route(methods="put", resource="/system/status/showdata",
           schema=HOSTNAME_SCHEMA)
    def put_system_data(self, message, response):
        if not(hasattr(message, "data")):
            return response(code=400, data={"message": "Invaild Input"})

        hostname = message.data['hostname']
        self.set_hostname(hostname)

        self.model.db['hostname'] = hostname
        self.model.save_db()

    def start_thread(self):
        try:
            kill_rc = self.kill_thread()
            if kill_rc is False:
                return False

            # start thread to grep status
            t = MonitorThread(
                Status.DB_PATH,
                Status.LOG_INTERVAL_SEC,
                Status.LOG_COUNT
            )
            t.start()

            # save to thread pool
            self.thread_pool.append((t))
            _logger.debug("start thread pool: %s" % self.thread_pool)
            return True

        except Exception as e:
            _logger.debug("start thread error: %s" % e)
            return False

    def kill_thread(self):
        try:
            # kill thread from thread pool
            for idx, value in enumerate(self.thread_pool):
                _logger.debug("kill thread id:%s" % value)
                value.join()

                # pop thread_id in thread pool
                self.thread_pool.pop(idx)
            return True
        except Exception as e:
            _logger.debug("kill thread error: %s" % e)
            return False

    def set_hostname(self, hostname):
        exit_status = subprocess.call(['hostname', '-b', hostname])
        if exit_status != 0:
            raise ValueError

    def _get_mxcloud_version(self):

        for package in ['mxcloud-cs', 'mxcloud-cg']:
            try:
                pkg_info = subprocess.check_output(['dpkg', '-s', package])
                break
            except CalledProcessError:
                continue

        match = re.search(r'Version: (\S+)', pkg_info)
        if not match:
            return '(not installed)'

        return match.group(1)


def str_from_datetime(time_dt):
    return time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')


if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=0, format=FORMAT)
    _logger = logging.getLogger("ssh")

    status = Status(connection=Mqtt())
    status.start()
