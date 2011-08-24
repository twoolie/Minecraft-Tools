import math

# playerpos and targetpos are tuples
# playerpos[0] = x
# playerpos[1] = y
# playerpos[2] = z
# +y is up, -y is down
# 

def getOffset(playerpos, targetpos):
	return ( playerpos[0] - targetpos[0],
			 playerpos[1] - targetpos[1],
			 playerpos[2] - targetpos[2])

def getDistance3D(playerpos, targetpos):
	return math.sqrt((playerpos[0] - targetpos[0])**2 + (playerpos[1] - targetpos[1])**2 + (playerpos[2] - targetpos[2])**2)

def getDistance2D(playerpos, targetpos):
	return math.sqrt((playerpos[0] - targetpos[0])**2 + (playerpos[2] - targetpos[2])**2)

def vertAngle(playerpos, targetpos):
	distance = getDistance2D(playerpos, targetpos)
	vDiff = playerpos[1] - targetpos[1]
	return math.atan(vDiff / distance)

def compassDirection(playerpos, targetpos):
	offset = getOffset(playerpos, targetpos)
	x = offset[0]
	if x == 0:
		x = 0.001
	z = offset[2]
	if (x > 0):
		return math.degrees(math.atan(z/x))+90
	else:
		return math.degrees(math.atan(z/x))+270
	

# -x = north
# +x = south
# -z = east
# +z = west

#			90 rotation
#			-X axis
#			^
#			| North
#	West	|		East
# +Z <------+-------> -Z
#	0 rot	|		180 rot
#			|
#			| South
#			v
#			+X axis
#			270 rot
#
# rotation = rotation % 360
# notch is spatially challenged
#

def sane_angle(playerangle):
	playerangle = playerangle % 360
	if (playerangle < 0):
		playerangle = (360 + playerangle)
	return playerangle

def humanReadableAngle(playerangle):
	playerangle = sane_angle(playerangle)
	angleNames = ["W","NW","N","NE","E","SE","S","SW"]
	index = int(round(((playerangle)*(len(angleNames)))/360))
	if index == 8:
		index = 0
	closest = angleNames[index]
	return closest

def coordsToPoint(playerpos,itempos):		
		angle = compassDirection(playerpos,itempos)
		hrangle = humanReadableAngle(angle)
		distance = getDistance2D(playerpos,itempos)
		return "%.2f blocks %s" % (distance,hrangle)

def saveWaypoints(serverprops):
	f = open("waypoints",'w')
	for waypoint in serverprops.waypoint:
		value = serverprops.waypoint[waypoint]
		if not waypoint == "Spawn":
			wp = "%s,%i,%i,%i\n" % (waypoint.replace(",","_"),value[0],value[1],value[2])
			f.write(wp)
	f.close()

def loadWaypoints(serverprops):
	f = open("waypoints",'r')
	waypoints = f.readlines()
	f.close()
	for waypoint in waypoints:
		waypoint = waypoint.split(",")
		if not waypoint[0] == "Spawn":
			serverprops.gui['wplist'].addItem(waypoint[0])
			serverprops.waypoint[waypoint[0]] = (int(waypoint[1]),int(waypoint[2]),int(waypoint[3]))
	