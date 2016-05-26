from threading import Event, Lock
from socket import timeout
import re, struct, socket, Queue

__version__ = 'Luigi'
__author__ = '0.0.1'




class Rcon(object):
    """
    Facade to expose the SourceRcon class with an API as expected by B3 parsers
    """
    lock = Lock()

    MAX_PACKET_SIZE=4096*1024
    MAX_INT=0xffffffff
    TYPE_RESPONSE=0
    TYPE_COMMAND=2
    TYPE_PASSWORD=3
    ID_PASSWORD=1
    ID_RCON_COMMAND=0xa7
    buf=''

    def __init__(self, console, host, password):
        self.console = console
        self.host, self.port = host
        self.password = password
        self.timeout = 1.0
        self.queue = Queue.Queue()
        self.stop_event = Event()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.console.info("RCON: connecting to RUST game server")

        if not self.connect():
            self.console.error("RCON: timeout error while trying to connect to game server at %s:%s. "
                               "Make sure the rcon_ip and port are correct and that the game server is "
                               "running" % (self.host, self.port))
        elif self.send_auth():
            self.console.error("RCON: Authentication failed")
            self.disconnect()
        else:
            self.console.info("RCON: Authentication successful")



    ########################################################
    #
    #   expected B3 Rcon API
    #
    ########################################################

    def writelines(self, lines):
        """
        Sends multiple rcon commands and do not wait for responses (non blocking)
        """
        self.queue.put(lines)


    def write(self, cmd, *args, **kwargs):
        """
        Sends a rcon command and return the response (blocking until timeout)
        """
        with Rcon.lock:
            try:
                self.console.info("RCON SEND: %s" % cmd)
                self.send_data(self.ID_RCON_COMMAND, self.TYPE_COMMAND, self.encode_data(cmd));
                # Receive connection status
                id, type, msg = self.recv_data()
                if (id, type) != (self.ID_RCON_COMMAND, self.TYPE_RESPONSE):
                    print "(%d %d)"%(id, type)
                    print msg
                if msg:
                    data = msg.decode('UTF-8', 'replace')
                    self.console.info("RCON RECEIVED: %s" % data)
                    return data
            except timeout:
                self.console.error("RCON: timeout error while trying to connect to game server at %s:%s. "
                                   "Make sure the rcon_ip and port are correct and that the game server is "
                                   "running" % (self.host, self.port))


    def flush(self):
        pass


    def close(self):
        if self.server:
            try:
                self.console.info("RCON disconnecting from RUST game server")
                self.disconnect()
                self.console.verbose("RCON disconnected from RUST game server")
            finally:
                self.server = None
                del self.server


    ########################################################
    #
    #   others
    #
    ########################################################


    def recv(self):
        if self.buf is '':
            self.buf = self.socket.recv(self.MAX_PACKET_SIZE)
        # Pop the message length from the buffer
        msg_len = struct.unpack('I', self.buf[:4])[0]
        self.buf = self.buf[4:]
        while len(self.buf) < msg_len:
            self.buf = self.buf + self.socket.recv(self.MAX_PACKET_SIZE)
        # Pop the message from the buffer
        ret_buf, self.buf = self.buf[:msg_len - 2], self.buf[msg_len:]
        return ret_buf

    def recv_data(self):
        data = self.recv()
        (id, type), msg = struct.unpack('II', data[:8]), data[8:]
        if msg == '':
            msg = None
        # Is the data a log message
        if (id, type) == (0, 4):
            return self.recv_data()
        elif (id, type) == (self.MAX_INT, 0):
            return self.recv_data() 
        else:
            return id, type, msg

    def send_data(self, id, type, payload=None):
        if payload is None:
            payload = ''
        pkt = struct.pack('II', id, type) + payload + "\0\0"
        pkt = struct.pack('I', len(pkt)) + pkt
        self.send(pkt)

    def send_auth(self):
        self.send_data(self.ID_PASSWORD, self.TYPE_PASSWORD, self.password)
        # expect (1, 0). This seems to be an ACK
        id, type, _ = self.recv_data()
        # Authentication response now comes through
        id, type, _ = self.recv_data()
        if id == self.MAX_INT:
            return -1
        elif id == self.ID_PASSWORD:
            return 0
        else:
            return -1        

    def send(self, message):
        self.socket.send(message)

    def encode_data(self, data):
        if not data:
            return data
        if type(data) is unicode:
            return data.encode('UTF-8')
        else:
            return data

    def disconnect(self):
        rekt = self.socket.close()
        print "Disconnected from RCON"
        return rekt

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            return False