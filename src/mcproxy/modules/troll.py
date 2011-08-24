import math, time
from modules import Command
#import mcpackets
    
class Entomb(Command):
    """Syntax: entomb other_player [block_type]"""
    required_hooks = ['playertracking']
    
    def run(other_player, block_type="3"): #default to dirt
        try:
            otherplayer = [id for id,props in self.server.players.items() if other_player.lower() in props['playerName'].lower()][0]
        except:
            self.chat("Cannot find %s, maybe not in range!" % other_player)
            return
        try:
            block = int(block_type)
        except:
            print "%s is not an integer. cannot make block." % command[2]
            return
        
        their_x = int(math.floor(serverprops.players[otherplayer]['x']/32))
        their_y = int(math.floor(serverprops.players[otherplayer]['y']/32))
        their_z = int(math.floor(serverprops.players[otherplayer]['z']/32))
        
        for x in xrange(their_x -2, their_x + 2):
            for y in xrange(their_y -2, their_y + 5):
                for z in xrange(their_z -2, their_z + 2):
                    if block!=0:
                        packet = {'dir':'c2s', 'type':block, 'x':x, 'y':y-1, 'z':z, 'direction': 1} #direction: +X
                        print packet
                        encpacket = mcpackets.encode('c2s', 0x0F, packet)
                        serverprops.comms.serverqueue.put(encpacket)
