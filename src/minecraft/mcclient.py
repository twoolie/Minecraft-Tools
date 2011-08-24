#!/usr/bin/env python
import curses
import time
import urllib
import socket
import struct
import mcpackets
import thread
import minichunktracker
import sys

stdscr = curses.initscr()
curses.start_color()
curses.noecho()
curses.cbreak()
stdscr.keypad(1)

height, width = stdscr.getmaxyx()

mapwin = curses.newwin(height-10, width, 0, 0)
textwin = curses.newwin(10,width, height-10,0)

mapwin.addstr("TTYCraft 0.1",curses.A_REVERSE)
mapwin.refresh()

textwin.addstr("TTYCraft 0.1\n",0)
textwin.refresh()

#debuglog = open("debug.log",'w')

def logprint(text,style=0):
    #debuglog.write(text)
    #debuglog.flush()
    maxy,maxx = textwin.getmaxyx()
    y,x = textwin.getyx()
    if (y == maxy-1):
        textwin.move(0,0)
        textwin.deleteln()
        textwin.move(y-1,0)
    textwin.addstr(text,style)
    textwin.refresh()

def MCLogin(altlogin=0):
    user = "noone1234"
    passwd = ""
    logprint("Attempting login... ")
    data = urllib.urlencode({"user":user, "password":passwd, "version":"12"})
    #logprint(str(data))
    if altlogin == 0:
        response = urllib.urlopen("https://login.minecraft.net/",data)
    else:
        response = urllib.urlopen("http://www.minecraft.net/game/getversion.jsp",data)
    resp = response.read()
    if resp.count(":"):
        version,ticket,username,sessionID = resp[:-1].split(":")
        logprint("Success: logged in as %s, session ID %s\n" % (username,sessionID))
        return (username,sessionID)
    else:
        print ("Error! Returned %s\n" % resp)
        sys.exit()

def MCServerAuth(session,servId):
    logprint("Authenticating to minecraft.net... ")
    data = urllib.urlencode({"user":session[0], "sessionId":session[1], "serverId":servId})
    response = urllib.urlopen("http://www.minecraft.net/game/joinserver.jsp?"+data)
    resp = response.read()
    logprint("Response %s, continuing server join\n" % resp)

class clientprops():
    gotServLoc = 0
    playerloc = [0,0,0]
    playerdir = 0
    playerpitch = 0

session = MCLogin()

logprint("Connecting to server... ")
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.connect(("stackunderflow.com",25555))
buff = serversocket.makefile('rb', 4096)
logprint("Success\n")

logprint("Sending handshake... ")
serversocket.sendall(mcpackets.encode("c2s",0x02,{'username':session[0]}))
logprint("Waiting for response... ")

packetid = struct.unpack("!B", buff.read(1))[0]
#logprint("Got %s\n" % mcpackets.decoders[packetid]["name"]) 
if packetid == 0x02:
    packet = mcpackets.decode("s2c", buff, packetid)
    connhash = packet['username']
    logprint("Got conn hash: %s\n" % connhash)
else:
    logprint("Error: expected 0x01, got 0x%x" % packetid)

MCServerAuth(session,connhash)

logprint("Sending login... ")
serversocket.sendall(mcpackets.encode("c2s",0x01,{'protoversion':14, 'username':session[0], 'seed':0, 'dimension':0}))
logprint(" successful\n")

packetid = struct.unpack("!B", buff.read(1))[0]
if packetid != 0x01:
    logprint("unexpected packet 0x%x\n" % packetid)
packet = mcpackets.decode("s2c", buff, packetid)
entid = packet['entid']

logprint("Got entity ID: %i\n" % entid)

# now this is the point where we set it free

def networkThread(serversocket, buff, clientprops):
    logprint("Started network thread\n")
    while 1:
        packetid = struct.unpack("!B", buff.read(1))[0]
        #if packetid not in [0x1F, 0x21, 0x1C, 0x04, 0x22, 0x18]:
        #logprint("Got %s\n" % mcpackets.decoders[packetid]["name"]) 
        packet = mcpackets.decode("s2c", buff, packetid)
        if packetid == 0x33:
            logprint("test\n")
        if packetid in [0x33, 0x34, 0x35]:
            logprint("updated map with 0x%.2x\n" % packetid)
            minichunktracker.addPacketChanges(packetid, packet, None)
            drawMap()
        if packetid == 0x03:
            message = packet['message'].encode('utf-8')
            logprint(message+"\n")#,curses.color_pair(curses.COLOR_CYAN))
        if packetid in [0x0B, 0x0C, 0x0D]: # spawn pos?
            clientprops.gotServLoc = 1
            logprint("got player position: %f %f %f\n" % (clientprops.playerloc[0],clientprops.playerloc[1],clientprops.playerloc[2]))
            if packetid in [0x0B,0x0D]:
                clientprops.playerloc[0] = packet['x']
                clientprops.playerloc[1] = packet['y']
                clientprops.playerloc[2] = packet['z']
            if packetid in [0x0C,0x0D]:
                clientprops.playerdir = packet['rotation']
                clientprops.playerpitch = packet['pitch'] 
            serversocket.sendall(mcpackets.encode("c2s",0x0D,{'x':clientprops.playerloc[0], 
                                   'y':clientprops.playerloc[1],
                                   'z':clientprops.playerloc[2],
                                   'stance':clientprops.playerloc[1] + 1.62,
                                   'rotation':0,
                                   'pitch':0,
                                   'flying':0,
                                   }))
        if packetid == 0x06:
            logprint("got spawn pos")
            clientprops.playerloc[0] = packet['x']
            clientprops.playerloc[1] = packet['y']
            clientprops.playerloc[2] = packet['z']
            serversocket.sendall(mcpackets.encode("c2s",0x0D,{'x':clientprops.playerloc[0], 
                                               'y':clientprops.playerloc[1],
                                               'z':clientprops.playerloc[2],
                                               'stance':clientprops.playerloc[1] + 1.62,
                                               'rotation':0,
                                               'pitch':0,
                                               'flying':0,
                                               }))
        if packetid == 0x32:
            serversocket.sendall(mcpackets.encode("c2s",0x0D,{'x':clientprops.playerloc[0], 
                                               'y':clientprops.playerloc[1],
                                               'z':clientprops.playerloc[2],
                                               'stance':clientprops.playerloc[1] + 1.62,
                                               'rotation':0,
                                               'pitch':0,
                                               'flying':0,
                                               }))

def networkKeepAlive(serversocket,clientprops):
    while 1:
        if clientprops.gotServLoc == 1:
            serversocket.sendall(mcpackets.encode("c2s",0x0A,{
            'flying':0,
            }))
            serversocket.sendall(mcpackets.encode("c2s",0x0B,{'x':clientprops.playerloc[0], 
            'y':clientprops.playerloc[1],
            'z':clientprops.playerloc[2],
            'stance':clientprops.playerloc[1] + 1.62,
            'onground':False,
            }))
            serversocket.sendall(mcpackets.encode("c2s",0x0C,{
            'rotation':0,
            'pitch':0,
            'flying':0,
            }))
            serversocket.sendall(mcpackets.encode("c2s",0x0D,{'x':clientprops.playerloc[0], 
            'y':clientprops.playerloc[1],
            'z':clientprops.playerloc[2],
            'stance':clientprops.playerloc[1] + 1.62,
            'rotation':0,
            'pitch':0,
            'flying':0,
            }))
        else:
            logprint("no pos from server yet: %i\n" % clientprops.gotServLoc)
        time.sleep(0.05)

thread.start_new_thread(networkKeepAlive,(serversocket,clientprops))

thread.start_new_thread(networkThread,(serversocket,buff,clientprops))

def drawMap():
    # x along x axis
    # z along y axis
    maxy,maxx = mapwin.getmaxyx()
    midx,midy = maxx/2,maxy/2
    #logprint("midx %i, midy %i\n" % (midx,midy))
    plx, ply = clientprops.playerloc[0], clientprops.playerloc[2]
    #logprint("clix %i, cliy %i\n" % (plx,ply))
    minplx,minply = plx-midx,ply-midy
    #logprint("top left at %i, %i\n" % (minplx,minply))
    logprint("Chunktracker has %i stacks\n" % len(minichunktracker.blocktype))
    if len(minichunktracker.blocktype) > 0:
        logprint(str(minichunktracker.blocktype.keys()[0]))
    
    for x in xrange(0,maxx):
        for y in range(0,maxy-1):
            realx = int(minplx + x)
            realy = int(minply + y)
            char = ord(" ")
            if (realx,realy) == (int(plx),int(ply)):
                char = ord("*")
            elif (realx,realy) in minichunktracker.blocktype.keys():
                block = minichunktracker.blocktype[(realx,realy)][clientprops.playerloc[1]]
                char = int((block % 26) + ord("a"))
            mapwin.addch(y,x,char)
    mapwin.refresh()

while 1:
    key = chr(textwin.getch())
    if key == ',':
        clientprops.playerloc[2] += 0.02
    elif key == 'o':
        clientprops.playerloc[2] -= 1
    elif key == 'r':
        drawMap()
