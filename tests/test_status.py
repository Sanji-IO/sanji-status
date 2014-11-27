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

    @patch("status.Status.start_thread")
    def test_get_cpu(self, start_thread):
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
        start_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 1, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.get_cpu(message=message, response=resp2, test=True)

        # case 3: with query string and response code 400
        start_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "server push failed"})
        self.status.get_cpu(message=message, response=resp3, test=True)

    @patch("status.Status.kill_thread")
    def test_put_cpu(self, kill_thread):
        # case 1: message donsn't has data attribute
        message = Message({})

        def resp1(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "Invaild Input"})
        self.status.put_cpu(message=message, response=resp1, test=True)

        # case 2: kill_thread = true
        message = Message({"data": {"cpuPush": 0}, "query": {"push": "true"},
                           "param": {"id": "cpu"}})
        kill_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.put_cpu(message=message, response=resp2, test=True)

        # case 3: kill_thread = false
        kill_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "cpu status error"})
        self.status.put_cpu(message=message, response=resp3, test=True)

    @patch("status.Status.start_thread")
    def test_get_memory(self, start_thread):
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
        start_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 1})
        self.status.get_memory(message=message, response=resp2, test=True)

        # case 3: with query string and response code 400
        start_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "server push failed"})
        self.status.get_memory(message=message, response=resp3, test=True)

    @patch("status.Status.kill_thread")
    def test_put_memory(self, kill_thread):
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
        kill_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.put_memory(message=message, response=resp2, test=True)

        # case 3: kill_memeory_thread = false
        kill_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "memory status error"})
        self.status.put_memory(message=message, response=resp3, test=True)

    @patch("status.Status.start_thread")
    def test_get_disk(self, start_thread):
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
        start_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 1,
                                    "memoryPush": 0})
        self.status.get_disk(message=message, response=resp2, test=True)

        # case 3: with query string and response code 400
        start_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "server push failed"})
        self.status.get_disk(message=message, response=resp3, test=True)

    @patch("status.Status.kill_thread")
    def test_put_disk(self, kill_thread):
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
        kill_thread.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"cpuPush": 0, "diskPush": 0,
                                    "memoryPush": 0})
        self.status.put_disk(message=message, response=resp2, test=True)

        # case 3: kill_disk_thread = false
        kill_thread.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "disk status error"})
        self.status.put_disk(message=message, response=resp3, test=True)

    @patch("status.PushThread")
    @patch("status.Status.kill_thread")
    def test_start_thread(self, kill_thread, PushThread):
        # fun_type = "cpu"
        # case 1: kill_thread = false
        kill_thread.return_value = False
        rc = self.status.start_thread("cpu")
        self.assertEqual(rc, False)

        # case 2: kill_thread = True
        kill_thread.return_value = True
        rc = self.status.start_thread("cpu")
        self.assertEqual(rc, True)
        PushThread.assert_called_once_with("cpu")

        # case 3: fun_type error
        rc = self.status.start_thread("fail function type")
        self.assertEqual(rc, False)

        # fun_type = "memory"
        # case 1: kill_thread = false
        kill_thread.return_value = False
        rc = self.status.start_thread("memory")
        self.assertEqual(rc, False)

        # case 2: kill_thread = True
        kill_thread.return_value = True
        rc = self.status.start_thread("memory")
        self.assertEqual(rc, True)

        # fun_type = "disk"
        # case 1: kill_thread = false
        kill_thread.return_value = False
        rc = self.status.start_thread("disk")
        self.assertEqual(rc, False)

        # case 2: kill_thread = True
        kill_thread.return_value = True
        rc = self.status.start_thread("disk")
        self.assertEqual(rc, True)

    @patch("status.PushThread")
    def test_kill_thread(self, PushThread):
        # fun_type = cpu
        # case 1
        t = PushThread("cpu")
        self.status.cpu_thread_pool.append(t)
        rc = self.status.kill_thread("cpu")
        t.join.assert_called_once_with()
        self.assertEqual(rc, True)

        # fun_type = memory
        # case 2
        PushThread.reset_mock()
        t = PushThread("memory")
        self.status.memory_thread_pool.append(t)
        rc = self.status.kill_thread("memory")
        t.join.assert_called_once_with()
        self.assertEqual(rc, True)

        # fun_type = disk
        # case 3
        PushThread.reset_mock()
        t = PushThread("disk")
        self.status.disk_thread_pool.append(t)
        rc = self.status.kill_thread("disk")
        t.join.assert_called_once_with()
        self.assertEqual(rc, True)

        # case 4: error fun_type
        rc = self.status.kill_thread("error fun_type")
        self.assertEqual(rc, False)

        # case 5: exception
        PushThread.reset_mock()
        self.status.cpu_thread_pool = []
        t = PushThread("cpu")
        t.join.side_effect = Exception("error exception!")
        self.status.cpu_thread_pool.append(t)
        # PushThread.side_effect = Exception("error exception!")
        rc = self.status.kill_thread("cpu")
        self.assertEqual(rc, False)

if __name__ == "__main__":
    unittest.main()
