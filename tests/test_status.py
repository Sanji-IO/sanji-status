import os
import sys
import unittest
import logging

from sanji.connection.mockup import Mockup
from sanji.message import Message
from mock import patch

logger = logging.getLogger()

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
    from status import Status
except ImportError as e:
    print e
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)


class TestStatusClass(unittest.TestCase):

    def setUp(self):
        self.status = Status(connection=Mockup())

    def tearDown(self):
        self.status.stop()
        self.status = None

    @patch("status.Status.start_cpu_thread")
    def test_get_cpu(self, start_cpu_thread):
        # case 1: without query string
        message = Message({"data": "test data", "query": {},
                           "param": {"id": "cpu"}})

        def resp1(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.get_cpu(message=message, response=resp1, test=True)

        # case 2: with query string and response code 200
        message = Message({"data": "test data", "query": {"push": "true"},
                           "param": {"id": "cpu"}})
        start_cpu_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 1, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.get_cpu(message=message, response=resp2, test=True)

        # case 3: with query string and response code 400
        start_cpu_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "server push failed"})
        self.status.get_cpu(message=message, response=resp3, test=True)

    @patch("status.Status.kill_cpu_thread")
    def test_put_cpu(self, kill_cpu_thread):
        # case 1: message donsn't has data attribute
        message = Message({})

        def resp1(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "Invaild Input"})
        self.status.put_cpu(message=message, response=resp1, test=True)

        # case 2: kill_cpu_thread = true
        message = Message({"data": {"cpuPush": 0}, "query": {"push": "true"},
                           "param": {"id": "cpu"}})
        kill_cpu_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.put_cpu(message=message, response=resp2, test=True)

        # case 3: kill_cpu_thread = false
        kill_cpu_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "cpu status error"})
        self.status.put_cpu(message=message, response=resp3, test=True)

    @patch("status.Status.start_memory_thread")
    def test_get_memory(self, start_memory_thread):
        # case 1: without query string
        message = Message({"data": "test data", "query": {},
                           "param": {"id": "memory"}})

        def resp1(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.get_memory(message=message, response=resp1, test=True)

        # case 2: with query string and response code 200
        message = Message({"data": "test data", "query": {"push": "true"},
                           "param": {"id": "memory"}})
        start_memory_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 1})
        self.status.get_memory(message=message, response=resp2, test=True)

        # case 3: with query string and response code 400
        start_memory_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "server push failed"})
        self.status.get_memory(message=message, response=resp3, test=True)

    @patch("status.Status.kill_memory_thread")
    def test_put_memory(self, kill_memory_thread):
        # case 1: message donsn't has data attribute
        message = Message({})

        def resp1(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "Invaild Input"})
        self.status.put_memory(message=message, response=resp1, test=True)

        # case 2: kill_memory_thread = true
        message = Message({"data": {"memoryPush": 0},
                           "query": {"push": "true"},
                           "param": {"id": "memory"}})
        kill_memory_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.put_memory(message=message, response=resp2, test=True)

        # case 3: kill_memeory_thread = false
        kill_memory_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "memory status error"})
        self.status.put_memory(message=message, response=resp3, test=True)

    @patch("status.Status.start_disk_thread")
    def test_get_disk(self, start_disk_thread):
        # case 1: without query string
        message = Message({"data": "test data", "query": {},
                           "param": {"id": "disk"}})

        def resp1(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.get_disk(message=message, response=resp1, test=True)

        # case 2: with query string and response code 200
        message = Message({"data": "test data", "query": {"push": "true"},
                           "param": {"id": "disk"}})
        start_disk_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 1,
                                    "memoryPush": 0})
        self.status.get_disk(message=message, response=resp2, test=True)

        # case 3: with query string and response code 400
        start_disk_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "server push failed"})
        self.status.get_disk(message=message, response=resp3, test=True)

    @patch("status.Status.kill_disk_thread")
    def test_put_disk(self, kill_disk_thread):
        # case 1: message donsn't has data attribute
        message = Message({})

        def resp1(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "Invaild Input"})
        self.status.put_disk(message=message, response=resp1, test=True)

        # case 2: kill_disk_thread = true
        message = Message({"data": {"diskPush": 0},
                           "query": {"push": "true"},
                           "param": {"id": "disk"}})
        kill_disk_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.put_disk(message=message, response=resp2, test=True)

        # case 3: kill_disk_thread = false
        kill_disk_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "disk status error"})
        self.status.put_disk(message=message, response=resp3, test=True)

    @patch("status.Status.kill_cpu_thread")
    def test_start_cpu_thread(self, kill_cpu_thread):
        # case 1: kill_cpu_thread = false
        kill_cpu_thread.return_value = False
        rc = self.status.start_cpu_thread()
        self.assertEqual(rc, False)

        # case 2: kill_cpu_thread = True
        # kill_cpu_thread.return_value = False


if __name__ == "__main__":
    unittest.main()
