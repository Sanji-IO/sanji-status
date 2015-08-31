#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import psutil
import subprocess
import socket
import re

from subprocess import CalledProcessError

from sanji.core import Sanji
from sanji.core import Route
from sanji.connection.mqtt import Mqtt

from voluptuous import Schema
from voluptuous import Required
from voluptuous import REMOVE_EXTRA
from voluptuous import Length
from voluptuous import All
from voluptuous import MultipleInvalid


_logger = logging.getLogger("sanji.status")

HOSTNAME_REGEX = re.compile("[^a-zA-Z\d\-]")


def is_valid_hostname(hostname):
    if hostname[:1] != "-" and all(map(
            lambda x: len(x) and not
            HOSTNAME_REGEX.search(x), hostname.split("."))):
        return hostname
    raise MultipleInvalid("Invaild Hostname")


class Status(Sanji):

    HOSTNAME_SCHEMA = Schema({
        Required("hostname"): All(is_valid_hostname, Length(1, 255))
    }, extra=REMOVE_EXTRA)

    def init(self, *args, **kwargs):
        pass

    def set_hostname(self, hostname):
        exit_status = subprocess.call(['hostname', '-b', hostname])
        if exit_status != 0:
            raise ValueError

    def get_product_version(self):

        for package in ['mxcloud-cg']:
            try:
                pkg_info = subprocess.check_output(['dpkg', '-s', package])
                break
            except CalledProcessError:
                continue

        match = re.search(r'Version: (\S+)', pkg_info)
        if not match:
            return '(not installed)'

        return match.group(1)

    @Route(methods="get", resource="/system/status")
    def get_system_info(self, message, response):
        # Tcall SystemStatus class to get data
        hostname = socket.gethostname()

        product_version = self.get_product_version()

        with open('/proc/uptime', 'r') as f:
            uptime_sec = int(float(f.readline().split()[0]))

        disk_free_byte = psutil.disk_usage('/').free

        return response(
            code=200,
            data={
                'hostname': hostname,
                'version': product_version,
                'uptimeSec': uptime_sec,
                'diskFreeByte': disk_free_byte
            }
        )

    @Route(methods="put", resource="/system/status",
           schema=HOSTNAME_SCHEMA)
    def put_system_info(self, message, response):
        if not(hasattr(message, "data")):
            return response(code=400, data={"message": "Invaild Input"})

        hostname = message.data['hostname']
        self.set_hostname(hostname)

        self.model.db['hostname'] = hostname
        self.model.save_db()


if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=0, format=FORMAT)
    _logger = logging.getLogger("status")

    status = Status(connection=Mqtt())
    status.start()
