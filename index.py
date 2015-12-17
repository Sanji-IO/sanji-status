#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import logging
import sh
import requests
import datetime
import status

from sanji.core import Sanji
from sanji.core import Route
from sanji.connection.mqtt import Mqtt

from voluptuous import Schema
from voluptuous import Required, REMOVE_EXTRA, Length, Any, All


_logger = logging.getLogger("sanji.status")


class Index(Sanji):

    HOSTNAME_SCHEMA = Schema({
        Required("hostname"): All(Any(unicode, str), Length(1, 255))
    }, extra=REMOVE_EXTRA)

    def init(self, *args, **kwargs):
        path_root = os.path.abspath(os.path.dirname(__file__))
        self.status = status.Status(name="status", path=path_root)

    @Route(methods="get", resource="/system/status")
    def get_status(self, message, response):
        return response(
            data={
                "hostname": self.status.get_hostname(),
                "version": self.status.get_product_version(),
                "uptimeSec": self.status.get_uptime(),
                "memory": self.status.get_memory(),
                "disks": self.status.get_disks()
            }
        )

    @Route(methods="put", resource="/system/status")
    def put_status(self, message, response, schema=HOSTNAME_SCHEMA):
        self.status.set_hostname(message.data['hostname'])
        return response(data=message.data)

    @Route(methods="get", resource="/network/interfaces")
    def get_net_interface(self, message, response):
        ifaces = self.status.get_net_interfaces()
        return response(data=ifaces)

    @Route(methods="post", resource="/system/syslog")
    def post_syslog(self, message, response):
        output = status.tar_syslog_files(
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
    bundle = Index(connection=Mqtt())
    bundle.start()