import struct
import nbt
from collections import OrderedDict as od
from StringIO import StringIO
# thanks to http://mc.kev009.com/wiki/Protocol

class BaseProtocol(object):
	packets = {
		# basic packets
		0x00: { 'name':'keepalive', 
				'decoders': [lambda buff: {}], 
				'hooks': []},
		
		0x01: { 'name':'login',
				'hooks': [],
				'format': [od([ ('entid',		nbt.TAG_Int),
								('unknown1',	nbt.TAG_UCS2_String),
								('mapseed', 	nbt.TAG_Long),
								('dimension',	nbt.TAG_Byte), ]),
						   od([ ('protoversion',nbt.TAG_Int),
								('username',	nbt.TAG_UCS2_String),
								('seed', 		nbt.TAG_Long),
								('dimension',	nbt.TAG_Byte), ])] },
		#disconnect
		0xFF: {	'name':'disconnect',
				'hooks': [],
				'format': [od([	('reason', nbt.TAG_UCS2_String),])] },
	}

class Pv14(BaseProtocol):
	version=14
	
	@staticmethod
	def decodeMultiBlockChange(buffer):
		packet = {
			'x':		nbt.TAG_Int(buffer=buffer).value,
			'z':		nbt.TAG_Int(buffer=buffer).value,
			'size':		nbt.TAG_Short(buffer=buffer).value,
			'coords':	[],
			'type':		None,
			'meta':		None,
			}
		for num in range(packet['size']):
			coord = nbt.TAG_Short(buffer=buffer).value
			packet['coords'].append(( (coord&0xF000)>>12, (coord&0x00FF), (coord&0x0F00)>>8, ))
		packet['type'] = buffer.read(packet['size'])
		packet['meta'] = buffer.read(packet['size'])
		return packet
	
	@staticmethod
	def decodeComplexEntity(buffer):
		return {
			'x':		nbt.TAG_Int(buffer=buffer).value,
			'y':		nbt.TAG_Short(buffer=buffer).value,
			'z':		nbt.TAG_Int(buffer=buffer).value,
			'payload':	nbt.TAG_Byte_Array(buffer=buffer, lentype=nbt.TAG_Short).value, # size is a short!
			}
	
	@staticmethod
	def decodeExplosion(buffer):
		packet = {
			'x':		nbt.TAG_Double(buffer=buffer).value,
			'y':		nbt.TAG_Double(buffer=buffer).value,
			'z':		nbt.TAG_Double(buffer=buffer).value,
			'unknown':	nbt.TAG_Float(buffer=buffer).value,
			'numrecs':	nbt.TAG_Int(buffer=buffer).value,
			'blocks':	[],
			}
		for num in range(packet['numrecs']):
			x = nbt.TAG_Byte(buffer=buffer).value
			y = nbt.TAG_Byte(buffer=buffer).value
			z = nbt.TAG_Byte(buffer=buffer).value
			packet['blocks'].append((x,y,z))
		return packet
	
	@staticmethod
	def decodeWindowClick(buffer):
		packet = {
			'windowid':	nbt.TAG_Byte(buffer=buffer).value,
			'slotid':	nbt.TAG_Short(buffer=buffer).value,
			'rightclick': nbt.TAG_Byte(buffer=buffer).value,
			'actionnum': nbt.TAG_Short(buffer=buffer).value,
	        'shift': nbt.TAG_Bool(buffer=buffer).value,  
			'itemid': nbt.TAG_Short(buffer=buffer).value
		}
		if (packet['itemid'] != -1):
			packet['itemcount'] = nbt.TAG_Byte(buffer=buffer).value
			packet['itemuses'] = nbt.TAG_Short(buffer=buffer).value
		return packet
	
	@staticmethod
	def decodeSetSlot(buffer):
		packet = {
			'windowid':	nbt.TAG_Byte(buffer=buffer).value,
			'slotid':	nbt.TAG_Short(buffer=buffer).value,
			'itemid': 	nbt.TAG_Short(buffer=buffer).value,
		}
		if (packet['itemid'] != -1):
			packet['itemcount'] = nbt.TAG_Byte(buffer=buffer).value
			packet['itemuses'] = nbt.TAG_Short(buffer=buffer).value
		return packet
	
	@staticmethod
	def encodeSetSlot(buffer, packet):
		nbt.TAG_Byte(value=packet['windowid'])._render_buffer(buffer)
		nbt.TAG_Short(value=packet['slotid'])._render_buffer(buffer)
		nbt.TAG_Short(value=packet['itemid'])._render_buffer(buffer)
		print packet['itemid']
		if (packet['itemid'] != -1):
			nbt.TAG_Byte(value=packet['itemcount'])._render_buffer(buffer)
			nbt.TAG_Byte(value=packet['itemuses'])._render_buffer(buffer)
	
	@staticmethod
	def decodeBlockPlace(buffer):
		packet = {
			'x':			nbt.TAG_Int(buffer=buffer).value,
			'y':			nbt.TAG_Byte(buffer=buffer).value,
			'z': 			nbt.TAG_Int(buffer=buffer).value,
			'Direction': 	nbt.TAG_Byte(buffer=buffer).value,
			'itemid': 		nbt.TAG_Short(buffer=buffer).value,
		}
		if (packet['itemid'] > 0):
			packet['amount'] = nbt.TAG_Byte(buffer=buffer).value
			packet['damage'] = nbt.TAG_Short(buffer=buffer).value
		return packet
	
	@staticmethod
	def encodeBlockPlace(buffer, packet):
		nbt.TAG_Int(value=packet['x'])._render_buffer(buffer)
		nbt.TAG_Byte(value=packet['y'])._render_buffer(buffer)
		nbt.TAG_Int(value=packet['z'])._render_buffer(buffer)
		nbt.TAG_Byte(value=packet['Direction'])._render_buffer(buffer)
		nbt.TAG_Short(value=packet['itemid'])._render_buffer(buffer)
		if (packet['itemid'] > 0):
			nbt.TAG_Byte(value=packet['amount'])._render_buffer(buffer)
			nbt.TAG_Short(value=packet['damage'])._render_buffer(buffer)
	
	@staticmethod
	def decodeWindowItems(buffer):
		packet = {
			'type':		nbt.TAG_Byte(buffer=buffer).value,
			'count':	nbt.TAG_Short(buffer=buffer).value,
			'payload': 	[],
		}
		for num in xrange(packet['count']):
			itemid = nbt.TAG_Short(buffer=buffer).value
			if (itemid != -1):
				count = nbt.TAG_Byte(buffer=buffer).value
				uses = nbt.TAG_Short(buffer=buffer).value
				packet['payload'].append({'itemid': itemid, 'count': count, 'uses': uses})
		return packet
	
	@staticmethod
	def decodeVehicleSpawn(buffer):
		packet = {
			'uniqueID':		nbt.TAG_Int(buffer=buffer).value,
			'type':			nbt.TAG_Byte(buffer=buffer).value,
			'x':			nbt.TAG_Int(buffer=buffer).value,
			'y':			nbt.TAG_Int(buffer=buffer).value,
			'z': 			nbt.TAG_Int(buffer=buffer).value,
			'unknown':		nbt.TAG_Int(buffer=buffer).value,
		}
		if packet['unknown'] > 0:
			packet['x?'] = nbt.TAG_Short(buffer=buffer).value
			packet['y?'] = nbt.TAG_Short(buffer=buffer).valu
			packet['z?'] = nbt.TAG_Short(buffer=buffer).valu
		return packet
	
	@staticmethod
	def decodeInsanity(buffer):
		#print "decoding insanity... this may not go well"
		objects = []
		while 1:
			i = nbt.TAG_Byte(buffer=buffer).value
			if (i == 127): return objects
			j = (i & 0xE0) >> 5
			k = i & 0x1F
			val = None
			if (j == 0):
				val = nbt.TAG_Byte(buffer=buffer).value
			elif (j == 1):
				val = nbt.TAG_Short(buffer=buffer).value
			elif (j == 2):
				val = nbt.TAG_Int(buffer=buffer).value
			elif (j == 3):
				val = nbt.TAG_Float(buffer=buffer).value
			elif (j == 4):
				val = nbt.TAG_String(buffer=buffer).value
			elif (j == 5):
				m = nbt.TAG_Short(buffer=buffer).value
				n = nbt.TAG_Byte(buffer=buffer).value
				i1 = nbt.TAG_Short(buffer=buffer).value
				val = [m,n,i1]
			else:
				print "unknown tag"
			objects.append(val)
	
	@staticmethod
	def decodeMobSpawn(buffer):
		packet = {
			'uniqueID':		nbt.TAG_Int(buffer=buffer).value,
			'mobtype':		nbt.TAG_Byte(buffer=buffer).value,
			'x':			nbt.TAG_Int(buffer=buffer).value,
			'y':			nbt.TAG_Int(buffer=buffer).value,
			'z': 			nbt.TAG_Int(buffer=buffer).value,
			'rotation': 	nbt.TAG_Byte(buffer=buffer).value,
			'pitch': 		nbt.TAG_Byte(buffer=buffer).value,
		}
		packet['insanity'] = decodeInsanity(buffer)
		return packet
	
	@staticmethod
	def decodeMetadata(buffer):
		packet = {
			'entid':		nbt.TAG_Int(buffer=buffer).value,
		}
		packet['insanity'] = decodeInsanity(buffer)
		return packet
	

	# name is name of packet
	# decoders is a set of functions which define specialty decoders
	# encoders is a set of functions which define specialty encoders
	# hooks is a list of functions to be called when a packet is received
	# format is s2c followed by c2s second

	packets = BaseProtocol.packets.copy()
	packets.update({
		0x02: { 'name':'handshake',
				'hooks': [],
				'format': [od([ ('username',	nbt.TAG_UCS2_String),])] },
		
		0x03: {	'name':'chat',
				'hooks': [],
				'format': [od([ ('message', 	nbt.TAG_UCS2_String),])] },
		
		0x04: {	'name':'time',
				'hooks': [],
				'format': [od([ ('time',		nbt.TAG_Long)])]},
			
		0x05: { 'name':'entityequipment',
				'hooks': [],
				'format': [od([ ('entityID',	nbt.TAG_Int),
								('slot',	nbt.TAG_Short),
								('itemID',	nbt.TAG_Short),
								('???',		nbt.TAG_Short),])] },
		
		0x06: {	'name':'spawnposition',
				'hooks': [],
				'format': [od([	('x', nbt.TAG_Int),
								('y', nbt.TAG_Int),
								('z', nbt.TAG_Int)	])],	},
		
		0x07: {	'name':'useent', 
				'hooks': [],
				'format': [od([	('User', nbt.TAG_Int),
								('Target', nbt.TAG_Int),
								('Left Click', nbt.TAG_Byte)])],	},
		
		0x08: { 'name': 'health',
				'hooks': [],
				'format': [od([ ('health', nbt.TAG_Short), ])],}, #health: 0-20
		
		0x09: { 'name':'respawn',
				'hooks':'',
				'format': [{}, od([ ('world', nbt.TAG_Byte), ])], },
		
		
		# playerstate packets	
		0x0A: {	'name':'flying',
				'hooks': [], 
				'format': [od([	('flying', 	nbt.TAG_Bool), ])] },
		
		0x0B: {	'name':'playerposition',
				'hooks': [],
				'format': [od([	('x',		nbt.TAG_Double),
								('y',		nbt.TAG_Double),
								('stance',	nbt.TAG_Double),
								('z',		nbt.TAG_Double),
								('onground',nbt.TAG_Bool),])] },
							
		0x0C: {	'name':'playerlook',
				'hooks': [],
				'format': [od([	('rotation',		nbt.TAG_Float),
								('pitch',			nbt.TAG_Float),
								('flying',			nbt.TAG_Bool),])] },
							
		0x0D: {	'name':'playermovelook',
				'hooks': [],
				'format': [	od([	('x',			nbt.TAG_Double),
									('y',			nbt.TAG_Double),
									('stance',		nbt.TAG_Double),
									('z',			nbt.TAG_Double),
									('rotation',	nbt.TAG_Float),
									('pitch',		nbt.TAG_Float),
									('flying',		nbt.TAG_Bool),]),
									
							od([	('x',			nbt.TAG_Double),
									('stance',		nbt.TAG_Double),
									('y',			nbt.TAG_Double),
									('z',			nbt.TAG_Double),
									('rotation',	nbt.TAG_Float),
									('pitch',		nbt.TAG_Float),
									('flying',		nbt.TAG_Byte),])] },
									
		# world interaction packets
		
		0x0E: {	'name':'blockdig',
				'hooks': [],
				'format': [od([	('status',			nbt.TAG_Byte),
								('x',				nbt.TAG_Int),
								('y',				nbt.TAG_Byte),
								('z',				nbt.TAG_Int),
								('direction',		nbt.TAG_Byte),])] },
						
							
		0x0F: {	'name':'blockplace',
				'hooks': [],
				'decoders' : [decodeBlockPlace],
				'encoders' : [encodeBlockPlace], },
						
		#more playerstate
			
		0x10: { 'name':'holding',
				'hooks':[],
				'format': [od([ ('item', nbt.TAG_Short), ])],},
	
		0x11: { 'name':'Use Bed',
				'hooks':[],
				'format': [od([ ('entityID', nbt.TAG_Int),
								('inbed', nbt.TAG_Byte),
								('x', nbt.TAG_Int),
								('y', nbt.TAG_Byte),
								('z', nbt.TAG_Int), ])],},
	
		
		0x12: {	'name':'armanim',
				'hooks': [],
				'format': [od([	('entityID',	nbt.TAG_Int),
								('Animate',		nbt.TAG_Byte),])] },
		
		0x13: { 'name':'entaction',
				'hooks': [],
				'format': [od([ ('entid',	nbt.TAG_Int),
								('action',	nbt.TAG_Byte),])] },
		
		#entities
		
		0x14: {	'name':'namedentspawn',
				'hooks': [],
				'format': [od([	('uniqueID',	nbt.TAG_Int),
								('playerName',	nbt.TAG_UCS2_String),
								('x',			nbt.TAG_Int),
								('y',			nbt.TAG_Int),
								('z',			nbt.TAG_Int),
								('rotation',	nbt.TAG_Byte),
								('pitch',		nbt.TAG_Byte),
								('currentItem',	nbt.TAG_Short),])] },
									
		0x15: {	'name':'pickupspawn',
				'hooks': [],
				'format': [od([	('uniqueID',	nbt.TAG_Int),
								('item',		nbt.TAG_Short),
								('count',		nbt.TAG_Byte),
								('unknown1',	nbt.TAG_Short),
								('x',			nbt.TAG_Int),
								('y',			nbt.TAG_Int),
								('z',			nbt.TAG_Int),
								('rotation',	nbt.TAG_Byte),
								('pitch',		nbt.TAG_Byte),
								('roll',		nbt.TAG_Byte),])] },
		
		0x16: {	'name':'collectitem',
				'hooks': [],
				'format': [od([	('collectedItemID', nbt.TAG_Int),
								('itemCollectorID', nbt.TAG_Int),])] },
		
		0x17: {	'name':'vehiclespawn',
				'hooks': [],
				'decoders': [decodeVehicleSpawn], },
		
		0x18: {	'name':'mobspawn',
				'hooks': [],
				'decoders': [decodeMobSpawn], },
		
		0x19: { 'name':'Painting',
				'hooks': [],
				'format': [od([ ('Entity ID',	nbt.TAG_Int),
								('Title',		nbt.TAG_UCS2_String),
								('X',			nbt.TAG_Int),
								('Y',			nbt.TAG_Int),
								('Z',			nbt.TAG_Int),
								('Direction',	nbt.TAG_Int), ])] },
		
		0x1B: {	'name':'Stance Update?',
				'hooks': [],
				'format': [od([	('unknown1',	nbt.TAG_Float),
								('unknown2',	nbt.TAG_Float),
								('unknown3',	nbt.TAG_Float),
								('unknown4',	nbt.TAG_Float),
								('unknown5',	nbt.TAG_Bool),
								('unknown6',	nbt.TAG_Bool), ])] },
		
		0x1C: { 'name':'entvelocity',
				'hooks': [],
				'format': [od([	('uniqueID',	nbt.TAG_Int),
								('x',			nbt.TAG_Short),
								('y',			nbt.TAG_Short),
								('z',			nbt.TAG_Short),])] },
		
		0x1D: {	'name':'destroyent',
				'hooks': [],
				'format': [od([	('uniqueID', 	nbt.TAG_Int),])] },
		
		0x1E: {	'name':'entity',
				'hooks': [],
				'format': [od([	('uniqueID', 		nbt.TAG_Int),])] },
		
		0x1F: {	'name':'relentmove',
				'hooks': [],
				'format': [od([	('uniqueID', 		nbt.TAG_Int),
								('x',				nbt.TAG_Byte),
								('y',				nbt.TAG_Byte),
								('z',				nbt.TAG_Byte),])] },
		
		0x20: {	'name':'entitylook',
				'hooks': [],
				'format': [od([	('uniqueID',		nbt.TAG_Int),
								('rotation',		nbt.TAG_Byte),
								('pitch',			nbt.TAG_Byte),])] },
								
		0x21: {	'name':   'relentmovelook',
				'hooks':  [],
				'format': [od([	('uniqueID', 		nbt.TAG_Int),
								('x',				nbt.TAG_Byte),
								('y',				nbt.TAG_Byte),
								('z',				nbt.TAG_Byte),
								('rotation',		nbt.TAG_Byte),
								('pitch',			nbt.TAG_Byte),])] },
								
		0x22: {	'name':   'enttele',
				'hooks':  [],
				'format': [od([	('uniqueID', 		nbt.TAG_Int),
								('x',				nbt.TAG_Int),
								('y',				nbt.TAG_Int),
								('z',				nbt.TAG_Int),
								('rotation',		nbt.TAG_Byte),
								('pitch',			nbt.TAG_Byte),])] },
		
		0x26: {	'name':   'entstatus',
				'hooks':  [],
				'format': [od([ ('entid',			nbt.TAG_Int),
								('entstatus',		nbt.TAG_Byte),])] },
		
		0x27: {	'name':   'attachent',
				'hooks':  [],
				'format': [od([	('entID', 			nbt.TAG_Int),
								('vehicleID',		nbt.TAG_Int),])] },
		
		0x28: {	'name':   'Entity Metadata',
				'hooks':  [],
				'decoders': [decodeMetadata], },
		#map
		
		0x32: {	'name':   'prechunk',
				'hooks':  [],
				'format': [od([	('x',				nbt.TAG_Int),
								('z',				nbt.TAG_Int),
								('mode',			nbt.TAG_Byte),])] },
								
		0x33: {	'name':'mapchunk',
				'hooks': [],
				'format': [od([	('x',				nbt.TAG_Int),
								('y',				nbt.TAG_Short),
								('z',				nbt.TAG_Int),
								('size_x',			nbt.TAG_Byte),
								('size_y',			nbt.TAG_Byte),
								('size_z',			nbt.TAG_Byte),
								('chunk',			nbt.TAG_Byte_Array), ])] },
								
							
		0x34: {	'name':'multiblockchange',	
				'decoders': [decodeMultiBlockChange],	
				'hooks': []},
		
		0x35: {	'name':'blockchange',
				'hooks': [],
				'format': [od([	('x',				nbt.TAG_Int),
								('y',				nbt.TAG_Byte),
								('z',				nbt.TAG_Int),
								('type',			nbt.TAG_Byte),
								('meta',			nbt.TAG_Byte),])] },	
		
		0x36: { 'name':'playnote',
				'hooks': [],
				'format': [od([ ('x',				nbt.TAG_Int),
								('y',				nbt.TAG_Short),
								('z',				nbt.TAG_Int),
								('instrumenttype',	nbt.TAG_Byte),
								('pitch',			nbt.TAG_Byte), ])] },
				
		
		0x3C: { 'name':'explosion',
				'hooks':[],
				'decoders': [decodeExplosion], },
			
		0x3D: { 'name':'Sound Effect',
				'hooks':[],
				'format':  [od([('effectID',		nbt.TAG_Int),
								('x',				nbt.TAG_Int),
								('y',				nbt.TAG_Byte),
								('z',				nbt.TAG_Int),
								('sound',			nbt.TAG_Int),])] },
	
		0x46: { 'name':'invalid state',
				'hooks': [],
				'format': [od([('reason',			nbt.TAG_Byte)])], },
	
		0x47: { 'name':'thunderbolt',
				'hooks': [],
				'format':  [od([('entid',			nbt.TAG_Int),
								('unknown',			nbt.TAG_Bool),
								('x',				nbt.TAG_Int),
								('y',				nbt.TAG_Int),
								('z',				nbt.TAG_Int), ])], },
	
		0x64: { 'name':'openwindow',
				'hooks': [],
				'format': [od([ ('window id',		nbt.TAG_Byte),
								('inventory type',	nbt.TAG_Byte),
								('window title',	nbt.TAG_String),
								('numslots',		nbt.TAG_Byte), ])] },
	
		0x65: { 'name':'closewindow',
				'hooks': [],
				'format': [od([ ('window id',	nbt.TAG_Byte), ])], },
	
		0x66: { 'name':'windowclick',
				'hooks': [],
				'decoders' : [decodeWindowClick],},
	
		0x67: { 'name':'setslot',
				'hooks': [],
				'decoders' : [decodeSetSlot],
				'encoders' : [encodeSetSlot],},
	
		0x68: { 'name':'windowitems',
				'hooks': [],
				'decoders': [decodeWindowItems],},
	
		0x69: { 'name':'updateprogressbar',
				'hooks': [],
				'format' : [od([('windowid',	nbt.TAG_Byte),
								('progressbar',	nbt.TAG_Short),
								('value',		nbt.TAG_Short), ])] },
	
		0x6A: { 'name':'transaction',
				'hooks': [],
				'format' : [od([('windowid',		nbt.TAG_Byte),
								('actionnumber',	nbt.TAG_Short),
								('accepted',		nbt.TAG_Byte), ])] },
	
		0x82: { 'name':'updatesign',
				'hooks': [],
				'format' : [od([('x',		nbt.TAG_Int),
								('y',		nbt.TAG_Short),
								('z',		nbt.TAG_Int),
								('Text1',	nbt.TAG_UCS2_String),
								('Text2',	nbt.TAG_UCS2_String),
								('Text3',	nbt.TAG_UCS2_String),
								('Text4',	nbt.TAG_UCS2_String), ])] },
		0x83: { 'name':'itemdata',
			'hooks':[],
			'format' : [od([('type',		nbt.TAG_Short),
							('id',			nbt.TAG_Short),
							('bytearray',	nbt.TAG_String),])]
			},
		0xC8: { 'name':'incrementstat',
				'hooks':[],
				'format':  [od([('statID', nbt.TAG_Int),
								('amount', nbt.TAG_Byte), ])] },
	})
	name_to_id = dict([(packets[id]['name'], id) for id in packets])

	@staticmethod
	def decode(direction, buffer, packetID):
		packet_desc = packets[packetID]
		
		#decode by format description
		if packet_desc.has_key('format'): #isinstance(decoder, dict):
			packet = {}
			format = packet_desc['format'][{"s2c":0,"c2s":-1}[direction]]
			#render to stream
			for field in format:
				try:
					packet[field] = format[field](buffer=buffer).value
				except Exception as e:
					print "error decoding %s->%s:%s(%s)"%(decoders[packetID]['name'], field, e.__class__.__name__, e)
			#print packet
		
		#decode using specialized decoder
		else:
			#use pre-made decoder
			decoder = packets[packetID]['decoders'][{"s2c":0,"c2s":-1}[direction]]
			packet = decoder(buffer)
			
		packet['dir'] = direction
		packet['packetID'] = packetID
		
		return packet

	@staticmethod
	def encode(direction, packetID, packet):
		outbuff = StringIO()
		outbuff.seek(0)
		packet_desc = packets[packetID]
		
		#write in the packet id
		nbt.TAG_ByteU(value=packetID)._render_buffer(outbuff)
		
		if not (packet.has_key('dir') and packet['dir']==None):
			#encode by format description
			if packet_desc.has_key('format'):
				format = packet_desc['format'][{"s2c":0,"c2s":-1}[direction]]
				#render packet to buffer
				for field in format:
					format[field](value=packet[field])._render_buffer(outbuff)
					
			#revert to specialised encoder
			elif packet_desc.has_key('encoders'):
				encoder = packet_desc['encoders'][{"s2c":0,"c2s":-1}[direction]]
				encoder(outbuff, packet)
				
			#i am error
			else:
				print("unable to render packetID", packetID)
		else:
			raise Exception("cannot determine packet direction")
		
		return outbuff.getvalue()
	
supported_protocols = {14: Pv14}