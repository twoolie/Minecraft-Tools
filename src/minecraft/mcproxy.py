#!/usr/bin/env python2.7
from test.test_telnetlib import EOF_sigil
__VERSION__ = ('0','5')
__AUTHOR__ = ('gm_stack', 'twoolie', 'kleinig')

import os.path, sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import socket, struct, time, sys, traceback, argparse, logging
from Queue import Queue
from threading import Thread, RLock
from binascii import hexlify
from conf import settings

#---------- Arguments ----------
if __name__== '__main__':
	class BetterArgParser(argparse.ArgumentParser):
		def convert_arg_line_to_args(self, arg_line):
			for arg in arg_line.split():
				if not arg.strip():
					continue
				yield arg
	parser = BetterArgParser(
			description="""
			===========================================================================
			| MCProxy minecraft hax server v%s by %s.
			===========================================================================
			"""%(".".join(__VERSION__), ". ".join(__AUTHOR__)),
			epilog="See included documentation for licensing, blackhats.net.au for info about the people.",
			fromfile_prefix_chars='@', # allow loading config from a file e.g. `mcproxy.py @stackunderflow`
		)
	parser.add_argument("server", help="The server to connect clients to.")
	parser.add_argument('-L',"--local-port", dest='local_port', default=25565,
						help="The local port mcproxy listens on (default: %(default)s")
	parser.add_argument('-m',"--modules", dest='modules', default=['all'], nargs='+', metavar='MODULE',
						help="Which modules should be activated by default. e.g \"-m all -troll\" or \"-m default troll.Entomb\"")
	parser.add_argument("--no-console", dest='console', action='store_false',
						help="Do not start an interactive console.")
	parser.add_argument('-c',"--metachar",  dest='metachar', default=settings.metachar, metavar='META',
						help="The metachar that prefixes mcproxy chat commands. (default: %(default)s)")
	parser.add_argument('-C', "--chat-color", dest='chat_color', default=settings.chat_color, metavar='COLORCODE',
						help="The colorcode for default chat color from mcproxy [values: 1-f]. (default: %(default)s)")
	parser.add_argument('-l', '--logevel', dest='log_level', default=settings.log_level, metavar='LEVEL',
						help="Set the loglevel seen in the console. (default: %(default)s)")
	parser.add_argument("--debug", action="store_true", default=False,
						help="Enables advanced debugging.")
	settings = parser.parse_args(namespace=settings)
	
#--------- Init Systems ---------
import mcpackets, nbt, hooks, items, modules, log
logging.root.level = logging.DEBUG
server_log = logging.getLogger("SERVER")

#--------- Threads ----------

def startNetworkSockets(settings):
	#====================================================================================#
	# server <---------- serversocket | mcproxy | clientsocket ----------> minecraft.jar #
	#====================================================================================#
	
	while True:
		try:
			# Client Socket
			listensocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			listensocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			listensocket.bind(('127.0.0.1', 25565)) # 25565
			listensocket.listen(1)
			server_log.info("Waiting for connection...")
			
			clientsocket, addr = listensocket.accept()
			server_log.info("Connection accepted from %s" % str(addr))
			
			# Server Socket
			#preserv = "70.138.82.67"
			#preserv = "craft.minestick.com"
			#preserv = "mccloud.is-a-chef.com"
			#preserv = "60.226.115.245"
			#preserv = 'simplicityminecraft.com'
			
			host = settings.server
			if ":" in host: 
				host, port = host.split(":")
				port = int(port)
			else: port = 25565
			server_log.info("Connecting to %s...", host)	
			serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			serversocket.connect((host,port))
			
			session = Session()
			settings.session = session
			session.comms.clientqueue = Queue()
			session.comms.serverqueue = Queue()
			session.comms.clientsocket = clientsocket
			session.comms.serversocket = serversocket
			
			#start processing threads
			serverthread = Thread(target=sock_foward, name=str(id(session))+"-ClientToServer", 
								args=("c2s", clientsocket, serversocket, session.comms.serverqueue, settings))
			serverthread.setDaemon(True)
			serverthread.start()

			clientthread = Thread(target=sock_foward, name=str(id(session))+"-ServerToClient", 
								args=("s2c", serversocket, clientsocket, session.comms.clientqueue, settings))
			clientthread.setDaemon(True)
			clientthread.start()
			
			#playerMessage.printToPlayer(session,"MCProxy active. %shelp for commands."%settings.metachar)
			
			#wait for something bad to happen :(
			serverthread.join()
			clientthread.join()
			server_log.info("Session(%s) exited cleanly.", id(session))
			
		except Exception as e:
			server_log.error("Something went wrong with Session(%s). (%s)", id(session), e )

def sock_foward(dir, insocket, outsocket, outqueue, settings):
	buff = FowardingBuffer(insocket, outsocket)
	session = settings.session
	try:
		while True:
			#decode packet
			buff.packet_start()
			packetid = struct.unpack("!B", buff.read(1))[0]
			if packetid in session.protocol.packets.keys():
				packet = session.protocol.decode(dir, buff, packetid)
				if packetid==0x01 and dir=='c2s':
					if packet['protoversion'] in mcpackets.supported_protocols.keys():
						session.comms.protocol = mcpackets.supported_protocols[packet['protoversion']]()
			else:
				server_log.critical("unknown packet 0x%2X from %s", packetid, {'c2s':'client', 's2c':'server'}[dir])
				buff.packet_end()
				raise Exception("Unknown Packet 0x%2X"%packetid)
				#playerMessage.printToPlayer(session,("unknown packet 0x%2X from" % packetid) + {'c2s':'client', 's2c':'server'}[dir])
			packetbytes = buff.packet_end()
			
			modpacket = run_hooks(packetid, packet, session)
			if modpacket == None: # if run_hooks returns none, the packet was not modified
				packet_info(packetid, packet, buff, session)
				buff.write(packetbytes)
			elif modpacket == {}: # if an empty dict, drop the packet
				pass
			else:
				packet_info(packetid, modpacket, buff, session)
				buff.write(session.comms.protocol.encode(dir,packetid,modpacket))
			
			#send all items in the outgoing queue
			while not outqueue.empty():
				task = outqueue.get()
				buff.write(task)
				outqueue.task_done()
				
	except socket.error, e:
		server_log.error("%s connection quit unexpectedly: %s", {'s2c':'server', 'c2s':'client'}[dir], e)
	finally:
		insocket.close()
		outsocket.close()
	return

#does not currently run
def ishell(settings):
	while True:
		try:
			command = raw_input("> ")
		except EOFError:
			server_log.info("Quit Shell!")
			break
		command = command.split(" ")
		try:
			modules.commands.runCommand(settings.session, command)
		except Exception as e:
			traceback.print_exc()
			print "error in command", command[0] 

#--------- utility ---------------
class FowardingBuffer():
	def __init__(self, insocket, outsocket, *args, **kwargs):
		self.inbuff = insocket.makefile('rb', 4096)
		self.outsock = outsocket
		self.lastpack = ""
		
	def read(self, nbytes):
		#stack = traceback.extract_stack()
		bytes = self.inbuff.read(nbytes)
		if len(bytes) != nbytes:
			raise socket.error("Socket has collapsed, unknown error")
		self.lastpack += bytes
		#self.outsock.send(bytes)
		return bytes
	
	def write(self, bytes):
		self.outsock.send(bytes)
		
	def packet_start(self):
		self.lastpack = ""
		
	def packet_end(self):
		return self.lastpack
		
	def render_last_packet(self):
		rpack = self.lastpack
		truncate = False
		if len(rpack) > 512:
			rpack = rpack[:32]
			truncate = True
		rpack = " ".join([hexlify(byte) for byte in rpack])
		if truncate: rpack += " ..."
		return rpack

#will not run yet
def run_hooks(packetid, packet, session):
	ret = None
	hooks = session.protocol.packets[packetid]['hooks']
	if hooks:
		for hook in hooks:
			try:
				retpacket = hook(packetid,packet,session)
				if retpacket != None:
					packet = retpacket
					ret = packet
			except Exception as e:
				traceback.print_exc()
				print('Hook "%s" crashed!' % modules.hook_to_name[hook]) #: File:%s, line %i in %s (%s)" % (execption[0], execption[1], execption[2], execption[3]))
				session.protocol.packets[packetid]['hooks'].remove(hook)
			#	#FIXME: make this report what happened
	return ret

def packet_info(packetid, packet, buff, session):
	if settings.dump_packets:
		if not settings.dumpfilter or (packetid in settings.filterlist):
			print packet['dir'], "->", session.protocol.packets[packetid]['name'], ":", packet
		if settings.hexdump:
			print buff.render_last_packet()

#storage class for a session with the server
class Session():
	def __init__(self):
		self.dump_packets = True
		self.dumpfilter = True
		self.filterlist = [0x01, 0x02, 0xFF]
		self.hexdump = False
		self.screen = None
		self.detect = False
		self.playerdata = {}
		self.playerdata_lock = RLock()
		self.players = {}
		self.gui = {}
		self.waypoint = {}
		self.currentwp = ""
		class comms:
			clientqueue = None
			serverqueue = None
			protocol = mcpackets.BaseProtocol()

if __name__ == "__main__":
	#====================================================================================#
	# server <---------- serversocket | mcproxy | clientsocket ----------> minecraft.jar #
	#====================================================================================#
	
	#---------- Spool up server threads ------------
	server_log.info("Server starting up on port %d", settings.local_port)
	sd = Thread(name="ServerDispatch", target=startNetworkSockets, args=(settings, ))
	sd.setDaemon(True)
	sd.start()

	#--------- Start interactive console ----------
	if settings.console:
		shell = Thread(name="InteractiveShell", target=ishell, args=(settings, ))
		shell.setDaemon(True)
		shell.start()

	while 1:
		try:
			time.sleep(1)
		except KeyboardInterrupt:
			if hasattr(settings, 'session'):
				if settings.session.comms.serversocket is not None:
					try: settings.session.comms.serversocket.shutdown()
					except: settings.session.comms.serversocket.close()
				if settings.session.comms.clientsocket is not None:
					try: settings.session.comms.clientsocket.shutdown()
					except: settings.session.comms.clientsocket.close()
			server_log.warn("Server Shutdown.")
			break
	#import gui
	#gui.start_gui(serverprops)
	#app should exit here, and threads should terminate
