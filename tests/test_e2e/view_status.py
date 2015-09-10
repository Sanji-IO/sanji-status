#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
from time import sleep

from sanji.core import Sanji
from sanji.connection.mqtt import Mqtt


REQ_RESOURCE = "/system/status"
MANUAL_TEST = 0


class View(Sanji):

    # This function will be executed after registered.
    def run(self):

        for count in xrange(0, 100, 1):
            # Normal CRUD Operation
            #   self.publish.[get, put, delete, post](...)
            # One-to-One Messaging
            #   self.publish.direct.[get, put, delete, post](...)
            #   (if block=True return Message, else return mqtt mid number)
            # Agruments
            #   (resource[, data=None, block=True, timeout=60])

            # case 1: test GET collection
            sleep(2)
            resource = REQ_RESOURCE
            print "GET %s" % resource
            res = self.publish.get(resource)
            if res.code != 200:
                print "GET is supported, should be code 200"
                print res.to_json()
                self.stop()
            if 1 == MANUAL_TEST:
                print res.to_json()
                var = raw_input("Please enter any key to continue...")

            # case 2: test PUT with no data attribute
            sleep(2)
            print "PUT %s" % REQ_RESOURCE
            res = self.publish.put(REQ_RESOURCE, None)
            if res.code != 400:
                print "data is required, code 400 is expected"
                print res.to_json()
                self.stop()
            if 1 == MANUAL_TEST:
                var = raw_input("Please enter any key to continue...")

            # case 3: test PUT with empty data
            sleep(2)
            print "PUT %s" % REQ_RESOURCE
            res = self.publish.put(REQ_RESOURCE, data={})
            if res.code != 500:
                print "data.enable is required, code 500 is expected"
                print res.to_json()
                self.stop()
            if 1 == MANUAL_TEST:
                var = raw_input("Please enter any key to continue...")

            # case 4: test PUT with hostname
            sleep(2)
            data = {"hostname": "test"}
            resource = REQ_RESOURCE
            print "PUT %s" % resource
            res = self.publish.put(resource, data=data)
            if res.code != 200:
                print "data.hostname=\"test\" should reply code 200"
                print res.to_json()
                self.stop()
            print data
            if 1 == MANUAL_TEST:
                print var

            # stop the test view
            self.stop()


if __name__ == "__main__":
    FORMAT = "%(asctime)s - %(levelname)s - %(lineno)s - %(message)s"
    logging.basicConfig(level=0, format=FORMAT)
    logger = logging.getLogger("Status")

    view = View(connection=Mqtt())
    view.start()
