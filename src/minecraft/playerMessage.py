import mcpackets

def printToPlayer(serverprops,message):
	packet = {'message':message}
	encpacket = mcpackets.encode("s2c",mcpackets.name_to_id['chat'],packet)
	serverprops.comms.clientqueue.put(encpacket)
