"""
DEBUG MCPROXY COMMANDS 
Activated with --debug command line switch
"""

from modules import Command, Hook, colors
from conf import settings

#----------------- Commands ------------------

class PacketDump(Command):
    """
    syntax: dump [on|off]
    If no on|off state is specified the packet dumping state will be toggled
    """
    alias = "dump"
    #requires_hooks = ['ProtoLog']
    
    def run(self, state=None):
            if state:
                try:
                    self.session.debug.packet_dump = {"on":True, "off":False}[args[0].lower()]
                except KeyError:
                    self.chat("please set on or off")
            else:
                self.session.packet_dump = not self.session.debug.packet_dump
            self.chat("Packet Dumping is %s" % {True:"ON", False:"OFF"}[self.session.debug.packet_dump])

class PacketFilter(Command):
    """
    syntax: filter [on|off]
    If no on|off state is specified the packet filter state will be toggled
    """
    alias = "filter"
    
    def run(self, state=None):
            if state:
                try:
                    self.session.debug.dump_packets = {"on":True, "off":False}[state.lower()]
                except KeyError:
                    self.chat("please set 'on' or 'off'")
            else:
                self.session.debug.filter = not self.session.debug.filter
            self.chat("Packet Filtering is %s" % {True:"ON", False:"OFF"}[self.session.debug.filter])

class HexDump(Command):
    """
    syntax: hexdump [on|off]
    If no on|off state is specified the packet filter state will be toggled
    """
    alias = "hexdump"
    
    def run(self, state=None):
            if state:
                try:
                    self.session.debug.hex_dump = {"on":True, "off":False}[state.lower()]
                except KeyError:
                    self.chat("please set 'on' or 'off'")
            else:
                self.session.debug.hex_dump = not self.session.debug.hex_dump
            self.chat("Hex Dumping is %s" % {True:"ON", False:"OFF"}[self.session.debug.hex_dump])