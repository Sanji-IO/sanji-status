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
import netifaces
from passlib.hash import sha512_crypt
from sh import grep, cut, usermod
from sanji.model import Model

from libmxidaf_py import TagV2


_logger = logging.getLogger("sanji.status")
HOSTNAME_REGEX = re.compile("[^a-zA-Z\d\-]")


def is_valid_hostname(hostname):
    hostname_len = len(hostname)
    if hostname_len < 0 or hostname_len > 255:
        raise StatusError("Invaild Hostname")
    if hostname[:1] != "-" and all(map(
            lambda x: len(x) and not
            HOSTNAME_REGEX.search(x), hostname.split("."))):
        return hostname
    raise StatusError("Invaild Hostname")


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


def get_password(username="moxa", shadow_file="/etc/shadow"):
    return cut(grep(username, shadow_file), "-f", 2, "-d", ":").strip()


def set_password(password, username="moxa", salt=None):
    hashed_password = sha512_crypt.encrypt(password, rounds=10000)
    return usermod("-p", hashed_password, username)


class StatusError(Exception):
    pass


class SysStatus(object):

    def __init__(self):
        self._tagv2 = TagV2.instance()
        self._cpu_usage = 0.0
        self._memory_usage = 0.0

    def _on_tag_callback(self, equipment_name, tag_name, tag):
        if equipment_name == "SYSTEM":
            if tag_name == "cpu_usage":
                self._cpu_usage = tag.value().as_float()
            elif tag_name == "memory_usage":
                self._memory_usage = tag.value().as_float()

    def run(self):
        self._tagv2.subscribe_callback(self._on_tag_callback)
        self._tagv2.subscribe("SYSTEM", "cpu_usage")
        self._tagv2.subscribe("SYSTEM", "memory_usage")

    @property
    def cpu_usage(self):
        return self._cpu_usage

    @property
    def memory_usage(self):
        return self._memory_usage


class Status(Model):

    def __init__(self, *args, **kwargs):
        super(Status, self).__init__(*args, **kwargs)

        self.sysstatus = SysStatus()
        self.sysstatus.run()

    def get_hostname(self):
        """Get hostname

            Return:
                hostname (str)
        """
        try:
            return socket.gethostname()
        except:
            return ""

    def set_hostname(self, hostname):
        """Update hostname

            Args:
                hostname (str): hostname to be updated
        """
        try:
            is_valid_hostname(hostname)

            sh.hostname("-b", hostname)
            sh.echo(hostname, _out="/etc/hostname")
            self.update(id=1, newObj={"hostname": hostname})
        except Exception as e:
            raise e

    def get_product_version(self):
        """Get product version

            Return:
                version (str): product version (#.#)
        """
        # FIXME: get version via pversion
        try:
            return " ".join(sh.pversion().split(" ")[2:])
        except:
            pass
        return "(not installed)"

    def get_uptime(self):
        """Get system uptime by seconds.

            Return:
                uptime (int): system uptime, unit: second
        """
        try:
            with open("/proc/uptime", "r") as f:
                uptime_sec = int(float(f.readline().split()[0]))
        except Exception as e:
            _logger.error("Cannot get the uptime: %s" % e)
            uptime_sec = 0
        return uptime_sec

    def get_net_interfaces(self):
        """Get network interface list

            Returns:
                interface list (array)
        """
        try:
            ifaces = netifaces.interfaces()
            ifaces = [x for x in ifaces if not
                      (x.startswith("lo") or x.startswith("mon."))]
            return ifaces
        except Exception as e:
            _logger.error("Cannot get interfaces: %s" % e)
            return []

    def _parse_collectd_value(self, value):
        if len(value) != 1:
            return 0.0
        else:
            return value[0].split('=')[1]

    def get_cpu_usage(self):
        return self.sysstatus.cpu_usage

    def get_memory_usage(self):
        return self.sysstatus.memory_usage

    def get_memory(self):
        return psutil.virtual_memory().total

    def _disk_get_alias(self, mapping, device):
        dev = mapping["device"].search(device)
        if dev is None:
            return None
        alias = "%s" % mapping["alias"]
        if mapping["part"] is None:
            return alias
        part = mapping["part"].findall(dev.group(0))
        if part is not None:
            alias += "-%s" % "-".join(part)
        return alias

    def disk_get_alias(self, device):
        # SD: /dev/mmcblk0, /dev/mmcblk0p1
        # USB: /dev/sda, /dev/sda1
        # search() for device
        # findall() for drive and partition
        dev_mapping = [
            {"alias": "System",
             "device": re.compile("/dev/root"),
             "part": None},
            {"alias": "SD",
             "device": re.compile("(?<=/dev/mmcblk)\w+"),
             "part": re.compile("^\d+|\d+$")},
            {"alias": "USB",
             "device": re.compile("(?<=/dev/sd)\w+"),
             "part": re.compile("^[a-z]+|\d+$")}
        ]
        for mapping in dev_mapping:
            alias = self._disk_get_alias(mapping, device)
            if alias is not None:
                return alias
        return "UNKNOWN"

    def get_disks(self):
        """Get disks usages, including system, SD card, and USB stick.

            Returns:
                disks (array): array with all disks information
                    [{
                      "name": disk alias,
                      "mount": mount point (ex: /mnt/usb0),
                      "device": disk device (ex: /dev/sda1),
                      "usage": {
                        "total": total storage size (unit: byte),
                        "used": used storage size (unit: byte),
                        "free": free storage size (unit: byte),
                        "percent": used percent
                      }
                    }]
        """
        disks = []
        disk_parts = psutil.disk_partitions()
        for disk_part in disk_parts:
            disk = {}
            disk["name"] = self.disk_get_alias(disk_part.device)
            disk["mount"] = disk_part.mountpoint
            disk["device"] = disk_part.device
            disk["usage"] = {}

            # FIXME: Most Linux filesystems reserve 5% space for use only the
            # root user. Use the following commane to check:
            #   $ sudo dumpe2fs /dev/mmcblk0p2 | grep -i reserved
            disk_usage = psutil.disk_usage(disk_part.mountpoint)
            disk["usage"]["total"] = disk_usage.total
            disk["usage"]["used"] = disk_usage.used
            disk["usage"]["free"] = disk_usage.free
            disk["usage"]["percent"] = disk_usage.percent
            disks.append(disk)
        return disks

    def reboot(self):
        _logger.info("Rebooting...")
        sh.reboot()


if __name__ == "__main__":
    path_root = os.path.dirname(os.path.abspath(__file__)) + "/../"
    status = Status(name="status", path=path_root)
    print status.get_hostname()
    print status.get_product_version()
    print status.get_uptime()
    print status.get_net_interfaces()
    print status.get_memory()
    print status.get_disks()
    print status.getAll()
    print status.get(id=1)
    # status.set_hostname("test")
