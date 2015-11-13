from threading import Timer, Thread, Lock
import threading
import pdb
import sys
import select
import socket
import time
from configuration import Configuration

#tag:print
def printdata(head, node, source, end, data):
    print "NODE#%d: %s %d=====>%d data=[%s]" %( node, head, source, end, data)

def TCPSend(dest, content):
    print "TCPSend"
    #pdb.set_trace()
    TCP_IP = Configuration.getIP(dest) 
    MYIP = Configuration.getPublicIP()
    if TCP_IP == MYIP:
       print "TCPSend() cancelled. (WARNING: sending to itself)" #Ignore itself
       return 1 #sending msg failed
    TCP_PORT = Configuration.TCPPORT 
    ID = Configuration.getMyID()
    #print threading.currentThread().getName(), 'TCP Client Starting. I am Node#', ID
    BUFFER_SIZE = 1024
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    s.send(content)
    printdata("TCP Send", ID, ID, Configuration.getID(TCP_IP), content)
    s.close()
    return 0 #exit successfully 
    
def bcastCoordinator():
    for i in range(1, Configuration.getN() + 1):
        TCPSend(i, "Coordinator")

def bcastElection(ID):
    print "bcastElection"
    for bi in range(ID + 1, Configuration.getN() + 1):
        TCPSend( bi, "ELECTION") 

#tag:tcpserver
def TCPServer():
    ID = Configuration.getMyID()
    N = Configuration.getN()
    MYIP = Configuration.getPublicIP()
    TCP_PORT = Configuration.TCPPORT 
    BUFFER_SIZE = 1024
    print threading.currentThread().getName(), 'TCP Server Starting. I am Node#', ID, "ip=", MYIP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(( socket.gethostname(), TCP_PORT))
    print "TCP Server at", socket.gethostname(), ":", TCP_PORT
    server.listen(5) #At most 5 concurrent connection
    input = [server] 
    running = 1 
    while running: 
        inputready,outputready,exceptready = select.select(input,[],[]) 
    
        for s in inputready: 
            if s == server: 
                # handle the server socket 
                client, address = server.accept() 
                input.append(client) 
            else: 
                # handle all other sockets 
                data = s.recv(BUFFER_SIZE) 
                if data: 
                    peerID =  Configuration.getID( s.getpeername()[0] )
                    printdata("TCP Recv", ID, peerID, ID, data)
                    time.sleep(1)
                    if data[0] == 'C': #Coordinate
                        print "NODE #", ID, "Leader is", peerID
                    elif data[0] == 'E': #Election
                        if peerID < ID:
                            TCPSend( peerID, "OK")
                            bcastElection( ID)
                    elif data[0] == 'O': #OK
                        print "NODE #", ID, "Gave up. (Receive OK from", peerID, ")"
                else: 
                    s.close() 
                    input.remove(s) 
    server.close()

    print threading.currentThread().getName(), 'TCP Server Exiting. I am NODE#', ID
    return

#============================ main =========================#


leader = -1 # unknown leader 

tTCPServer = threading.Thread(target=TCPServer)
tTCPServer.daemon = True
tTCPServer.start()

time.sleep(1)

ID = Configuration.getMyID()
bcastElection(ID)

while True:
    try:
       print "Check every one alive. My leader is", leader 
       if leader != -1:
           if TCPSend(leader, "hi") == "1" : #leader dead
               bcastElection(ID)
    finally:
        time.sleep(5)

while threading.active_count() > 0:
    time.sleep(0.1)
