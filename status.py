#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import logging
import sh
import psutil
import socket
import re
import tarfile
import glob
import requests
import datetime

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


def tar_syslog_files(output):
    """
    Tar and Compress (gz) syslog files to output directory
    """
    filelist = glob.glob("/var/log/syslog*") + \
        glob.glob("/var/log/uc8100-webapp*") + \
        glob.glob("/var/log/sanji*")

    with tarfile.open(output, "w:gz") as tar:
        for name in filelist:
            if not os.path.exists(name):
                continue
            _logger.debug("Packing %s" % (name))
            tar.add(name, arcname=os.path.basename(name))

    return output


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
            output = sh.grep(sh.dpkg("--get-selections"), "-E",
                             "mxcloud.*install")
            self.product = output.split()[0]
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
            sh.echo(hostname, _out="/etc/hostname")
        except Exception as e:
            raise e

    def get_product_version(self):

        try:
            pkg_info = sh.dpkg("-s", self.product)

            match = re.search(r"Version: (\S+)", str(pkg_info))
            if match:
                version = match.group(1).split(".")
                return "%s.%s" % (version[0], version[1])
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

        # FIXME: Most Linux filesystems reserve 5% space for use only the
        # root user. Use the following commane to check:
        #   $ sudo dumpe2fs /dev/mmcblk0p2 | grep -i reserved
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
                    "percent": disk_usage.percent + 5
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

    @Route(methods="post", resource="/system/syslog")
    def post_syslog(self, message, response):
        output = tar_syslog_files(
            "/run/shm/syslog-%s.tar.gz" %
            (datetime.datetime.now().strftime("%Y%m%d%H%M")))
        headers = message.data.get("headers", {})
        r = requests.post(
            message.data["url"],
            files={output: open(output, "rb")},
            headers=headers,
            verify=False
        )

        if r.status_code != requests.codes.ok:
            return response(
                code=r.status_code,
                data={"message": "Can't upload config."}
            )

        sh.rm("-rf", sh.glob("/run/shm/syslog-*.tar.gz"))
        resp = r.json()
        if "url" not in resp:
            return response(
                code=500, data={"message": "Can't get file link."})

        return response(data={"url": resp["url"]})

if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=0, format=FORMAT)
    _logger = logging.getLogger("status")
    logging.getLogger("sh").setLevel(logging.WARN)
    status = Status(connection=Mqtt())
    status.start()
