#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import logging
import sh
import psutil
import socket
import re

from sanji.core import Sanji
from sanji.core import Route
from sanji.connection.mqtt import Mqtt
from sanji.model_initiator import ModelInitiator

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
        try:  # pragma: no cover
            bundle_env = kwargs["bundle_env"]
        except KeyError:
            bundle_env = os.getenv("BUNDLE_ENV", "debug")

        # load configuration
        self.path_root = os.path.abspath(os.path.dirname(__file__))
        if bundle_env == "debug":  # pragma: no cover
            self.path_root = "%s/tests" % self.path_root

        try:
            self.load(self.path_root)
        except:
            self.stop()
            raise IOError("Cannot load any configuration.")

        # find product name
        try:
            output = sh.grep(sh.dpkg("-l"), "mxcloud")
            self.product = output.split()[1]
        except:
            self.product = None

    def load(self, path):
        """
        Load the configuration. If configuration is not installed yet,
        initialise them with default value.

        Args:
            path: Path for the bundle, the configuration should be located
                under "data" directory.
        """
        self.model = ModelInitiator("status", path, backup_interval=-1)
        if self.model.db is None:
            raise IOError("Cannot load any configuration.")
        self.save()

    def save(self):
        """
        Save and backup the configuration.
        """
        self.model.save_db()
        self.model.backup_db()

    def get_hostname(self):
        try:
            return socket.gethostname()
        except:
            return ""

    def set_hostname(self, hostname):
        try:
            sh.hostname("-b", hostname)
        except Exception as e:
            raise e

    def get_product_version(self):

        try:
            pkg_info = sh.dpkg("-s", self.product)

            match = re.search(r"Version: (\S+)", pkg_info)
            if match:
                return match.group(1)
        except:
            pass
        return "(not installed)"

    @Route(methods="get", resource="/system/status")
    def get_status(self, message, response):
        hostname = self.get_hostname()
        product_version = self.get_product_version()

        with open("/proc/uptime", "r") as f:
            uptime_sec = int(float(f.readline().split()[0]))

        disk_usage = psutil.disk_usage("/")

        return response(
            code=200,
            data={
                "hostname": hostname,
                "version": product_version,
                "uptimeSec": uptime_sec,
                "diskUsage": {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": disk_usage.percent
                }
            }
        )

    @Route(methods="put", resource="/system/status")
    def put_status(self, message, response, schema=HOSTNAME_SCHEMA):
        if not(hasattr(message, "data")):
            return response(code=400, data={"message": "Invaild Input"})

        hostname = message.data['hostname']
        self.set_hostname(hostname)

        self.model.db['hostname'] = hostname
        self.save()
        return response(data=self.model.db)


if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=0, format=FORMAT)
    _logger = logging.getLogger("status")

    status = Status(connection=Mqtt())
    status.start()
