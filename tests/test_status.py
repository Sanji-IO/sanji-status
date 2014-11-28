import os
import sys
import unittest
import logging
import time

from sanji.connection.mockup import Mockup
from sanji.message import Message
from mock import patch

logger = logging.getLogger()

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
    from status import Status
    from status import ConvertData
    from status import PushThread
    from myobject import Myobject
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

        # fun_type = "memory"
        # case 1: kill_thread = false
        kill_thread.return_value = False
        rc = self.status.start_thread("memory")
        self.assertEqual(rc, False)

        # case 2: kill_thread = True
        PushThread.reset_mock()
        kill_thread.return_value = True
        rc = self.status.start_thread("memory")
        self.assertEqual(rc, True)
        PushThread.assert_called_once_with("memory")

        # fun_type = "disk"
        # case 1: kill_thread = false
        kill_thread.return_value = False
        rc = self.status.start_thread("disk")
        self.assertEqual(rc, False)

        # case 2: kill_thread = True
        PushThread.reset_mock()
        kill_thread.return_value = True
        rc = self.status.start_thread("disk")
        self.assertEqual(rc, True)
        PushThread.assert_called_once_with("disk")

        # exception
        PushThread.reset_mock()
        t = PushThread("cpu")
        t.start.side_effect = Exception("error exception!")
        rc = self.status.start_thread("cpu")
        self.assertEqual(rc, False)

    @patch("status.PushThread")
    def test_kill_thread(self, PushThread):
        # fun_type = cpu
        # case 1
        t = PushThread("cpu")
        self.status.thread_pool.append(("cpu", t))
        rc = self.status.kill_thread("cpu")
        t.join.assert_called_once_with()
        self.assertEqual(rc, True)

        # fun_type = memory
        # case 2
        PushThread.reset_mock()
        t = PushThread("memory")
        self.status.thread_pool.append(("memory", t))
        rc = self.status.kill_thread("memory")
        t.join.assert_called_once_with()
        self.assertEqual(rc, True)

        # fun_type = disk
        # case 3
        PushThread.reset_mock()
        t = PushThread("disk")
        self.status.thread_pool.append(("disk", t))
        rc = self.status.kill_thread("disk")
        t.join.assert_called_once_with()
        self.assertEqual(rc, True)

        # case 4: exception
        PushThread.reset_mock()
        self.status.thread_pool = []
        t = PushThread("cpu")
        t.join.side_effect = Exception("error exception!")
        self.status.thread_pool.append(("cpu", t))
        # PushThread.side_effect = Exception("error exception!")
        rc = self.status.kill_thread("cpu")
        self.assertEqual(rc, False)


class TestConverDataClass(unittest.TestCase):

    def test_human_size(self):
        # case 1: size_bytes = "0 Byte"
        rc = ConvertData.human_size(0)
        self.assertEqual(rc, "0 Byte")

        # case 2: size_bytes = "2048"
        rc = ConvertData.human_size(2048)
        self.assertEqual(rc, "2 KB")

        # case 3: size_bytes = "15728640"
        rc = ConvertData.human_size(15728640)
        self.assertEqual(rc, "15.0 MB")

    def test_get_time(self):
        rc = ConvertData.get_time()
        self.assertEqual(time.strftime("%Y/%m/%d %H:%M:%S",
                                       time.localtime(time.time())), rc)


class TestPushThreadClass(unittest.TestCase):

    @patch.object(PushThread, "get_cpu_data")
    def test_cpu_run(self, get_cpu_data):
        self.cpu_thread = PushThread("cpu")
        get_cpu_data.return_value = 55.6
        self.cpu_thread.start()
        time.sleep(0.2)
        get_cpu_data.assert_called_once_with()
        time.sleep(0.2)
        self.cpu_thread.join()
        self.cpu_thread = None

    @patch.object(PushThread, "get_memory_data")
    def test_memory_run(self, get_memory_data):
        self.memory_thread = PushThread("memory")
        get_memory_data.return_value = {"total": "2G",
                                        "used": "1.36G",
                                        "free": "0.64G"}
        self.memory_thread.start()
        time.sleep(0.1)
        get_memory_data.assert_called_once_with()
        time.sleep(0.1)
        self.memory_thread.join()
        self.memory_thread = None

    @patch.object(PushThread, "get_disk_data")
    def test_disk_run(self, get_disk_data):
        self.disk_thread = PushThread("disk")
        get_disk_data.return_value = {"total": "20G",
                                      "used": "13.6G",
                                      "free": "6.4G"}
        self.disk_thread.start()
        time.sleep(0.1)
        get_disk_data.assert_called_once_with()
        time.sleep(0.1)
        self.disk_thread.join()
        self.disk_thread = None

    @patch("psutil.cpu_percent")
    def test_get_cpu_data(self, cpu_percent):
        self.cpu_thread1 = PushThread("cpu")
        cpu_percent.return_value = 55.6
        self.cpu_thread1.start()
        time.sleep(0.1)
        rc = self.cpu_thread1.get_cpu_data()
        self.assertEqual(rc, cpu_percent.return_value)
        time.sleep(0.1)
        self.cpu_thread1.join()
        self.cpu_thread1 = None

    @patch("status.ConvertData.get_time")
    @patch("psutil.virtual_memory")
    def test_get_memory_data(self, mem_data, mock_time):
        self.memory_thread1 = PushThread("memory")
        mem_data.return_value = Myobject()
        mock_time.return_value = "2014/11/28 10:11:18"
        self.memory_thread1.start()
        time.sleep(0.1)
        rc = self.memory_thread1.get_memory_data()
        self.assertEqual(rc, {"time": "2014/11/28 10:11:18",
                              "total": "2 KB",
                              "used": "1 KB",
                              "free": "1 KB",
                              "usedPercentage": 50.0})
        time.sleep(0.1)
        self.memory_thread1.join()
        self.memory_thread1 = None

    @patch("status.ConvertData.get_time")
    @patch("psutil.disk_usage")
    def test_get_disk_data(self, disk_data, mock_time):
        self.disk_thread1 = PushThread("disk")
        disk_data.return_value = Myobject()
        mock_time.return_value = "2014/11/28 10:11:18"
        self.disk_thread1.start()
        time.sleep(0.1)
        rc = self.disk_thread1.get_disk_data()
        self.assertEqual(rc, {"time": "2014/11/28 10:11:18",
                              "total": "2 KB",
                              "used": "1 KB",
                              "free": "1 KB",
                              "usedPercentage": 50.0})
        time.sleep(0.1)
        self.disk_thread1.join()
        self.disk_thread1 = None

if __name__ == "__main__":
    unittest.main()
