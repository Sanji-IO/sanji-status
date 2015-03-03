import os
import sys
import unittest
import logging
import time
from sanji.connection.mockup import Mockup
from sanji.message import Message
from mock import patch
from mock import Mock
from mock import mock_open
from mock import call

logger = logging.getLogger()


try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
    from status import Status
    from status import ConvertData
    from status import GrepThread
    from status import SystemData
    from myobject import Myobject
    from status import DataBase
except ImportError as e:
    print e
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)


class TestStatusClass(unittest.TestCase):

    @patch("status.Status.start_thread")
    def setUp(self, start_thread):
        self.status = Status(connection=Mockup())

    def tearDown(self):
        self.status.stop()
        self.status = None

    @patch("status.Status.parse_cpu_return_data")
    @patch("status.DataBase")
    def test_get_cpu(self, DataBase, parse_cpu_return_data):

        # case 1: should return code 200
        # arrange
        message = Message({"data": "test data", "query": {},
                           "param": {}})
        rtn_msg = [{"value": 1.6, "time": "2015/01/02 15:16:17"}]

        Status.RETRY_INTERVAL = 1
        Status.RETRY_TIMES = 1
        DataBase.get_table_count.return_value = 3
        DataBase.get_table_data.return_value = []
        parse_cpu_return_data.return_value = rtn_msg

        # act and assert
        def resp1(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, rtn_msg)
        self.status.get_cpu(message=message, response=resp1, test=True)

        # case 2: with parse_cpu_return_data failed, should response code 400
        # arrange
        message = Message({"data": "test data", "query": {"push": "true"},
                           "param": {}})

        Status.parse_cpu_return_data.side_effect = Exception(
            "parse cpu failed")

        # act and assert
        def resp2(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "get_cpu retry failed"})
        self.status.get_cpu(message=message, response=resp2, test=True)

    @patch("status.Status.parse_memory_return_data")
    @patch("status.DataBase")
    def test_get_memory(self,
                        DataBase,
                        parse_memory_return_data,
                        ):

        # case 1: should return code 200
        # arrange
        message = Message({"data": "test data", "query": {},
                           "param": {}})
        rtn_msg = [{"time": "2015/01/02 15:11:11",
                    "usedPercentage": "2.6",
                    "total": "100 GB",
                    "free": "5 GB",
                    "used": "95 GB",
                    }]

        Status.RETRY_INTERVAL = 1
        Status.RETRY_TIMES = 1
        DataBase.get_table_count.return_value = 3
        DataBase.get_cpu_data.return_value = []
        parse_memory_return_data.return_value = rtn_msg

        # act and assert
        def resp1(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, rtn_msg)
        self.status.get_memory(message=message, response=resp1, test=True)

        # case 2: parse_memory_return_data failed, should response code 400
        # arrange
        message = Message({"data": "test data", "query": {"push": "true"},
                           "param": {"id": "memory"}})

        Status.parse_memory_return_data.side_effect = Exception(
            "parse memory failed")

        # act and assert
        def resp2(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "get_memory retry failed"})
        self.status.get_memory(message=message, response=resp2, test=True)

    @patch("status.Status.parse_disk_return_data")
    @patch("status.DataBase")
    def test_get_disk(self,
                      DataBase,
                      parse_disk_return_data,
                      ):

        # case 1: should return code 200
        # arrange
        message = Message({"data": "test data", "query": {},
                           "param": {}})
        rtn_msg = [{"time": "2015/01/02 15:11:11",
                    "usedPercentage": "5.6",
                    "total": "100 GB",
                    "free": "5 GB",
                    "used": "95 GB",
                    }]
        Status.RETRY_INTERVAL = 1
        Status.RETRY_TIMES = 1
        DataBase.get_table_count.return_value = 3
        DataBase.get_cpu_data.return_value = []
        parse_disk_return_data.return_value = rtn_msg

        # act and assert
        def resp1(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, rtn_msg)
        self.status.get_disk(message=message, response=resp1, test=True)

        # case 2: parse_disk_return_data failed, should response code 400
        # arrange
        message = Message({"data": "test data", "query": {"push": "true"},
                           "param": {}})

        Status.parse_disk_return_data.side_effect = Exception(
            "parse disk failed")

        def resp2(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "get_disk retry failed"})
        self.status.get_disk(message=message, response=resp2, test=True)

    @patch("status.SystemData.showdata")
    def test_get_system_data(self, showdata):
        message = Message({})

        def resp1(code=200, data=None):
            showdata.return_value = {"firmware": "MXcloud",
                                     "hostname": "Moxa", "storage": "50.0 GB",
                                     "uptime": "1 days, 23:22:21"}
            showdata.assert_called_once_with()
        self.status.get_system_data(message=message, response=resp1, test=True)

    @patch("status.SystemData.set_hostname")
    def test_put_system_data(self, set_hostname):
        message = Message({})

        # case1: invalid input
        def resp1(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "Invaild Input"})
        self.status.put_system_data(message=message, response=resp1, test=True)

        # case2: set hostname success
        message = Message({"data": {"hostname": "Moxa"},
                           "query": {},
                           "param": {"id": "showdata"}})
        set_hostname.return_value = True

        def resp2(code=200, data=None):
            self.assertEqual(code, 200)
            self.assertEqual(data, {"hostname": "Moxa"})
        self.status.put_system_data(message=message, response=resp2, test=True)

        # case3: set hostname failed
        set_hostname.return_value = False

        def resp3(code=200, data=None):
            self.assertEqual(code, 400)
            self.assertEqual(data, {"message": "Set hostname error"})
        self.status.put_system_data(message=message, response=resp3, test=True)

    @patch("status.GrepThread")
    @patch("status.Status.kill_thread")
    def test_start_thread(self, kill_thread, GrepThread):

        # case 1: kill_thread = false
        kill_thread.return_value = False
        rc = self.status.start_thread()
        self.assertEqual(rc, False)

        # case 2: kill_thread = True
        kill_thread.return_value = True
        rc = self.status.start_thread()
        self.assertEqual(rc, True)
        GrepThread.assert_called_once_with()

        # case 3: GrepThread exception
        GrepThread.reset_mock()
        t = GrepThread()
        t.start.side_effect = Exception("error exception!")
        rc = self.status.start_thread()
        self.assertEqual(rc, False)

    @patch("status.GrepThread")
    def test_kill_thread(self, GrepThread):
        self.status.thread_pool = []

        # case 1
        t = GrepThread()
        self.status.thread_pool.append((t))
        rc = self.status.kill_thread()
        t.join.assert_called_once_with()
        self.assertEqual(rc, True)

        # case 2: exception
        GrepThread.reset_mock()
        self.status.thread_pool = []
        t = GrepThread()
        t.join.side_effect = Exception("error exception!")
        self.status.thread_pool.append((t))
        rc = self.status.kill_thread()
        self.assertEqual(rc, False)

    def test_parse_cpu_return_data(self):

        # case 1: data_cnt >= MAX_RETURN_CNT
        # arrange
        Status.MAX_RETURN_CNT = 3
        data_cnt = 5
        data_obj = [CpuObject(1.0, "2015/01/02 15:11:00"),
                    CpuObject(1.2, "2015/01/02 15:11:05"),
                    CpuObject(1.4, "2015/01/02 15:11:10"),
                    CpuObject(1.6, "2015/01/02 15:11:15"),
                    CpuObject(1.8, "2015/01/02 15:11:20")
                    ]
        check_msg = []

        for item in data_obj[2:5]:
            check_msg.append({
                "time": item.time,
                "value": item.usage
            })

        # act
        rtn_data = self.status.parse_cpu_return_data(data_obj, data_cnt)

        # assert
        self.assertEqual(rtn_data, check_msg)

        # case 2: data_cnt < MAX_RETURN_CNT
        # arrange
        Status.MAX_RETURN_CNT = 5
        data_cnt = 2
        data_obj = []
        data_obj = [CpuObject(1.0, "2015/01/02 15:11:00"),
                    CpuObject(1.2, "2015/01/02 15:11:05")
                    ]
        check_msg = []

        for item in data_obj:
            check_msg.append({
                "time": item.time,
                "value": item.usage
            })

        # act
        rtn_data = self.status.parse_cpu_return_data(data_obj, data_cnt)

        # assert
        self.assertEqual(rtn_data, check_msg)

    def test_parse_memory_return_data(self):

        # case 1: data_cnt >= MAX_RETURN_CNT
        # arrange
        Status.MAX_RETURN_CNT = 3
        data_cnt = 5
        data_obj = [MemoryObject(5.0, "100 MB", "95 MB", "5 MB",
                                 "2015/01/02 15:11:00"),
                    MemoryObject(6.0, "100 MB", "94 MB", "6 MB",
                                 "2015/01/02 15:11:05"),
                    MemoryObject(7.0, "100 MB", "93 MB", "7 MB",
                                 "2015/01/02 15:11:10"),
                    MemoryObject(8.0, "100 MB", "92 MB", "8 MB",
                                 "2015/01/02 15:11:15"),
                    MemoryObject(9.0, "100 MB", "91 MB", "9 MB",
                                 "2015/01/02 15:11:20")
                    ]
        check_msg = []

        for item in data_obj[2:5]:
            check_msg.append({
                "time": item.time,
                "total": item.total,
                "used": item.used,
                "free": item.free,
                "usedPercentage": item.usedPercentage
            })

        # act
        rtn_data = self.status.parse_memory_return_data(data_obj, data_cnt)

        # assert
        self.assertEqual(rtn_data, check_msg)

        # case 2: data_cnt < MAX_RETURN_CNT
        # arrange
        Status.MAX_RETURN_CNT = 5
        data_cnt = 2
        data_obj = []
        data_obj = [MemoryObject(5.0, "100 MB", "95 MB", "5 MB",
                                 "2015/01/02 15:11:00"),
                    MemoryObject(6.0, "100 MB", "94 MB", "6 MB",
                                 "2015/01/02 15:11:05")
                    ]
        check_msg = []

        for item in data_obj:
            check_msg.append({
                "time": item.time,
                "total": item.total,
                "used": item.used,
                "free": item.free,
                "usedPercentage": item.usedPercentage
            })

        # act
        rtn_data = self.status.parse_memory_return_data(data_obj, data_cnt)

        # assert
        self.assertEqual(rtn_data, check_msg)

    def test_parse_disk_return_data(self):

        # case 1: data_cnt >= MAX_RETURN_CNT
        # arrange
        Status.MAX_RETURN_CNT = 3
        data_cnt = 5
        data_obj = [DiskObject(5.0, "100 GB", "95 GB", "5 GB",
                               "2015/01/02 15:11:00"),
                    DiskObject(6.0, "100 GB", "94 GB", "6 GB",
                               "2015/01/02 15:11:05"),
                    DiskObject(7.0, "100 GB", "93 GB", "7 GB",
                               "2015/01/02 15:11:10"),
                    DiskObject(8.0, "100 GB", "92 GB", "8 GB",
                               "2015/01/02 15:11:15"),
                    DiskObject(9.0, "100 GB", "91 GB", "9 GB",
                               "2015/01/02 15:11:20")
                    ]
        check_msg = []

        for item in data_obj[2:5]:
            check_msg.append({
                "time": item.time,
                "total": item.total,
                "used": item.used,
                "free": item.free,
                "usedPercentage": item.usedPercentage
            })

        # act
        rtn_data = self.status.parse_disk_return_data(data_obj, data_cnt)

        # assert
        self.assertEqual(rtn_data, check_msg)

        # case 2: data_cnt < MAX_RETURN_CNT
        # arrange
        Status.MAX_RETURN_CNT = 5
        data_cnt = 2
        data_obj = []
        data_obj = [DiskObject(5.0, "100 GB", "95 GB", "5 GB",
                               "2015/01/02 15:11:00"),
                    DiskObject(6.0, "100 GB", "94 GB", "6 GB",
                               "2015/01/02 15:11:05")
                    ]
        check_msg = []

        for item in data_obj:
            check_msg.append({
                "time": item.time,
                "total": item.total,
                "used": item.used,
                "free": item.free,
                "usedPercentage": item.usedPercentage
            })

        # act
        rtn_data = self.status.parse_disk_return_data(data_obj, data_cnt)

        # assert
        self.assertEqual(rtn_data, check_msg)


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


class TestDataBaseClass(unittest.TestCase):

    def setUp(self):
        self.database = DataBase(":memory:")

    def tearDown(self):
        pass

    def test_insert_table_with_cpu_type(self):

        # arrange
        data = {"time": "2015/01/01 11:12:13",
                "usage": 55.6}

        # act
        self.database.insert_table("cpu", data)

        # assert
        rtn_obj_list = self.database.get_table_data("cpu")
        check_data = {"time": rtn_obj_list[0].time,
                      "usage": rtn_obj_list[0].usage}

        self.assertEqual(data, check_data)

    def test_insert_table_with_memory_type(self):

        # arrange
        data = {"time": "2015/01/01 11:12:13",
                "total": "100 MB",
                "used": "5 MB",
                "free": "95 MB",
                "usedPercentage": 5.0}

        # act
        self.database.insert_table("memory", data)

        # assert
        rtn_obj_list = self.database.get_table_data("memory")
        check_data = {"time": rtn_obj_list[0].time,
                      "total": rtn_obj_list[0].total,
                      "used": rtn_obj_list[0].used,
                      "free": rtn_obj_list[0].free,
                      "usedPercentage": rtn_obj_list[0].usedPercentage}

        self.assertEqual(data, check_data)

    def test_insert_table_with_disk_type(self):

        # arrange
        data = {"time": "2015/01/01 11:12:13",
                "total": "100 GB",
                "used": "5 GB",
                "free": "95 GB",
                "usedPercentage": 5.0}

        # act
        self.database.insert_table("disk", data)

        # assert
        rtn_obj_list = self.database.get_table_data("disk")
        check_data = {"time": rtn_obj_list[0].time,
                      "total": rtn_obj_list[0].total,
                      "used": rtn_obj_list[0].used,
                      "free": rtn_obj_list[0].free,
                      "usedPercentage": rtn_obj_list[0].usedPercentage}

        self.assertEqual(data, check_data)

    def test_delete_table_with_cpu_type(self):

        # arrange
        data = {"time": "2015/01/01 11:12:13",
                "usage": 55.6}
        self.database.insert_table("cpu", data)
        before_cnt = self.database.get_table_count("cpu")

        # act
        self.database.delete_table("cpu")

        # assert
        after_cnt = self.database.get_table_count("cpu")
        self.assertEqual(before_cnt, after_cnt+1)

    def test_delete_table_with_memory_type(self):

        # arrange
        data = {"time": "2015/01/01 11:12:13",
                "total": "100 MB",
                "used": "5 MB",
                "free": "95 MB",
                "usedPercentage": 5.0}

        self.database.insert_table("memory", data)
        before_cnt = self.database.get_table_count("memory")

        # act
        self.database.delete_table("memory")

        # assert
        after_cnt = self.database.get_table_count("memory")
        self.assertEqual(before_cnt, after_cnt+1)

    def test_delete_table_with_disk_type(self):

        # arrange
        data = {"time": "2015/01/01 11:12:13",
                "total": "100 GB",
                "used": "5 GB",
                "free": "95 GB",
                "usedPercentage": 5.0}

        self.database.insert_table("disk", data)
        before_cnt = self.database.get_table_count("disk")

        # act
        self.database.delete_table("disk")

        # assert
        after_cnt = self.database.get_table_count("disk")
        self.assertEqual(before_cnt, after_cnt+1)

    def test_get_table_with_cpu_type(self):

        # arrange
        data1 = {"time": "2015/01/01 11:12:13",
                 "usage": 55.6}
        data2 = {"time": "2015/01/01 11:13:14",
                 "usage": 56.5}
        self.database.insert_table("cpu", data1)
        self.database.insert_table("cpu", data2)

        # act
        rtn_obj_list = self.database.get_table_data("cpu")
        check_data1 = {"time": rtn_obj_list[0].time,
                       "usage": rtn_obj_list[0].usage}
        check_data2 = {"time": rtn_obj_list[1].time,
                       "usage": rtn_obj_list[1].usage}

        # assert
        self.assertEqual(check_data1, data1)
        self.assertEqual(check_data2, data2)

    def test_get_table_with_memory_type(self):

        # arrange
        data1 = {"time": "2015/01/01 11:12:13",
                 "total": "100 MB",
                 "used": "5 MB",
                 "free": "95 MB",
                 "usedPercentage": 5.0}
        data2 = {"time": "2015/01/01 11:13:14",
                 "total": "100 MB",
                 "used": "6 MB",
                 "free": "94 MB",
                 "usedPercentage": 6.0}
        self.database.insert_table("memory", data1)
        self.database.insert_table("memory", data2)

        # act
        rtn_obj_list = self.database.get_table_data("memory")
        check_data1 = {"time": rtn_obj_list[0].time,
                       "total": rtn_obj_list[0].total,
                       "used": rtn_obj_list[0].used,
                       "free": rtn_obj_list[0].free,
                       "usedPercentage": rtn_obj_list[0].usedPercentage}
        check_data2 = {"time": rtn_obj_list[1].time,
                       "total": rtn_obj_list[1].total,
                       "used": rtn_obj_list[1].used,
                       "free": rtn_obj_list[1].free,
                       "usedPercentage": rtn_obj_list[1].usedPercentage}

        # assert
        self.assertEqual(check_data1, data1)
        self.assertEqual(check_data2, data2)

    def test_get_table_with_disk_type(self):

        # arrange
        data1 = {"time": "2015/01/01 11:12:13",
                 "total": "100 GB",
                 "used": "5 GB",
                 "free": "95 GB",
                 "usedPercentage": 5.0}
        data2 = {"time": "2015/01/01 11:13:14",
                 "total": "100 GB",
                 "used": "6 GB",
                 "free": "94 GB",
                 "usedPercentage": 6.0}
        self.database.insert_table("disk", data1)
        self.database.insert_table("disk", data2)

        # act
        rtn_obj_list = self.database.get_table_data("disk")
        check_data1 = {"time": rtn_obj_list[0].time,
                       "total": rtn_obj_list[0].total,
                       "used": rtn_obj_list[0].used,
                       "free": rtn_obj_list[0].free,
                       "usedPercentage": rtn_obj_list[0].usedPercentage}
        check_data2 = {"time": rtn_obj_list[1].time,
                       "total": rtn_obj_list[1].total,
                       "used": rtn_obj_list[1].used,
                       "free": rtn_obj_list[1].free,
                       "usedPercentage": rtn_obj_list[1].usedPercentage}

        # assert
        self.assertEqual(check_data1, data1)
        self.assertEqual(check_data2, data2)

    def get_table_count_with_cpu_type(self):

        # arrange
        data1 = {"time": "2015/01/01 11:12:13",
                 "usage": 55.6}
        data2 = {"time": "2015/01/01 11:13:14",
                 "usage": 56.5}
        self.database.insert_table("cpu", data1)
        self.database.insert_table("cpu", data2)

        # act
        cpu_cnt = self.database.get_table_count("cpu")

        # assert
        self.assertEqual(cpu_cnt, 2)

    def get_table_count_with_memory_type(self):

        # arrange
        data1 = {"time": "2015/01/01 11:12:13",
                 "total": "100 MB",
                 "used": "5 MB",
                 "free": "95 MB",
                 "usedPercentage": 5.0}
        data2 = {"time": "2015/01/01 11:13:14",
                 "total": "100 MB",
                 "used": "6 MB",
                 "free": "94 MB",
                 "usedPercentage": 6.0}
        self.database.insert_table("memory", data1)
        self.database.insert_table("memory", data2)

        # act
        memory_cnt = self.database.get_table_count("memory")

        # assert
        self.assertEqual(memory_cnt, 2)

    def get_table_count_with_disk_type(self):

        # arrange
        data1 = {"time": "2015/01/01 11:12:13",
                 "total": "100 GB",
                 "used": "5 GB",
                 "free": "95 GB",
                 "usedPercentage": 5.0}
        data2 = {"time": "2015/01/01 11:13:14",
                 "total": "100 GB",
                 "used": "6 GB",
                 "free": "94 GB",
                 "usedPercentage": 6.0}
        self.database.insert_table("disk", data1)
        self.database.insert_table("disk", data2)

        # act
        disk_cnt = self.database.get_table_count("disk")

        # assert
        self.assertEqual(disk_cnt, 2)

    def test_check_table_count_with_cpu_type_should_return_true(self):

        # arrange
        DataBase.MAX_TABLE_CNT = 5
        data = {"time": "2015/01/01 11:12:13",
                "usage": 55.6}

        for i in range(1, 11):
            self.database.insert_table("cpu", data)

        # act
        rc = self.database.check_table_count("cpu")

        # assert
        self.assertEqual(rc, True)

    def test_check_table_count_with_cpu_type_should_return_false(self):

        # arrange
        DataBase.MAX_TABLE_CNT = 5
        data = {"time": "2015/01/01 11:12:13",
                "usage": 55.6}

        for i in range(1, 3):
            self.database.insert_table("cpu", data)

        # act
        rc = self.database.check_table_count("cpu")

        # assert
        self.assertEqual(rc, False)

    def test_check_table_count_with_memory_type_should_return_true(self):

        # arrange
        DataBase.MAX_TABLE_CNT = 5
        data = {"time": "2015/01/01 11:12:13",
                "total": "100 MB",
                "used": "5 MB",
                "free": "95 MB",
                "usedPercentage": 5.0}

        for i in range(1, 11):
            self.database.insert_table("memory", data)

        # act
        rc = self.database.check_table_count("memory")

        # assert
        self.assertEqual(rc, True)

    def test_check_table_count_with_memory_type_should_return_false(self):

        # arrange
        DataBase.MAX_TABLE_CNT = 5
        data = {"time": "2015/01/01 11:12:13",
                "total": "100 MB",
                "used": "5 MB",
                "free": "95 MB",
                "usedPercentage": 5.0}

        for i in range(1, 3):
            self.database.insert_table("memory", data)

        # act
        rc = self.database.check_table_count("memory")

        # assert
        self.assertEqual(rc, False)

    def test_check_table_count_with_disk_type_should_return_true(self):

        # arrange
        DataBase.MAX_TABLE_CNT = 5
        data = {"time": "2015/01/01 11:12:13",
                "total": "100 GB",
                "used": "5 GB",
                "free": "95 GB",
                "usedPercentage": 5.0}

        for i in range(1, 11):
            self.database.insert_table("disk", data)

        # act
        rc = self.database.check_table_count("disk")

        # assert
        self.assertEqual(rc, True)

    def test_check_table_count_with_disk_type_should_return_false(self):

        # arrange
        DataBase.MAX_TABLE_CNT = 5
        data = {"time": "2015/01/01 11:12:13",
                "total": "100 GB",
                "used": "5 GB",
                "free": "95 GB",
                "usedPercentage": 5.0}

        for i in range(1, 3):
            self.database.insert_table("disk", data)

        # act
        rc = self.database.check_table_count("disk")

        # assert
        self.assertEqual(rc, False)


class TestGrepThreadClass(unittest.TestCase):

    @patch.object(GrepThread, "get_disk_data")
    @patch.object(GrepThread, "get_memory_data")
    @patch.object(GrepThread, "get_cpu_data")
    @patch("status.DataBase")
    def test_run(self,
                 DataBase,
                 get_cpu_data,
                 get_memory_data,
                 get_disk_data):

        #arrange
        self.grep_thread = GrepThread()
        cpu_msg = {"time": "2015/01/01 11:12:13",
                   "usage": 55.6}
        memory_msg = {"time": "2015/01/01 11:12:13",
                      "total": "100 MB",
                      "used": "5 MB",
                      "free": "95 MB",
                      "usedPercentage": 5.0}
        disk_msg = {"time": "2015/01/01 11:12:13",
                    "total": "100 GB",
                    "used": "5 GB",
                    "free": "95 GB",
                    "usedPercentage": 5.0}

        get_cpu_data.return_value = cpu_msg
        get_memory_data.return_value = memory_msg
        get_disk_data.return_value = disk_msg

        DataBase().check_table_count.return_value = True
        delete_calls = [call("cpu"), call("memory"), call("disk")]
        insert_calls = [call("cpu", cpu_msg),
                        call("memory", memory_msg),
                        call("disk", disk_msg)]

        # act and assert   
        self.grep_thread.start()
        time.sleep(2)
        get_cpu_data.assert_called_with()
        get_memory_data.assert_called_with()
        get_disk_data.assert_called_with()
        DataBase().delete_table.assert_has_calls(delete_calls, any_order=True)
        DataBase().insert_table.assert_has_calls(insert_calls, any_order=True)
        time.sleep(1)
        self.grep_thread.join()
        self.grep_thread = None

    @patch("status.ConvertData.get_time")
    @patch("psutil.cpu_percent")
    @patch("status.DataBase")
    def test_get_cpu_data(self, DataBase, cpu_percent, mock_time):

        # arrange
        cpu_msg = {"time": "2015/01/01 11:11:11",
                   "usage": 55.6}
        mock_time.return_value = "2015/01/01 11:11:11"
        cpu_percent.return_value = 55.6

        # act and assert
        self.cpu_thread1 = GrepThread()
        self.cpu_thread1.start()
        time.sleep(1)

        rc = self.cpu_thread1.get_cpu_data()
        self.assertEqual(rc, cpu_msg)
        time.sleep(0.1)
        self.cpu_thread1.join()
        self.cpu_thread1 = None

    @patch("status.ConvertData.get_time")
    @patch("psutil.virtual_memory")
    @patch("status.DataBase")
    def test_get_memory_data(self, DataBase, mem_data, mock_time):

        # arrange
        memory_msg = {"time": "2014/11/28 10:11:18",
                      "total": "2 KB",
                      "used": "1 KB",
                      "free": "1 KB",
                      "usedPercentage": 50.0}
        mem_data.return_value = Myobject()
        mock_time.return_value = "2014/11/28 10:11:18"

        # act and assert
        self.memory_thread1 = GrepThread()
        self.memory_thread1.start()
        time.sleep(1)
        rc = self.memory_thread1.get_memory_data()
        self.assertEqual(rc, memory_msg)
        time.sleep(0.1)
        self.memory_thread1.join()
        self.memory_thread1 = None

    @patch("status.ConvertData.get_time")
    @patch("psutil.disk_usage")
    @patch("status.DataBase")
    def test_get_disk_data(self, DataBase, disk_data, mock_time):

        # arrange
        disk_msg = {"time": "2014/11/28 10:11:18",
                    "total": "2 KB",
                    "used": "1 KB",
                    "free": "1 KB",
                    "usedPercentage": 50.0}
        disk_data.return_value = Myobject()
        mock_time.return_value = "2014/11/28 10:11:18"

        # act and assert
        self.disk_thread1 = GrepThread()
        self.disk_thread1.start()
        time.sleep(1)
        rc = self.disk_thread1.get_disk_data()
        self.assertEqual(rc, disk_msg)
        time.sleep(0.1)
        self.disk_thread1.join()
        self.disk_thread1 = None


class TestSystemDataClass(unittest.TestCase):

    @patch("status.subprocess.Popen")
    def test_get_firmware(self, Popen):
        process_mock = Mock()
        # case 1: Popen success
        attrs = {"communicate.return_value": ("MoxaCloud", "error")}
        process_mock.configure_mock(**attrs)
        Popen.return_value = process_mock
        rc = SystemData.get_firmware()
        self.assertEqual(rc, "MoxaCloud")

        # case 2: Popen success
        Popen.side_effect = Exception("error exception!")
        SystemData.get_firmware()

    @patch("status.socket.gethostname")
    def test_get_hostname(self, gethostname):
        gethostname.return_value = "Moxa"
        rc = SystemData.get_hostname()
        self.assertEqual(rc, "Moxa")

    @patch("psutil.disk_usage")
    def test_get_storage(self, disk_data):
        disk_data.return_value = Myobject()
        rc = SystemData.get_storage()
        self.assertEqual(rc, "1 KB")

    def test_get_uptime(self):
        m = mock_open(read_data="1644143.1 6520752.96")
        m().readline.return_value = "1644143.1 6520752.96"
        with patch("status.open", m, create=True):
            rc = SystemData.get_uptime()
            self.assertEqual(rc, "19 days, 0:42:23")

    @patch("status.subprocess.call")
    def test_set_hostname(self, call):
        # case 1: set hostname success
        call.return_value = 0
        rc = SystemData.set_hostname("new_host")
        self.assertEqual(rc, True)

        # case 2: set hostname failed
        call.return_value = 1
        rc = SystemData.set_hostname("new_host")
        self.assertEqual(rc, False)


class CpuObject(object):
    def __init__(self, usage, time):
        self.usage = usage
        self.time = time


class MemoryObject(object):
    def __init__(self, usedPercentage, total, free, used, time):
        self.usedPercentage = usedPercentage
        self.total = total
        self.free = free
        self.used = used
        self.time = time


class DiskObject(object):
    def __init__(self, usedPercentage, total, free, used, time):
        self.usedPercentage = usedPercentage
        self.total = total
        self.free = free
        self.used = used
        self.time = time


if __name__ == "__main__":
    unittest.main()
