#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import os
import threading
import time
import psutil
import subprocess
import socket

from sanji.core import Sanji
from sanji.core import Route
from sanji.model_initiator import ModelInitiator
from sanji.connection.mqtt import Mqtt

from threading import Thread
from datetime import timedelta

from sqlalchemy import asc
from sqlalchemy import func
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from mxc.flock import Flock

logger = logging.getLogger()

DB_PATH = "./status_db"

# prepare lock
global_lock = Flock(DB_PATH + ".lock")


class Status(Sanji):

    MAX_RETURN_CNT = 5

    def init(self, *args, **kwargs):
        path_root = os.path.abspath(os.path.dirname(__file__))
        self.model = ModelInitiator("status", path_root, backup_interval=1)

        # init thread pool
        self.thread_pool = []

        # start a thread to get status
        self.start_thread()

        # initialize db
        self._database = DataBase()

    @Route(methods="get", resource="/system/status/cpu")
    def get_cpu(self, message, response):
        print "in get cpu callback!!!"

        cpu_cnt = self._database.get_table_count("cpu")

        data_obj = self._database.get_table_data("cpu")

        return_data = self.parse_return_data(data_obj, cpu_cnt)

        return response(data=return_data)

    @Route(methods="get", resource="/system/status/memory")
    def get_memory(self, message, response):
        print "in get memory callback!!!"
        # if "push" in message.query:
        #     if message.query["push"] == "true":
        #         self.model.db["memoryPush"] = 1
        #         self.model.save_db()

        #         # start thread
        #         rc = self.start_thread("memory")
        #         if rc is True:
        #             return response(data=self.model.db)
        #         else:
        #             return response(code=400,
        #                             data={"message": "server push failed"})

        # push query is false, return db
        # return response(data=self.model.db)

    @Route(methods="get", resource="/system/status/disk")
    def get_disk(self, message, response):
        print "in get disk callback!!!"
        # if "push" in message.query:
        #     if message.query["push"] == "true":
        #         self.model.db["diskPush"] = 1
        #         self.model.save_db()

        #         # start thread
        #         rc = self.start_thread("disk")
        #         if rc is True:
        #             return response(data=self.model.db)
        #         else:
        #             return response(code=400,
        #                             data={"message": "server push failed"})
        # # push query is false, return db
        # return response(data=self.model.db)

    @Route(methods="get", resource="/system/status/showdata")
    def get_system_data(self, message, response):
        # Tcall SystemStatus class to get data
        return response(data=SystemData().showdata())

    @Route(methods="put", resource="/system/status/showdata")
    def put_system_data(self, message, response):
        if not(hasattr(message, "data")):
            return response(code=400, data={"message": "Invaild Input"})
        self.model.db["hostname"] = message.data["hostname"]
        self.model.save_db()
        # setup hostname
        rc = SystemData.set_hostname(message.data["hostname"])
        if rc is True:
            return response(data=self.model.db)
        else:
            return response(code=400, data={"message":
                                            "Set hostname error"})

    def start_thread(self):
        try:
            kill_rc = self.kill_thread()
            if kill_rc is False:
                return False

            # start thread to grep status
            t = GrepThread()
            t.start()

            # save to thread pool
            self.thread_pool.append((t))
            logger.debug("start thread pool: %s" % self.thread_pool)
            return True

        except Exception as e:
            logger.debug("start thread error: %s" % e)
            return False

    def kill_thread(self):
        try:
            # kill thread from thread pool
            for idx, value in enumerate(self.thread_pool):
                logger.debug("kill %s thread id:%s" % (value[0], value[1]))
                value[1].join()

                # pop thread_id in thread pool
                self.thread_pool.pop(idx)
            return True
        except Exception as e:
            logger.debug("kill thread error: %s" % e)
            return False

    def parse_return_data(self, data_obj, data_cnt):
        data = []
        print data_cnt
        # fetch newest MAX_RETURN_CNT data
        if data_cnt >= Status.MAX_RETURN_CNT:
            for item in data_obj[(
                    data_cnt-Status.MAX_RETURN_CNT):(data_cnt)]:

                data.append({
                    "time": item.time,
                    "value": item.usage
                })
        else:
            for item in data_obj:
                data.append({
                    "time": item.time,
                    "value": item.usage
                })
        return data


class ConvertData:
    # convert size
    @staticmethod
    def human_size(size_bytes):
        if size_bytes == 0:
            return "0 Byte"
        suffixes_table = [("bytes", 0), ("KB", 0), ("MB", 1), ("GB", 2)]
        num = float(size_bytes)
        for suffix, percision in suffixes_table:
            if num < 1024.0:
                break
            num /= 1024.0

        # convert to correct percision
        if percision == 0:
            formatted_size = ("%d" % num)
        else:
            formatted_size = str(round(num, ndigits=percision))
        return "%s %s" % (formatted_size, suffix)

    @staticmethod
    def get_time():
        current_time = time.strftime("%Y/%m/%d %H:%M:%S",
                                     time.localtime(time.time()))
        return current_time


class DataBase:

    Base = declarative_base()

    # define cpu status table
    class CpuStatus(Base):
        __tablename__ = "cpu"

        id = Column(Integer, primary_key=True)
        time = Column(String, nullable=False)
        usage = Column(Float, nullable=False)
        time_stamp = Column(Float, nullable=False)

        def __init__(self, intime, usage):
            self.time = intime
            self.usage = usage
            self.time_stamp = time.time()

    # define memory status table
    class MemoryStatus(Base):
        __tablename__ = "memory"

        id = Column(Integer, primary_key=True)
        time = Column(String, nullable=False)
        usedPercentage = Column(Integer, nullable=False)
        total = Column(String, nullable=False)
        free = Column(String, nullable=False)
        used = Column(String, nullable=False)
        time_stamp = Column(Float, nullable=False)

        def __init__(self, intime, usedPercentage, total, free, used):
            self.time = intime
            self.usedPercentage = usedPercentage
            self.total = total
            self.free = free
            self.used = used
            self.time_stamp = time.time()

    # difine disk usage status table

    def __init__(self):

        create_db_flag = 0

        # check db file exist or not, if not, create a new file
        if not os.path.isfile(DB_PATH):
            open(DB_PATH, "a").close()
            create_db_flag = 1
            print("open new file")

        # prepare instance
        self._engine = create_engine("sqlite:///" + DB_PATH)

        # # prepare lock
        # self._lock = Flock(db_path + ".lock")

        # prepare session for communicate with db
        self._session = sessionmaker(bind=self._engine)()

        # create db
        if create_db_flag == 1:
            self._create_db()

    def _create_db(self):
        with global_lock:
            logger.debug("create db")

            # delete all tables
            DataBase.Base.metadata.drop_all(self._engine)

            # create tables
            DataBase.Base.metadata.create_all(self._engine)

    def insert_table(self, table_type, data):
        with global_lock:
            if table_type == "cpu":
                self._session.add(DataBase.CpuStatus(
                    intime=data["time"],
                    usage=data["usage"]
                ))
            elif table_type == "memory":
                self._session.add(DataBase.MemoryStatus(
                    intime=data["time"],
                    usedPercentage=data["usedPercentage"],
                    total=data["total"],
                    free=data["free"],
                    used=data["used"]
                ))

            self._session.commit()

    def delete_table(self, table_type):
        with global_lock:
            if table_type == "cpu":
                del_obj = self._session.query(DataBase.CpuStatus).order_by(asc(
                    DataBase.CpuStatus.id))[0]

                # delete data by del_obj.id
                self._session.query(DataBase.CpuStatus).filter_by(
                    id=(del_obj.id)).delete()

    def get_table_data(self, table_name):
        with global_lock:
            if table_name == "cpu":
                return self._session.query(DataBase.CpuStatus).all()
            elif table_name == "memory":
                return self._session.query(DataBase.CpuStatus).all()

    def get_table_count(self, table_name):
        with global_lock:
            if table_name == "cpu":
                return self._session.query(
                    func.count(DataBase.CpuStatus.id)
                    ).one()[0]
            elif table_name == "memeory":
                return self._session.query(
                    func.count(DataBase.MemoryStatus.id)
                    ).one()[0]

    def check_table_count(self, table_name):
        """
        check table count is equal to max_table_cnt or not,
        if equal, return True, else return false
        """
        MAX_TABLE_CNT = 10

        # get_table_count
        with global_lock:
            if table_name == "cpu":
                cpu_cnt = self._session.query(
                    func.count(DataBase.CpuStatus.id)
                    ).one()[0]

                if cpu_cnt >= MAX_TABLE_CNT:
                    return True
                return False

            elif table_name == "memory":
                memory_cnt = self._session.query(
                    func.count(DataBase.MemoryStatus.id)
                    ).one()[0]

                if memory_cnt >= MAX_TABLE_CNT:
                    return True
                return False


class GrepThread(threading.Thread):

    # routine to get status info, and save to db
    # db_path = "./status_db"

    def __init__(self):
        super(GrepThread, self).__init__()
        self.stoprequest = threading.Event()

        # initialize db
        self._database = DataBase()

    def run(self):
        logger.debug("run GrepThread")
        grep_interval = 5
        cnt = 5
        while not self.stoprequest.isSet():
            if cnt == grep_interval:

                cpu_data = self.get_cpu_data()
                logger.debug("cpu_data:%s" % cpu_data)
                print time.time()

                # TODO: check db count is equal to max count or not
                if self._database.check_table_count("cpu"):
                    print "delete old data!!!!"
                    self._database.delete_table("cpu")

                self._database.insert_table("cpu", cpu_data)

                memory_data = self.get_memory_data()
                logger.debug("memory_data:%s" % memory_data)

                self._database.insert_table("memory", memory_data)

                disk_data = self.get_disk_data()
                logger.debug("disk_data:%s" % disk_data)

                cnt = 0
            cnt = cnt + 1
            time.sleep(1)

    def join(self):
        logger.debug("join GrepThread")

        # set event to stop while loop in run
        self.stoprequest.set()
        super(GrepThread, self).join()
        logger.debug("join finished")

    def get_cpu_data(self):
        data = {"time": ConvertData.get_time(),
                "usage": psutil.cpu_percent(interval=1)}
        return data

    def get_memory_data(self):
        mem = psutil.virtual_memory()
        data = {"time": ConvertData.get_time(),
                "total": ConvertData.human_size(mem.total),
                "used": ConvertData.human_size(mem.used),
                "free": ConvertData.human_size(mem.free),
                "usedPercentage": round(((float(mem.used)/mem.total)*100),
                                        ndigits=1)}
        return data

    def get_disk_data(self):
        disk = psutil.disk_usage("/")
        data = {"time": ConvertData.get_time(),
                "total": ConvertData.human_size(disk.total),
                "used": ConvertData.human_size(disk.used),
                "free": ConvertData.human_size(disk.free),
                "usedPercentage": disk.percent}
        return data


class SystemData:

    def __init__(self, *args, **kwargs):
        self.attribute = dict()
        self.threads = list()
        for item in ["firmware", "hostname", "storage", "uptime"]:
            def run(item):
                self.attribute[item] = getattr(SystemData, "get_" + item)()

            thread = Thread(target=run, args=[item])
            self.threads.append(thread)

        map((lambda thread: thread.start()), self.threads)
        map((lambda thread: thread.join()), self.threads)

    @staticmethod
    def get_firmware():
        cmd = "kversion -a"
        try:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            out = process.communicate()[0]
        except Exception as e:
            logger.debug("get firmware version error: %s" % e)
            return "N/A"
        return out

    @staticmethod
    def get_hostname():
        return socket.gethostname()

    @staticmethod
    def get_storage():
        disk = psutil.disk_usage("/")
        return ConvertData.human_size(disk.free)

    @staticmethod
    def get_uptime(format=True):
        uptime_string = None
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_string = str(timedelta(seconds=uptime_seconds))
            return uptime_string[:uptime_string.find('.')]

    @staticmethod
    def set_hostname(name):
        rc = subprocess.call("hostname -b %s" % name, shell=True)
        return True if rc == 0 else False

    def showdata(self):
        return self.attribute


if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=0, format=FORMAT)
    logger = logging.getLogger("ssh")

    status = Status(connection=Mqtt())
    status.start()
