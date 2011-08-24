import numpy, items, zlib

blocktype = {}
blockmeta = {}
blocklight = {}
skylight = {}

# TODO: numpy "chunks" not just stacks

def addPacketChanges(packetid, packet, serverprops):
	if packetid == 0x33:
		size_x = packet['size_x']+1
		size_y = packet['size_y']+1
		size_z = packet['size_z']+1
		#print "(%i,%i,%i) %i x %i x %i" % (packet['x'],packet['y'], packet['z'], packet['size_x'], packet['size_y'], packet['size_z'])
		
		chunkdata = zlib.decompress(packet['chunk'])
		if (len(chunkdata)) != (size_x * size_y * size_z * 2.5):
			print "ERROR: Chunk data size mismatch"
		for x in range(size_x):
			for z in range(size_z):
				coord = (packet['x'] + x,packet['z'] + z)
				stack = None
				if coord in blocktype:
					stack = blocktype[coord]
				else:
					stack = numpy.zeros(128)
					blocktype[coord] = stack
				for y in range(size_y):
					index = y + (z * size_y) + (x * size_y * size_z)
					btype = ord(chunkdata[index])
					stack[y + packet['y']] = btype
					#setBlockType(packet['x'] + x, packet['y'] + y, packet['z'] + z,btype) # FIXME: this seems to work...
	elif packetid == 0x34:
		pass
	elif packetid == 0x35:
		x = packet['x']
		y = packet['y']
		z = packet['z']
		btype = packet['type']
		setBlockType(x,y,z,btype)


def setBlockType(x,y,z,btype):
	coord = (x,z)
	if coord in blocktype:
		blocktype[coord][y] = btype
	else:
		#print "creating %i,%i" % (x,z)
		stack = numpy.zeros(128)
		stack[y] = btype
		blocktype[coord] = stack

