#!/usr/bin/python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------------
# SourceRcon - Python class for executing commands on RUST Dedicated Servers
# Copyright (c) 2016 Luigi Poole
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#------------------------------------------------------------------------------

"""http://developer.valvesoftware.com/wiki/Source_RCON_Protocol"""

import select
import socket
import struct

SERVERDATA_AUTH = 1
SERVERDATA_AUTH_TYPE = 3

SERVERDATA_EXECCOMMAND = 0xa7
SERVERDATA_EXECCOMMAND_TYPE = 2

MAX_PACKET_SIZE = 4096 * 1024
MAX_INT = 0xffffffff


class SourceRconError(Exception):
    pass


class RustRcon(object):
    """Example usage:

       import SourceRcon
       server = SourceRcon.SourceRcon('1.2.3.4', 27015, 'secret')
       print server.rcon('cvarlist')
    """

    def __init__(self, host, port=27015, password='', timeout=1.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.tcp = False
        self.buf = ''
        self.authed = False

    def disconnect(self):
        """Disconnect from the server."""
        if self.tcp:
            self.tcp.close()

    def connect(self):
        """Connect to the server. Should only be used internally."""
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.settimeout(self.timeout)
        self.tcp.connect((self.host, self.port))

    def send(self, cmd, type, message=None):
        """Send command and message to the server. Should only be used internally."""
        if message is None:
            message = ''
        pkt = struct.pack('II', cmd, type) + message + "\0\0"
        self.tcp.send(struct.pack('I', len(pkt)) + pkt)

    def receive(self):
        if self.buf is '':
            self.buf = self.tcp.recv(MAX_PACKET_SIZE)
        # Pop the message length from the buffer
        msg_len = struct.unpack('I', self.buf[:4])[0]
        self.buf = self.buf[4:]
        while len(self.buf) < msg_len:
            self.buf = self.buf + self.tcp.recv(MAX_PACKET_SIZE)
        # Pop the message from the buffer
        ret_buf, self.buf = self.buf[:msg_len - 2], self.buf[msg_len:]
        return ret_buf

    def recv_data(self):
        data = self.receive()
        (id, type), msg = struct.unpack('II', data[:8]), data[8:]
        if msg == '':
            msg = None
        # Is the data a log message
        if (id, type) == (0, 4):
            return self.recv_data()
        elif (id, type) == (MAX_INT, 0):
            return self.recv_data()
        else:
            return id, type, msg

    def auth(self):
        self.send(SERVERDATA_AUTH, SERVERDATA_AUTH_TYPE, self.password)
        # expect (1, 0). This seems to be an ACK
        self.recv_data()
        # Authentication response now comes through
        id, type, msg = self.recv_data()
        if id == MAX_INT:
            return False
        elif id == SERVERDATA_AUTH:
            self.authed = True
            return True
        else:
            raise SourceRconError('RCON authentication failure: %s' % (repr(id, type, msg)))

    def rcon(self, command):
        """Send RCON command to the server. Connect and auth if necessary,
           handle dropped connections, send command and return reply."""
        # special treatment for sending whole scripts
        if '\n' in command:
            commands = command.split('\n')

            def f(x): y = x.strip()
            return len(y) and not y.startswith("//")
            commands = filter(f, commands)
            results = map(self.rcon, commands)
            return "".join(results)

        if self.authed is not True:
            self.disconnect()
            self.connect()
            self.auth()

        self.send(SERVERDATA_EXECCOMMAND, SERVERDATA_EXECCOMMAND_TYPE, command)
        id, type, message = self.recv_data()
        return message
