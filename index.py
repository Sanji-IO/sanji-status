#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import logging
import sh
import requests
import datetime
import status
from status import set_password
from time import sleep
from sanji.core import Sanji
from sanji.core import Route
from sanji.model_initiator import ModelInitiator
from sanji.connection.mqtt import Mqtt

from voluptuous import Schema
from voluptuous import Required, REMOVE_EXTRA, Length, Any, All


_logger = logging.getLogger("sanji.status")


class Index(Sanji):

    HOSTNAME_SCHEMA = Schema({
        Required("hostname"): All(Any(unicode, str), Length(1, 255))
    }, extra=REMOVE_EXTRA)

    PASSWORD_SCHEMA = Schema({
        Required("password"): All(Any(unicode, str), Length(1, 255))
    }, extra=REMOVE_EXTRA)

    GPS_SCHEMA = Schema({
        "lat": Any(int, float),
        "lng": Any(int, float),
    }, extra=REMOVE_EXTRA)

    ALIASNAME_SCHEMA = Schema(All(Any(unicode, str), Length(0, 255)))

    PROPERTIES_SCHEMA = {
        "aliasName": ALIASNAME_SCHEMA,
        "gps": GPS_SCHEMA
    }

    UPDATE_PROPERTY_SCHEMA = Schema({
        "data": Any(list, dict, str, unicode, int, float)
    }, extra=REMOVE_EXTRA)

    def init(self, *args, **kwargs):
        path_root = os.path.abspath(os.path.dirname(__file__))
        self.status = status.Status(name="status", path=path_root)
        self.properties = ModelInitiator(
            model_name="properties", model_path=path_root)

        # Check aliasName
        if self.properties.db.get("aliasName", "$ModelName") == "$ModelName":
            self.set_alias()

    def set_alias(self):
        try:
            version = sh.pversion()
            self.properties.db["aliasName"] = version.split()[0]
        except Exception:
            self.properties.db["aliasName"] = "ThingsPro"
        self.properties.save_db()

    @Route(methods="get", resource="/system/status")
    def get_status(self, message, response):
        if message.query.get("fields") is None:
            return response(
                data={
                    "hostname": self.status.get_hostname(),
                    "version": self.status.get_product_version(),
                    "uptimeSec": self.status.get_uptime(),
                    "cpuUsage": self.status.get_cpu_usage(),
                    "memoryUsage": self.status.get_memory_usage(),
                    "memory": self.status.get_memory(),
                    "disks": self.status.get_disks()
                }
            )

        fields = [_.strip() for _ in message.query.get("fields").split(',')]
        data = {}
        if "hostname" in fields:
            data["hostname"] = self.status.get_hostname()
        if "version" in fields:
            data["version"] = self.status.get_product_version()
        if "uptimeSec" in fields:
            data["uptimeSec"] = self.status.get_uptime()
        if "cpuUsage" in fields:
            data["cpuUsage"] = self.status.get_cpu_usage()
        if "memoryUsage" in fields:
            data["memoryUsage"] = self.status.get_memory_usage()
        if "memory" in fields:
            data["memory"] = self.status.get_memory()
        if "disks" in fields:
            data["disks"] = self.status.get_disks()

        return response(data=data)

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

    @Route(methods="post", resource="/system/reboot")
    def post_reboot(self, message, response):
        response()
        sleep(3)
        self.status.reboot()

    @Route(methods="put", resource="/system/password", schema=PASSWORD_SCHEMA)
    def post_passwd(self, message, response):
        set_password(message.data["password"])
        return response()

    @Route(methods="get", resource="/system/properties")
    def get_properties(self, message, response):
        return response(data=self.properties.db)

    @Route(methods="get", resource="/system/properties/:key")
    def get_property(self, message, response):
        val = self.properties.db.get(message.param["key"], None)
        if val is None:
            return response(code=404)
        return response(data=val)

    @Route(methods="put", resource="/system/properties/:key",
           schema=UPDATE_PROPERTY_SCHEMA)
    def put_property(self, message, response):
        key = message.param["key"]
        if key not in Index.PROPERTIES_SCHEMA:
            return response(code=400, data={"message": "wrong key."})
        data = Index.PROPERTIES_SCHEMA.get(key)(message.data["data"])
        self.properties.db[key] = data
        self.properties.save_db()
        return response(data=self.properties.db[key])

    @Route(methods="get", resource="/mxc/system/equipments")
    def get_system_equipments(self, message, response):
        equs = [
            {
                "equipmentName": "SYSTEM",
                "equipmentTags": [
                    {
                        "name": "cpu_usage",
                        "dataType": "float64",
                        "access": "ro",
                        "size": 8,
                        "description": "CPU Usage"
                    },
                    {
                        "name": "memory_usage",
                        "dataType": "float64",
                        "access": "ro",
                        "size": 8,
                        "description": "Memory Usage"
                    },
                    {
                        "name": "disk_usage",
                        "dataType": "float64",
                        "access": "ro",
                        "size": 8,
                        "description": "Disk Usage"
                    }
                ]
            }
        ]
        return response(data=equs)


if __name__ == "__main__":
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=0, format=FORMAT)
    _logger = logging.getLogger("status")
    logging.getLogger("sh").setLevel(logging.WARN)
    bundle = Index(connection=Mqtt())
    bundle.start()
