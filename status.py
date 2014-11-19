#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import os
import threading
import time
from sanji.core import Sanji
from sanji.core import Route
from sanji.model_initiator import ModelInitiator
from sanji.connection.mqtt import Mqtt

logger = logging.getLogger()


class Status(Sanji):

    def init(self, *args, **kwargs):
        path_root = os.path.abspath(os.path.dirname(__file__))
        self.model = ModelInitiator("status", path_root, backup_interval=1)

        # reset flag
        self.model.db["cpuPush"] = 0
        self.model.db["memoryPush"] = 0
        self.model.db["diskPush"] = 0
        self.model.save_db()

        # init thread pool 
        self.cpu_thread_pool = []
        self.memory_thread_pool = []
        self.disk_thread_pool = []

    @Route(methods="get", resource="/system/status/cpu")
    def get_cpu(self, message, response):
        if "push" in message.query:
            if message.query["push"] == "true":
                self.model.db["cpuPush"] = 1
                self.model.save_db()

                rc = self.start_cpu_thread()
                if rc is True:
                    # response 200
                    print "response 200"
                else:
                    # response 400
                    print "response 400"

        # TODO: server push once
        print("message.query: %s" % message.query["push"])
        # return response(data={"enable": self.model.db["enable"]})

    '''
    @Route(methods="put", resource="/system/status/cpu")
    def put_cpu(self, message, response):
        if hasattr(message, "data") and "enable" in message.data:
            self.model.db["enable"] = message.data["enable"]
            self.model.save_db()
            self.update_ssh()
            return response(code=self.rsp["code"], data=self.rsp["data"])
        return response(code=400, data={"message": "Invaild Input"})

    @Route(methods="get", resource="/system/status/memory")
    def get_memory(self, message, response):
        return response(data={"enable": self.model.db["enable"]})

    @Route(methods="put", resource="/system/status/memory")
    def put_memory(self, message, response):
        if hasattr(message, "data") and "enable" in message.data:
            self.model.db["enable"] = message.data["enable"]
            self.model.save_db()
            self.update_ssh()
            return response(code=self.rsp["code"], data=self.rsp["data"])
        return response(code=400, data={"message": "Invaild Input"})

    @Route(methods="get", resource="/system/status/disk")
    def get_disk(self, message, response):
        return response(data={"enable": self.model.db["enable"]})

    @Route(methods="put", resource="/system/status/disk")
    def put_disk(self, message, response):
        if hasattr(message, "data") and "enable" in message.data:
            self.model.db["enable"] = message.data["enable"]
            self.model.save_db()
            self.update_ssh()
            return response(code=self.rsp["code"], data=self.rsp["data"])
        return response(code=400, data={"message": "Invaild Input"})
    '''

    def start_cpu_thread(self):
        kill_rc = self.kill_cpu_thread()
        if kill_rc is False:
            return False
        # start call thread to server push
        t = CpuThread()
        t.start()
        # save to thread pool
        self.cpu_thread_pool.append(t)
        print("start_cpu_thread thread pool: %s" % self.cpu_thread_pool)
        time.sleep(20)
        self.kill_cpu_thread()
        return True

    def kill_cpu_thread(self):
        try:
        # kill thread from thread pool
            print("in kill cpu thread: thread pool:%s" % self.cpu_thread_pool)
            for thread in self.cpu_thread_pool:
                print ("start to kill thread:%s" % thread)
                thread.join()
                print ("end to kill thread:%s" % thread)
            # flush thread pool
            self.cpu_thread_pool = []
            return True
        except Exception as e:
            logger.debug("kill thread error: %s" % e)
            return False

    def push_memory_data(self, enable):
        pass

    def push_disk_data(self, enable):
        pass


class CpuThread(threading.Thread):

    def run(self):
        print "in CpuThread run"

    def join(self):
        print "in CpuThread join"

if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=0, format=FORMAT)
    logger = logging.getLogger("ssh")

    status = Status(connection=Mqtt())
    status.start()
