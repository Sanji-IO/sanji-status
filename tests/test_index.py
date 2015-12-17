#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
import unittest
import glob
from mock import Mock
from mock import patch
from sanji.connection.mockup import Mockup
from sanji.message import Message

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")
    from index import Index
    from status import Status as status
except ImportError as e:
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    print (e)
    exit(1)


class TestIndexClass(unittest.TestCase):

    def setUp(self):
        self.root_path = os.path.abspath(os.path.dirname(__file__) + "/../")
        self.jsons = glob.glob(os.path.join(self.root_path, "data/*.json"))
        self.backups = glob.glob(os.path.join(self.root_path, "data/*.backup"))
        for file in self.jsons + self.backups:
            os.unlink(file)

        self.index = Index(connection=Mockup())

    def tearDown(self):
        files = glob.glob(os.path.join(self.root_path, "data/*.json")) + \
            glob.glob(os.path.join(self.root_path, "data/*.backup"))
        for prevConfig in files:
            try:
                os.unlink(prevConfig)
            except:
                pass

        self.index.stop()
        self.index = None

    @patch.object(status, "get_disks")
    @patch.object(status, "get_memory")
    @patch.object(status, "get_uptime")
    @patch.object(status, "get_product_version")
    @patch.object(status, "get_hostname")
    def test__get_status(
        self, mock_hostname, mock_version, mock_uptime, mock_memory,
            mock_disks):
        """test__get_status: Get system status"""
        mock_hostname.return_value = "Moxa"
        mock_version.return_value = "1.1"
        mock_uptime.return_value = 181499
        mock_memory.return_value = 257286144
        mock_disks.return_value = []
        resp = Mock()
        self.index.get_status(message=None, response=resp, test=True)
        resp.assert_called_once_with(
            data={
                "hostname": mock_hostname.return_value,
                "version": mock_version.return_value,
                "uptimeSec": mock_uptime.return_value,
                "memory": mock_memory.return_value,
                "disks": mock_disks.return_value})

    @patch.object(status, "set_hostname")
    def test__put_status(self, mock_set_hostname):
        """test__put_status: Update hostname"""
        resp = Mock()
        message = Message({
            "data": {
                "hostname": "test"
            }
        })
        self.index.put_status(message=message, response=resp, test=True)
        resp.assert_called_once_with(data=message.data)

    @patch.object(status, "get_net_interfaces")
    def test__get_net_interfaces(self, mock_netifaces):
        """test__get_net_interfaces: Get network interface list"""
        mock_netifaces.return_value = ["eth0", "eth1", "wwan0"]

        resp = Mock()
        self.index.get_net_interface(message=None, response=resp, test=True)
        resp.assert_called_once_with(data=mock_netifaces.return_value)


if __name__ == "__main__":
    unittest.main()
