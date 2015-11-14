from threading import Timer, Thread, Lock
import threading
import pdb
import sys
import select
import socket
import time
from configuration import Configuration

timervar = -99999999
leader = -1 # unknown leader 

#tag:print
def printdata(head, node, source, end, data):
    print "NODE#%d: %s %d=====>%d data=[%s]" %( node, head, source, end, data)

def TCPSend(dest, content):
    print "TCPSend"
    TCP_IP = Configuration.getIP(dest) 
    MYIP = Configuration.getPublicIP()
    TCP_PORT = Configuration.TCPPORT 
    ID = Configuration.getMyID()
    BUFFER_SIZE = 1024
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((TCP_IP, TCP_PORT))
        s.send(content)
        printdata("TCP Send", ID, ID, Configuration.getID(TCP_IP), content)
        s.close()
        return 0 #exit successfully 
    except:
        printdata("Fail", ID, ID, Configuration.getID(TCP_IP), content)
        return 1
    
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
    global timervar
    global leader

    while 1: 
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
                    if data[0] == 'C': #Coordinate
                        print "NODE #", ID, "Leader is", peerID
                        leader = peerID
                    elif data[0] == 'E': #Election
                        if peerID < ID:
                            TCPSend( peerID, "OK")
                            bcastElection(ID)
                            timervar = 0
                        elif peerID == ID:
                            bcastElection(ID)
                            timervar = 0
                    elif data[0] == 'O': #OK
                        print "NODE #", ID, "Gave up. (Receive OK from", peerID, ")"
                        timervar = -99999
                else: 
                    s.close() 
                    input.remove(s) 
    server.close()

    print threading.currentThread().getName(), 'TCP Server Exiting. I am NODE#', ID
    return

def accumulate():
    global timervar
    while True:
        time.sleep(1) 
        if timervar >= 0:
            timervar += 1 
            print "wait OK for " , timervar, "/10 seconds..." 
        if timervar == 10:
            timervar = -9999999
            bcastCoordinator()

def checkalive():
    time.sleep(10)
    ID = Configuration.getMyID()
    #hold election by itself
    TCPSend(ID, "ELECTION")
    global leader
    while True:
       try:
          print "Check leader alive? My leader is", leader 
          if leader != -1:
              if TCPSend(leader, "hi") == 1 : #leader dead
                  TCPSend(ID, "ELECTION")
       finally:
           time.sleep(15)

#============================ main =========================#


t = threading.Thread(target=checkalive)
t.daemon = True
t.start()

t2 = threading.Thread(target=accumulate)
t2.daemon = True
t2.start()

TCPServer()

time.sleep(5)

while threading.active_count() > 0:
    time.sleep(0.1)
