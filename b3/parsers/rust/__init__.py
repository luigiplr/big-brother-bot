
__author__ = 'Luigi'
__version__ = '1.0.0'


import b3
import b3.events
import re
import string

from b3.parsers.q3a.abstractParser import AbstractParser
from b3.parsers.rust.rcon import Rcon
from threading import Timer

class RustParser(AbstractParser):

    gameName = 'rust'
    OutputClass = Rcon
    
    _logSync = 3                                             # Value for unbuffered game logging (append mode)
    _counter = {}

    _line_color_prefix = ''

    _commands = {
        'message': 'tell %(cid)s %(message)s',
        'say': 'say %(message)s',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'clientkick %(cid)s',
        'ban': 'banclient %(cid)s',
        'unban': 'unbanuser %(name)s',
        'tempban': 'clientkick %(cid)s'
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')

    _lineFormats = (
        # Joined / Discsonnected events
        re.compile(
            r'^(?P<ip>\d+\.\d+\.\d+\.\d+)\:\d+\/(?P<steamid>\d+)\/(?P<name>\w+) (?P<type>joined|disconnecting)(\:|) (?P<reason>.*)$'
            , re.IGNORECASE),

        # Killed event
        re.compile(
            r'^(?P<name>\w+)\[(?P<extra>\d+)\/(?P<steamid>\d+)\] was killed by (?P<reason>.*)$'
            , re.IGNORECASE)

    )

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def startup(self):
        """
        Called after the parser is created before run().
        """
        self.warning(self.config)
        if not self.config.has_option('server','game_log'):
            self.critical("Your main config file is missing the 'game_log' setting in section 'server'")
            raise SystemExit(220)

        self.debug('Parser started')

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def OnSay(self, action, data, match=None):
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            client = self.getClient(match)
            if not client:
                return None

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        # decode the server data
        if self.encoding:
            try:
                data = data.decode(self.encoding)
            except Exception, msg:
                self.warning('ERROR: decoding data: %r', msg)

        if client.name != match.group('name'):
            client.name = match.group('name')

        return self.getEvent('EVT_CLIENT_SAY', data=data, client=client)


    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################



    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Unban a client.
        :param client: The client to unban
        :param reason: The reason for the unban
        :param admin: The admin who unbanned this client
        :param silent: Whether or not to announce this unban
        """
        name = self.stripColors(client.exactName)
        result = self.write(self.getCommand('unban', name=name, reason=reason))
        if admin:
            admin.message(result)

    def sync(self):
        """
        For all connected players returned by self.get_player_list(), get the matching Client
        object from self.clients (with self.clients.get_by_cid(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        """
        self.debug('synchronising clients...')
        plist = self.getPlayerList(maxRetries=4)
        mlist = {}

        return mlist

    def authorizeClients(self):
        self.debug('authing clients...')


#--LogLineFormats---------------------------------------------------------------

#===============================================================================
#
# *** RUST:
# Join:                 Platform assembly: C:\Users\Luigi\Downloads\Rust_Server\Server\rustds\RustDedicated_Data\Managed\System.Data.dll (this message is harmless)
#                       127.0.0.1:62056/76561198282334064/luigiplr joined [windows/76561198282334064]

# Quit:                 127.0.0.1:62056/76561198282334064/luigiplr disconnecting: closing

# Kill:                 luigiplr[8220/76561198282334064] was killed by Suicide

# Say to All:           [CHAT] luigiplr[8220/76561198282334064] : testing
#===============================================================================
