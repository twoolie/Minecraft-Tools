import math, time
import mcpackets, items
from modules import Command

class Tower(Command):
    """syntax: tower radius height blocktype [hollow=true]"""
    required_hooks = ['playertracking']
    
    def run(self, radius, height, block_type, *args):
        try:
            radius     = int(radius)
            height     = int(height)
        except:
            self.chat("radius and height must be integers")
            return
        try:
            block = items.get_block_type(block_type)
        except:
            self.chat("blocktype must be integer or known blocktype string")
            return
        
        print("radius:%s height:%s block:%s" % (radius, height, block))
        
        my_x = int(math.floor(self.server.playerdata['location'][0]));
        my_y = int(math.floor(self.server.playerdata['location'][1]));
        my_z = int(math.floor(self.server.playerdata['location'][2]));
        
        y_range = xrange(my_y, my_y + height)
        print(y_range)
        step = (1.0/radius)
        print(step)
        for y in y_range:
            sep = 0.0
            while sep < (2*math.pi):
                x = round(radius*math.cos(sep) + my_x)
                z = round(radius*math.sin(sep) + my_z)
                sep = sep + step
                print("X:%s Y:%s Z:%s" % (x, y, z))
                
                if block!=0:
                        #place block
                        packet = {'dir':'c2s', 'type':block, 'x':x, 'y':y-1, 'z':z, 'direction': 1} #direction: +X
                        encpacket = mcpackets.encode('c2s', 0x0F, packet)
                        self.comms.serverqueue.put(encpacket)
