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
            r'(?P<ip>\d+\.\d+\.\d+\.\d+)\:\d+\/(?P<steamid>\d+)\/(?P<name>\w+) (?P<type>joined|disconnecting)(\:|) (?P<reason>.*)'
            , re.IGNORECASE),

        # Killed event: luigiplr[8220/76561198282334064] was killed by Suicide
        re.compile(
            r'(?P<name>\w+)\[(?P<extra>\d+)\/(?P<steamid>\d+)\] was (?P<action>killed) by (?P<reason>.*)'
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
    	self.debug(action)



    def OnKilled(self, name, steamid, reason, match=None):
    	self.debug((name, steamid, reason))

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
