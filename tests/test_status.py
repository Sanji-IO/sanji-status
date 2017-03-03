#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys
import logging
import unittest
import tempfile
from mock import patch

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
    from status import Status
    from status import get_password, set_password
except ImportError as e:
    print os.path.dirname(os.path.realpath(__file__)) + '/../'
    print sys.path
    print e
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)

dirpath = os.path.dirname(os.path.realpath(__file__))

PVERSION_INFO = "UC-8112-LX-CG version 1.1 Build 12345678"
VERSION_INFO = "1.1 Build 12345678"


class TestStatusClass(unittest.TestCase):

    @patch("status.sh")
    def setUp(self, mock_sh):
        self.root_path = os.path.abspath(os.path.dirname(__file__) + "/../")
        self.name = "status"
        self.bundle = Status(name="status", path=self.root_path)

    def tearDown(self):
        self.bundle = None
        try:
            os.remove("%s/data/%s.json" % (dirpath, self.name))
        except OSError:
            pass

        try:
            os.remove("%s/data/%s.json.backup" % (dirpath, self.name))
        except OSError:
            pass

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

    @patch("sh.sed")
    @patch("sh.echo")
    @patch("sh.hostname")
    def test__set_hostname(self, mock_sethostname, mock_echo, mock_sed):
        """
        set_hostname
        """
        self.bundle.set_hostname("test")

    @patch("sh.sed")
    @patch("sh.echo")
    @patch("sh.hostname")
    def test__set_hostname_failed(self, mock_sethostname, mock_echo, mock_sed):
        """
        set_hostname: failed
        """
        mock_sethostname.side_effect = OSError
        with self.assertRaises(OSError):
            self.bundle.set_hostname("test")

    @patch("status.sh")
    def test__get_product_version(self, mock_sh):
        """
        get_product_version
        """
        mock_sh.pversion.return_value = PVERSION_INFO
        version = self.bundle.get_product_version()
        self.assertEqual(VERSION_INFO, version)

    @patch("status.sh")
    def test__get_product_version__failed(self, mock_sh):
        """
        get_product_version: failed
        """
        mock_sh.pversion.side_effect = OSError
        version = self.bundle.get_product_version()
        self.assertEqual("(not installed)", version)

    def test__get_password(self):
        """
        get_password
        """
        with tempfile.NamedTemporaryFile() as temp:
            temp.write("moxa:$6$Hs/8c4S4$gBHEMrckbK9dpFJ0xrrO07TecyKNgTeB2Q69PKwFuuZC47W0k7zdWyF115efj9c5UmpxjB.iz.sW/QbhEYER1/:16247:0:99999:7:::")  # noqa
            temp.flush()
            passhash = get_password("moxa", temp.name)
            self.assertEqual(passhash, "$6$Hs/8c4S4$gBHEMrckbK9dpFJ0xrrO07TecyKNgTeB2Q69PKwFuuZC47W0k7zdWyF115efj9c5UmpxjB.iz.sW/QbhEYER1/")  # noqa

    @patch("status.usermod")
    def test__set_password(self, mock_usermod):
        """
        set_password
        """
        set_password("moxa", "user")
        mock_usermod.called_args
        self.assertTrue(mock_usermod.called)
    '''
    @patch("status.tar_syslog_files")
    @patch("status.requests.post")
    @patch("status.sh")
    def test_post_syslog(
            self, mock_sh, mock_post_requests, mock_tar_syslog_files):
        """
        post
        "data": {
            "hostname": "test"
        }
        """
        message = Message({
            "data": {
                "headers": {
                    "xxx": "yyy"
                },
                "url": "https://localhost"
            }, "query": {}, "param": {}})
        download_url = "https://localhost/api/v1/download/123456789"
        filename = "xxx.tar.gz"
        mock_tar_syslog_files.return_value = filename
        mock_post_result = Mock()
        mock_post_requests.return_value = mock_post_result
        mock_post_result.status_code = requests.codes.ok
        mock_post_result.json.return_value = {
            "url": download_url
        }

        def resp(code=200, data=None):
            self.assertEqual(200, code)
            self.assertEqual(download_url, data["url"])

        with patch("__builtin__.open"):
            self.bundle.post_syslog(message=message, response=resp, test=True)
        mock_tar_syslog_files.assert_called_once_with(ANY)
        self.assertTrue(sh.rm.called)
        mock_post_requests.assert_called_once_with(
            message.data["url"],
            files={filename: ANY},
            headers=message.data["headers"],
            verify=False
        )
    '''


if __name__ == "__main__":
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=20, format=FORMAT)
    logger = logging.getLogger('Status Test')
    unittest.main()
