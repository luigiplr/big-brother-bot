from threading import Event, Lock
from socket import timeout
from Queue import Queue
from b3.lib.rustlib.RustRcon import RustRcon, SERVERDATA_EXECCOMMAND, SERVERDATA_EXECCOMMAND_TYPE, SERVERDATA_AUTH, SERVERDATA_AUTH_TYPE, SourceRconError

__version__ = ''
__author__ = ''



class Rcon(object):
    """
    Facade to expose the SourceRcon class with an API as expected by B3 parsers
    """
    lock = Lock()

    def __init__(self, console, host, password):
        self.console = console
        self.host, self.port = host
        self.password = password
        self.timeout = 1.0
        self.queue = Queue()
        self.stop_event = Event()
        self.server = RustRcon(self.host, self.port, self.password, self.timeout)

        self.console.info("RCON: connecting to Source game server")
        try:
            self.server.connect()
        except timeout, err:
            self.console.error("RCON: timeout error while trying to connect to game server at %s:%s. "
                               "Make sure the rcon_ip and port are correct and that the game server is "
                               "running" % (self.host, self.port))


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
                raw_data = self.server.rcon(self.encode_data(cmd))
                if raw_data:
                    data = raw_data.decode('UTF-8', 'replace')
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
                self.console.info("RCON disconnecting from Source game server")
                self.server.disconnect()
                self.console.verbose("RCON disconnected from Source game server")
            finally:
                self.server = None
                del self.server


    ########################################################
    #
    #   others
    #
    ########################################################

    def _writelines(self):
        while not self.stop_event.isSet():
            lines = self.queue.get(True)
            for cmd in lines:
                if not cmd:
                    continue
                with self.lock:
                    self.rconNoWait(cmd)


    def rconNoWait(self, cmd):
        """
        send a single command, do not wait for any response.
        connect and auth if necessary.
        """
        if self.server.authed is not True:
            self.server.disconnect()
            self.server.connect()
            self.server.auth()

        self.server.send(SERVERDATA_EXECCOMMAND, SERVERDATA_EXECCOMMAND_TYPE, self.encode_data(cmd))


    def encode_data(self, data):
        if not data:
            return data
        if type(data) is unicode:
            return data.encode('UTF-8')
        else:
            return data