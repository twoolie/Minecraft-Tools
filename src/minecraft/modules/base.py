""" BASIC MCPROXY COMMANDS """
from modules import Command, Hook, colors
from conf import settings
import re

#----------------- Commands ------------------

class Help(Command):
    """
    syntax: help [command] [EXTRA]
    If command is empty, will list all commands. change page with %(metachar)shelp [1|2|...]
    """
    alias = 'help'
    
    def run(self, *args):
        import modules.commands
        for command in (m for m in modules.commands 
                        if m.__class__.__name__== args[0] or m.alias == args[0]):
            helptext = (m.__doc__ % settings.__dict__).replace('\r\n','\n')
            if helptext.startswith("\n"):
                indent = re.match('^\n +', helptext).group()
                lines = [r.rstrip() for r in re.split(indent, helptext)]
            else:
                lines = [l.strip() for l in helptext.split('\n')]
            if not lines[0]: lines.pop(0)
            if not lines[-1]: lines.pop()
            
            for 
            self.chat("&")
            
                

#----------------- Hooks -------------------

class ChatCommands(Hook):
    """This hook intercepts chat packets and uses them to execute commands."""
    packets = ['chat']
    default = True # Load this hook by default
    
    def process(self, packet):
        if packet['message'].startswith(settings.metachar):
            from mcproxy.modules import commands
            packet['dir'] = None # block transmission of chat to server
            #try to parse command
            try:
                command_name, args, kwargs = commands.parse_command()
            except Exception as e:
                chat("Syntax error in command string.")
                return packet
            #try to find command with matching name
            try:
                command = commands.find_command(command_name)
            except IndexError:
                chat("No command by that name or alias")
                return packet
            #try to run the command
            try:
                command(*args,**kwargs)
            except Exception as e:
                chat("%s command returned exception: %s" % (command_name, e))
            #return useful packet object
            return packet

class TimeData(Hook):
    """Monitors and records in-game time. Makes this information available to other commands"""
    packets = ['time']
    
    def process(self, packet):
        time = packet['time']
        mchour = int(((time + 6000) % 24000) / 1000)
        mcminute = int(((time % 1000) / 1000.0) * 60.0)
        self.session.player.time = (mchour,mcminute)
        if settings.gui:
            gui.gui['time'].setText("%i:%.2i" % serverprops.playerdata['time'])
