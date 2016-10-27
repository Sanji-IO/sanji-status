#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import socket
import string

_logger = logging.getLogger("sanji.status.collectd")


class Collectd(object):

    UNIX_SOCKET_PATH = '/var/run/collectd.sock'

    def __init__(self, path=UNIX_SOCKET_PATH):
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._path = path
        self._sock.connect(self._path)

    def __del__(self):
        self._sock.close()

    def get(self, key, flush=True):
        num = self._command('GETVAL "' + key + '"')
        lines = []
        if num:
            lines = self._readlines(num)
        if flush:
            self._command('FLUSH identifier="' + key + '"')
        return lines

    def _command(self, command):
        self._sock.send(command + '\n')
        rtn = string.split(self._readline())
        status = int(rtn[0])
        if status:
            return status

        return False

    def _readline(self):
        data = ''
        buf = []
        while data != '\n':
            data = self._sock.recv(1)
            if not data:
                break
            if data != '\n':
                buf.append(data)
        return ''.join(buf)

    def _readlines(self, lens=0):
        total = 0
        lines = []
        while True:
            line = self._readline()
            if not line:
                break
            lines.append(line)
            total = len(lines)
            if lens and total >= lens:
                break
        return lines


if __name__ == '__main__':
    c = Collectd()
