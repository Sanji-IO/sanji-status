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
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import OperationalError
from flock import Flock

logger = logging.getLogger()

DB_PATH = "./status_db"


class Status(Sanji):

    MAX_RETURN_CNT = 500
    RETRY_TIMES = 5
    RETRY_INTERVAL = 5

    def init(self, *args, **kwargs):
        path_root = os.path.abspath(os.path.dirname(__file__))
        self.model = ModelInitiator("status", path_root, backup_interval=1)

        # init thread pool
        self.thread_pool = []

        # start a thread to get status
        self.start_thread()

    @Route(methods="get", resource="/system/status/cpu")
    def get_cpu(self, message, response):
        """
        get MAX_RETURN_CNT cpu data from cpu table and then response
        """

        cpu_database = DataBase(DB_PATH)
        retry_cnt = 0
        while retry_cnt < Status.RETRY_TIMES:
            try:
                cpu_cnt = cpu_database.get_table_count("cpu")
                data_obj = cpu_database.get_table_data("cpu")
                return_data = self.parse_cpu_return_data(data_obj, cpu_cnt)

                # close session to avoid new instance exception
                cpu_database._session.close()
                return response(data=return_data)
            except Exception as e:
                logger.warning("get_cpu exception %s" % e)
                retry_cnt = retry_cnt + 1
                time.sleep(Status.RETRY_INTERVAL)

        return response(code=400, data={"message":
                                        "get_cpu retry failed"})

    @Route(methods="get", resource="/system/status/memory")
    def get_memory(self, message, response):
        """
        get MAX_RETURN_CNT memory data from memory table and then response
        """

        memory_database = DataBase(DB_PATH)
        retry_cnt = 0

        while retry_cnt < Status.RETRY_TIMES:
            try:
                memory_cnt = memory_database.get_table_count("memory")
                data_obj = memory_database.get_table_data("memory")
                return_data = self.parse_memory_return_data(
                    data_obj,
                    memory_cnt)

                # close session to avoid new instance exception
                memory_database._session.close()
                return response(data=return_data)
            except Exception as e:
                logger.warning("get_memory exception: %s" % e)
                retry_cnt = retry_cnt + 1
                time.sleep(Status.RETRY_INTERVAL)

        return response(code=400, data={"message":
                                        "get_memory retry failed"})

    @Route(methods="get", resource="/system/status/disk")
    def get_disk(self, message, response):
        """
        get MAX_RETURN_CNT disk data from disk table and then response
        """

        disk_database = DataBase(DB_PATH)
        retry_cnt = 0

        while retry_cnt < Status.RETRY_TIMES:
            try:
                disk_cnt = disk_database.get_table_count("disk")
                data_obj = disk_database.get_table_data("disk")
                return_data = self.parse_disk_return_data(data_obj, disk_cnt)

                # close session to avoid new instance exception
                disk_database._session.close()
                return response(data=return_data)
            except Exception as e:
                logger.warning("get disk exception: %s" % e)
                retry_cnt = retry_cnt + 1
                time.sleep(Status.RETRY_INTERVAL)

        return response(code=400, data={"message":
                                        "get_disk retry failed"})

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
                logger.debug("kill thread id:%s" % value)
                value.join()

                # pop thread_id in thread pool
                self.thread_pool.pop(idx)
            return True
        except Exception as e:
            logger.debug("kill thread error: %s" % e)
            return False

    def parse_cpu_return_data(self, data_obj, data_cnt):
        data = []

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

    def parse_memory_return_data(self, data_obj, data_cnt):
        data = []

        # fetch newest MAX_RETURN_CNT data
        if data_cnt >= Status.MAX_RETURN_CNT:
            for item in data_obj[(
                    data_cnt-Status.MAX_RETURN_CNT):(data_cnt)]:

                data.append({
                    "time": item.time,
                    "total": item.total,
                    "used": item.used,
                    "free": item.free,
                    "usedPercentage": item.usedPercentage
                })
        else:
            for item in data_obj:
                data.append({
                    "time": item.time,
                    "total": item.total,
                    "used": item.used,
                    "free": item.free,
                    "usedPercentage": item.usedPercentage
                })
        return data

    def parse_disk_return_data(self, data_obj, data_cnt):
        data = []

        # fetch newest MAX_RETURN_CNT data
        if data_cnt >= Status.MAX_RETURN_CNT:
            for item in data_obj[(
                    data_cnt-Status.MAX_RETURN_CNT):(data_cnt)]:

                data.append({
                    "time": item.time,
                    "total": item.total,
                    "used": item.used,
                    "free": item.free,
                    "usedPercentage": item.usedPercentage
                })
        else:
            for item in data_obj:
                data.append({
                    "time": item.time,
                    "total": item.total,
                    "used": item.used,
                    "free": item.free,
                    "usedPercentage": item.usedPercentage
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
    MAX_TABLE_CNT = 5000

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
    class DiskStatus(Base):
        __tablename__ = "disk"

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

    def __init__(self, db_path):

        # prepare lock
        self._global_lock = Flock(db_path + ".lock")

        # prepare instance
        self._engine = create_engine("sqlite:///" + db_path)

        # prepare session for communicate with db
        self._session = sessionmaker(bind=self._engine)()

        # check db file exist or not, if not, create db
        try:
            self.get_table_count("cpu")
            self.get_table_count("memory")
            self.get_table_count("disk")
        except (IndexError, NoResultFound, OperationalError):
            self._create_db()
        finally:
            self._session.close()

    def _create_db(self):
        with self._global_lock:
            logger.debug("create db")

            # delete all tables
            DataBase.Base.metadata.drop_all(self._engine)

            # create tables
            DataBase.Base.metadata.create_all(self._engine)

    def insert_table(self, table_type, data):
        with self._global_lock:
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
            elif table_type == "disk":
                self._session.add(DataBase.DiskStatus(
                    intime=data["time"],
                    usedPercentage=data["usedPercentage"],
                    total=data["total"],
                    free=data["free"],
                    used=data["used"]
                ))
            else:
                logger.warning("insert_table table_type error")

            self._session.commit()

    def delete_table(self, table_type):
        with self._global_lock:

            if table_type == "cpu":
                del_obj = self._session.query(DataBase.CpuStatus).order_by(asc(
                    DataBase.CpuStatus.id))[0]

                # delete data by del_obj.id
                self._session.query(DataBase.CpuStatus).filter_by(
                    id=(del_obj.id)).delete()
            elif table_type == "memory":
                del_obj = self._session.query(DataBase.MemoryStatus).order_by(
                    asc(DataBase.MemoryStatus.id))[0]

                # delete data by del_obj.id
                self._session.query(DataBase.MemoryStatus).filter_by(
                    id=(del_obj.id)).delete()
            elif table_type == "disk":
                del_obj = self._session.query(DataBase.DiskStatus).order_by(
                    asc(DataBase.DiskStatus.id))[0]

                # delete data by del_obj.id
                self._session.query(DataBase.DiskStatus).filter_by(
                    id=(del_obj.id)).delete()
            else:
                logger.warning("delete table table_type error")

    def get_table_data(self, table_name):
        with self._global_lock:

            if table_name == "cpu":
                return self._session.query(DataBase.CpuStatus).all()
            elif table_name == "memory":
                return self._session.query(DataBase.MemoryStatus).all()
            elif table_name == "disk":
                return self._session.query(DataBase.DiskStatus).all()

    def get_table_count(self, table_name):
        with self._global_lock:

            if table_name == "cpu":
                return self._session.query(
                    func.count(DataBase.CpuStatus.id)
                    ).one()[0]
            elif table_name == "memory":
                return self._session.query(
                    func.count(DataBase.MemoryStatus.id)
                    ).one()[0]
            elif table_name == "disk":
                return self._session.query(
                    func.count(DataBase.DiskStatus.id)
                    ).one()[0]

    def check_table_count(self, table_name):
        """
        check table count is equal to max_table_cnt or not,
        if equal, return True, else return false
        """
        with self._global_lock:
            if table_name == "cpu":
                cpu_cnt = self._session.query(
                    func.count(DataBase.CpuStatus.id)
                    ).one()[0]

                if cpu_cnt >= DataBase.MAX_TABLE_CNT:
                    return True
                return False

            elif table_name == "memory":
                memory_cnt = self._session.query(
                    func.count(DataBase.MemoryStatus.id)
                    ).one()[0]

                if memory_cnt >= DataBase.MAX_TABLE_CNT:
                    return True
                return False

            elif table_name == "disk":
                disk_cnt = self._session.query(
                    func.count(DataBase.DiskStatus.id)
                    ).one()[0]

                if disk_cnt >= DataBase.MAX_TABLE_CNT:
                    return True
                return False


class GrepThread(threading.Thread):
    # routine to get status info, and save to db

    def __init__(self):
        super(GrepThread, self).__init__()
        self.stoprequest = threading.Event()

        # initialize db
        self._database = DataBase(DB_PATH)

    def run(self):
        logger.debug("run GrepThread")
        grep_interval = 60
        cnt = 60
        while not self.stoprequest.isSet():
            if cnt == grep_interval:

                cpu_data = self.get_cpu_data()
                logger.debug("cpu_data:%s" % cpu_data)

                """
                check db count is equal to max count or not,
                if equal, delete old data
                """

                if self._database.check_table_count("cpu"):
                    self._database.delete_table("cpu")

                self._database.insert_table("cpu", cpu_data)

                memory_data = self.get_memory_data()
                logger.debug("memory_data:%s" % memory_data)

                if self._database.check_table_count("memory"):
                    self._database.delete_table("memory")

                self._database.insert_table("memory", memory_data)

                disk_data = self.get_disk_data()
                logger.debug("disk_data:%s" % disk_data)

                if self._database.check_table_count("disk"):
                    self._database.delete_table("disk")

                self._database.insert_table("disk", disk_data)

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
