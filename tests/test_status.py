#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys
import sh
import logging
import unittest
from mock import patch

from sanji.connection.mockup import Mockup
from sanji.message import Message

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
    from status import Status
except ImportError as e:
    print os.path.dirname(os.path.realpath(__file__)) + '/../'
    print sys.path
    print e
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)

dirpath = os.path.dirname(os.path.realpath(__file__))

PKG_STATUS = "\
        Package: uc8100-mxcloud-cg \
        Status: install ok installed \
        Priority: extra \
        Section: utils \
        Installed-Size: 62 \
        Maintainer: Aeluin Chen <aeluin_chen@moxa.com> \
        Architecture: all \
        Source: mxcloud \
        Version: 0.1.2-1 \
        Depends: sanji-bundle-bootstrap, sanji-bundle-cellular, \
sanji-bundle-dns, sanji-bundle-ethernet, sanji-bundle-firmware, \
sanji-bundle-import-export, sanji-bundle-reboot, sanji-bundle-route, \
sanji-bundle-status, sanji-bundle-time, sanji-controller \
        Conffiles: \
         /etc/init.d/uc8100-mxcloud-cg df7aab4b91d6b2e3d3439a8e82cdcdd7 \
          /etc/default/uc8100-mxcloud-cg a02f25446f618b44ae180609eb8d0290 \
          Description: mxcloud package for Moxa cloud gateway on UC-8100-LX \
          Homepage: http://www.moxa.com"


class TestStatusClass(unittest.TestCase):

    @patch("sh.grep")
    @patch("sh.dpkg")
    def setUp(self, mock_dpkg, mock_grep):
        self.name = "status"
        self.bundle = Status(connection=Mockup())
        self.bundle.product = "uc8100-mxcloud-cg"

    def tearDown(self):
        self.bundle.stop()
        self.bundle = None
        try:
            os.remove("%s/data/%s.json" % (dirpath, self.name))
        except OSError:
            pass

        try:
            os.remove("%s/data/%s.json.backup" % (dirpath, self.name))
        except OSError:
            pass

    @patch("sh.dpkg")
    @patch("sh.grep")
    def test__init(self, mock_grep, mock_dpkg):
        """
        init
        """
        mock_grep.return_value = \
            "uc8100-mxcloud-cg install"
        self.bundle.init()
        self.assertEqual(self.bundle.product, "uc8100-mxcloud-cg")

    @patch("sh.dpkg")
    def test__init_cannot_get_product(self, mock_dpkg):
        """
        init: cannot get product name
        """
        mock_dpkg.side_effect = sh.ErrorReturnCode_1
        self.bundle.init()
        self.assertEqual(self.bundle.product, None)

    @patch("socket.gethostname")
    def test__get_hostname(self, mock_gethostname):
        """
        get_hostname
        """
        mock_gethostname.return_value = "moxa"
        hostname = self.bundle.get_hostname()
        self.assertEqual(hostname, "moxa")

    @patch("socket.gethostname")
    def test__get_hostname__failed(self, mock_gethostname):
        """
        get_hostname: failed
        """
        mock_gethostname.side_effect = OSError
        hostname = self.bundle.get_hostname()
        self.assertEqual(hostname, "")

    @patch("sh.hostname")
    def test__set_hostname(self, mock_sethostname):
        """
        set_hostname
        """
        self.bundle.set_hostname("test")

    @patch("sh.hostname")
    def test__set_hostname_failed(self, mock_sethostname):
        """
        set_hostname: failed
        """
        mock_sethostname.side_effect = OSError
        with self.assertRaises(OSError):
            self.bundle.set_hostname("test")

    @patch("sh.dpkg")
    def test__get_product_version(self, mock_dpkg):
        """
        get_product_version
        """
        mock_dpkg.return_value = PKG_STATUS
        version = self.bundle.get_product_version()
        self.assertEqual("0.1.2-1", version)

    @patch("sh.dpkg")
    def test__get_product_version__failed(self, mock_dpkg):
        """
        get_product_version: failed
        """
        mock_dpkg.side_effect = OSError
        version = self.bundle.get_product_version()
        self.assertEqual("(not installed)", version)

    @patch.object(Status, "get_product_version")
    @patch.object(Status, "get_hostname")
    def test__get(self, mock_gethostname, mock_getversion):
        """
        get
        """
        mock_gethostname.return_value = "moxa"
        mock_getversion.return_value = "0.1.2-1"
        message = Message({"data": {}, "query": {}, "param": {}})

        def resp(code=200, data=None):
            self.assertEqual(200, code)
            self.assertEqual("0.1.2-1", data["version"])
        self.bundle.get_status(message=message, response=resp, test=True)

    @patch.object(Status, "set_hostname")
    def test__put(self, mock_sethostname):
        """
        put
        "data": {
            "hostname": "test"
        }
        """
        message = Message({"data": {}, "query": {}, "param": {}})
        message.data["hostname"] = "test"

        def resp(code=200, data=None):
            self.assertEqual(200, code)
            self.assertEqual("test", data["hostname"])
        self.bundle.put_status(message=message, response=resp, test=True)
        self.assertEqual("test", self.bundle.model.db["hostname"])

if __name__ == "__main__":
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=20, format=FORMAT)
    logger = logging.getLogger('Status Test')
    unittest.main()
