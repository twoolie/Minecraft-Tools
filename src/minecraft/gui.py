import sys
import time
import positioning
import hooks
import mcpackets
import math
import chunktracker
from PyQt4 import QtGui, QtCore

framerate = 30

def start_gui(serverprops):
	app = QtGui.QApplication(sys.argv)
	main = MainWindow(serverprops)
	main.show()
	app.exec_()
	
def playerDataUpdate(serverprops):
	if not 'location' in serverprops.playerdata:
		return
	serverprops.gui['pos'].setText("X: %.2f\nY: %.2f\nZ: %.2f" % serverprops.playerdata['location'])
	rot = positioning.sane_angle(serverprops.playerdata['angle'][0])
	pitch = serverprops.playerdata['angle'][1]
	serverprops.gui['angle'].setText("Rotation: %i\nPitch: %i\nDirection: %s" % (rot, pitch, positioning.humanReadableAngle(rot)))
	#FIXME: this should run only if the actual block has changed, not the fractional one
	
	if not 'fracpos' in serverprops.playerdata: serverprops.playerdata['fracpos'] = (0,0,0)
	fracpos = (int(math.floor(serverprops.playerdata['location'][0])), int(math.floor(serverprops.playerdata['location'][1])), int(math.floor(serverprops.playerdata['location'][2])))
	if serverprops.playerdata['fracpos'] != fracpos:
		serverprops.playerdata['fracpos'] = fracpos
		serverprops.gui['stacklist'].setText(chunktracker.getBlockStack(serverprops.playerdata['fracpos'][0],serverprops.playerdata['fracpos'][2],serverprops))
	
	if serverprops.currentwp:
		playerpos = serverprops.playerdata['location']
		wppos = serverprops.waypoint[serverprops.currentwp]
		
		offset = positioning.getOffset(playerpos,wppos)
		angle = positioning.compassDirection(playerpos,wppos)
		hrangle = positioning.humanReadableAngle(angle)
		distance = positioning.getDistance2D(playerpos,wppos)
		serverprops.gui['wpdir'].setText("%.2f blocks %s\noffset: %i,%i,%i\nangle: %i" % (distance,hrangle,offset[0],offset[1],offset[2],angle))

def removeFromMenu(menu,item):
	num = menu.count()
	for i in range(num):
		itemname = str(menu.item(i).text())
		if itemname == item:
			menu.takeItem(i)
			break

def doAddWayPoint(name,loc,serverprops):
	if not name in serverprops.waypoint:
		serverprops.gui['wplist'].addItem(name)
	serverprops.waypoint[name] = loc
	positioning.saveWaypoints(serverprops)

class MainWindow(QtGui.QWidget):
	serverprops = None
	def __init__(self, serverprops):
		QtGui.QMainWindow.__init__(self)
		self.serverprops = serverprops
		gui = serverprops.gui
		
		# start main window
		self.setWindowTitle('mcproxy')
		grid = QtGui.QGridLayout()
		grid.setSpacing(10)
		
		# add player info
		grid.addWidget(QtGui.QLabel('Server:'),0,0)
		gui['server'] = QtGui.QLineEdit('stackunderflow.com:25555' if len(sys.argv)<2 else sys.argv[1])
		grid.addWidget(gui['server'],0,1)
		
		grid.addWidget(QtGui.QLabel('Current Time'), 1, 0)
		grid.addWidget(QtGui.QLabel('Current Position'), 2, 0)
		grid.addWidget(QtGui.QLabel('Player Angle'), 3, 0)
		gui['time'] = QtGui.QLabel('')
		gui['pos'] = QtGui.QLabel('X:\nY:\nZ:\n')
		gui['angle'] = QtGui.QLabel('Rotation:\nPitch:\nDirection:')
		grid.addWidget(gui['time'], 1, 1)
		grid.addWidget(gui['pos'], 2, 1)
		grid.addWidget(gui['angle'], 3, 1)
		
		# add waypoint list
		grid.addWidget(QtGui.QLabel('Waypoint:'), 5, 0)
		
		gui['wpdel'] = QtGui.QPushButton('-')
		gui['wpcomp'] = QtGui.QPushButton('Set Compass')
		gui['wptele'] = QtGui.QPushButton('Teleport')
		wpbtns = QtGui.QHBoxLayout()
		wpbtns.addWidget(gui['wpdel'])
		wpbtns.addWidget(gui['wpcomp'])
		wpbtns.addWidget(gui['wptele'])
		QtCore.QObject.connect(gui['wpdel'], QtCore.SIGNAL("clicked()"), self.removeWayPoint)
		QtCore.QObject.connect(gui['wpcomp'], QtCore.SIGNAL("clicked()"), self.compassWayPoint)
		QtCore.QObject.connect(gui['wptele'], QtCore.SIGNAL("clicked()"), self.Teleport)
		grid.addLayout(wpbtns,5,1)
		
		
		gui['wplist'] = QtGui.QListWidget()
		QtCore.QObject.connect(gui['wplist'], QtCore.SIGNAL("currentItemChanged (QListWidgetItem *,QListWidgetItem *)"), self.wayPointSelected)
		grid.addWidget(gui['wplist'], 6, 0, 1, 2)
		gui['wpname'] = QtGui.QLabel('')
		gui['wploc'] = QtGui.QLabel('')
		gui['wpdir'] = QtGui.QLabel('')
		grid.addWidget(gui['wpname'], 7, 0, 1, 2)
		grid.addWidget(gui['wploc'], 8, 0, 1, 2)
		grid.addWidget(gui['wpdir'], 9, 0, 1, 2)
		gui['newwp'] = QtGui.QPushButton('New Waypoint')
		gui['wpnamef'] = QtGui.QLineEdit()
		grid.addWidget(gui['wpnamef'],10,0)
		grid.addWidget(gui['newwp'],10,1)
		QtCore.QObject.connect(gui['newwp'], QtCore.SIGNAL("clicked()"), self.newWayPoint)
		gui['wpx'] = QtGui.QLineEdit()
		gui['wpy'] = QtGui.QLineEdit()
		gui['wpz'] = QtGui.QLineEdit()
		gui['wplocbtn'] = QtGui.QPushButton('New with loc')
		xyz = QtGui.QHBoxLayout()
		xyz.addWidget(gui['wpx'])
		xyz.addWidget(gui['wpy'])
		xyz.addWidget(gui['wpz'])
		xyz.addWidget(gui['wplocbtn'])
		QtCore.QObject.connect(gui['wplocbtn'], QtCore.SIGNAL("clicked()"), self.newWayPointWithLoc)
		gui['wpx'].setFixedWidth(40)
		gui['wpy'].setFixedWidth(40)
		gui['wpz'].setFixedWidth(40)
		grid.addLayout(xyz,11,0,1,2)
		
		# add hooks list
		hookgrid = QtGui.QGridLayout()
		hookgrid.addWidget(QtGui.QLabel("Hooks"),1,0,1,2)
		hookgrid.addWidget(QtGui.QLabel("Available"),2,0)
		hookgrid.addWidget(QtGui.QLabel("Active"),2,1)
		gui['hooklist'] = QtGui.QListWidget()
		gui['hookactive'] = QtGui.QListWidget()
		hooks.setupInitialHooks(self.serverprops)
		
		
		gui['hooklist'].setFixedWidth(130)
		gui['hookactive'].setFixedWidth(130)
		hookgrid.addWidget(gui['hooklist'],3,0,3,1)
		hookgrid.addWidget(gui['hookactive'],3,1,3,1)
		gui['activate'] = QtGui.QPushButton('Activate ->')
		gui['deactivate'] = QtGui.QPushButton('<- Remove')
		hookgrid.addWidget(gui['activate'],6,0)
		hookgrid.addWidget(gui['deactivate'],6,1)
		QtCore.QObject.connect(gui['activate'], QtCore.SIGNAL("clicked()"), self.activateHook)
		QtCore.QObject.connect(gui['deactivate'], QtCore.SIGNAL("clicked()"), self.deactivateHook)
		grid.addLayout(hookgrid,0,2,5,2)
		
		# add stack label
		stacklayout = QtGui.QGridLayout()
		stacklayout.addWidget(QtGui.QLabel("Stack from top to bottom:"),1,1)
		gui['stacklist'] = QtGui.QLabel("""<font color="red">Item 1</font><br>
Item 2<br>
Item 3<br>
Item 4<br>
Item 5<br>
Item 6<br>
Item 7<br>""")
		stacklayout.addWidget(gui['stacklist'],2,1,4,1)
		grid.addLayout(stacklayout,5,2,5,2)
		
		
		
		# set window layout to the grid
		self.setLayout(grid)
	
	def wayPointSelected(self, current=None, previous=None):
		selwp = str(current.text())
		self.serverprops.currentwp = selwp
		self.serverprops.gui['wpname'].setText(selwp)
		if selwp in self.serverprops.waypoint:
			self.serverprops.gui['wploc'].setText("%.2f,%.2f,%.2f" % self.serverprops.waypoint[selwp])
		else:
			print "waypoint undefined"
			self.serverprops.gui['wploc'].setText("unknown")
	
	def newWayPoint(self):
		wpname = str(self.serverprops.gui['wpnamef'].text())
		if wpname:
			doAddWayPoint(wpname,self.serverprops.playerdata['location'],self.serverprops)
		
	
	def newWayPointWithLoc(self):
		wpname = str(self.serverprops.gui['wpnamef'].text())
		try:
			wpx = int(str(self.serverprops.gui['wpx'].text()))
			wpy = int(str(self.serverprops.gui['wpy'].text()))
			wpz = int(str(self.serverprops.gui['wpz'].text()))
		except:
			print "not an integer value"
			return
		if wpname:
			if not wpname in self.serverprops.waypoint:
				self.serverprops.gui['wplist'].addItem(wpname)
			self.serverprops.waypoint[wpname] = (wpx,wpy,wpz)
			positioning.saveWaypoints(self.serverprops)
	
	def removeWayPoint(self):
		del self.serverprops.waypoint[self.serverprops.currentwp]
		removeFromMenu(self.serverprops.gui['wplist'],self.serverprops.currentwp)
		positioning.saveWaypoints(self.serverprops)

	def Teleport(self):
		#hooks.addHook(self.serverprops,'overridePlayerPos')
		wploc = self.serverprops.waypoint[self.serverprops.currentwp]
		my_x = int(math.floor(self.serverprops.playerdata['location'][0]))
		my_y = int(math.floor(self.serverprops.playerdata['location'][1]))
		my_z = int(math.floor(self.serverprops.playerdata['location'][2]))

		jumpdist = 20
		
		x_reached=False
		y_reached=False
		z_reached=False
		while((x_reached==False) or (y_reached==False) or (z_reached==False)):
			my_x = int(math.floor(self.serverprops.playerdata['location'][0]))
			my_y = int(math.floor(self.serverprops.playerdata['location'][1]))
			my_z = int(math.floor(self.serverprops.playerdata['location'][2]))
			if (my_x <= wploc[0]) and (x_reached==False): 	
					if wploc[0] - my_x > jumpdist:	my_x += jumpdist
					else: 							my_x = wploc[0]; x_reached = True
			elif 	my_x - wploc[0] > jumpdist:		my_x -= jumpdist
			else: 									my_x = wploc[0]; x_reached = True		

			if (my_y <= wploc[1]) and (y_reached==False): 	
					if wploc[1] - my_y > jumpdist:	my_y += jumpdist
					else: 							my_y = wploc[1]; y_reached = True 
			elif 	my_y - wploc[1] > jumpdist:		my_y -= jumpdist
			else: 									my_y = wploc[1] + 4; y_reached = True	
										
			if (my_z <= wploc[2]) and (z_reached==False): 	
					if wploc[2] - my_z > jumpdist:	my_z += jumpdist
					else: 							my_z = wploc[2]; z_reached = True 
			elif 	my_z - wploc[2] > jumpdist:		my_z -= jumpdist
			else: 									my_z = wploc[2]; z_reached = True				

			print("X:%s Y:%s Z:%s to X:%s Y:%s Z:%s %s%s%s" % (my_x, my_y, my_z, wploc[0], wploc[1], wploc[2],x_reached, y_reached, z_reached))
			time.sleep(0.05)
										
			packet = {'x':my_x, 'y':my_y, 'stance':0, 'z':my_z, 'onground':0}
			encpacket = mcpackets.encode("s2c",mcpackets.name_to_id['playerposition'],packet)
			self.serverprops.comms.clientqueue.put(encpacket)
		hooks.removeHook(self.serverprops,'overridePlayerPos')
	def compassWayPoint(self):
		wploc = self.serverprops.waypoint[self.serverprops.currentwp]
		packet = {'x':wploc[0], 'y':wploc[1], 'z':wploc[2]}
		encpacket = mcpackets.encode("s2c", mcpackets.name_to_id['spawnposition'], packet)
		self.serverprops.comms.clientqueue.put(encpacket)
	
	def activateHook(self):
		selected = str(self.serverprops.gui['hooklist'].currentItem().text())
		hooks.addHook(self.serverprops,selected)
	
	def deactivateHook(self):
		selected = str(self.serverprops.gui['hookactive'].currentItem().text())
		hooks.removeHook(self.serverprops,selected)