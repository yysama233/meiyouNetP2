from socket import *
import sys
from string import *
import struct
from time import time
class Packet(object):
    def __init__(self,data,seqNum,ackNum,flags,mrws):
        self.seq_num = seqNum
        self.data = data
        self.datalen = len(data)
        self.ack_num = ackNum
        self.ack_flag = flags[0]
        self.syn_flag = flags[1]
        self.fin_flag = flags[2]
        self.mrws = mrws
        self.time = time
        #self.chksum = self.makecheksum(self.data)
        self.formatString = "!HHHH???B"+ (str)(self.datalen) + "s"
    def makecheksum(self,data):
        sum = 0
        for i in range(len(data)):
            c = data[i]
            sum = sum+ ord(c) 
            if (sum > 0xFFFF):
                sum = (sum + 1) & (0x0000FFFF)
        return sum
    def setchksum(self,checksum):
        self.chksum = checksum
    def pack(self):
        self.chksum = self.makecheksum(self.data)
        return struct.pack(self.formatString,self.seq_num,self.ack_num,self.datalen,self.chksum,self.ack_flag,self.syn_flag,self.fin_flag,self.mrws,self.data)

    def getTimeOut(self,curTime):
        return (self.time - curTime > 2)

class Window(object):
    def __init__(self,sequenceBit,serHost,serPort,mrws):
        self.sequenceSize = pow(2,sequenceBit)
        self.windowSize = self.sequenceSize/2
        self.sendArray = [False] * self.sequenceSize
        self.sendBuffer = []
        self.pktBuffer = []
        self.recBuffer = []
        #self.timerArray = []
        self.head = 0
        self.end = self.windowSize
        self.lastSequence = 0
        self.lastAck = 0
        self.serHost = serHost
        self.serPort = serPort
        self.mrws = mrws

    def cliConnect(self):
        sock = socket(AF_INET,SOCK_DGRAM)
        synPack = Packet('Hello',0,0,(0,1,0),self.mrws)
        synMsg = synPack.pack()
        print synMsg[12:]
        sock.settimeout(2)
        for i in range(0,3):
            sock.sendto(synMsg,(self.serHost,self.serPort))
            try:
                response,serAdd = sock.recvfrom(2048)
                resPack = self.decode(response)
                if (resPack.ack_num == 0 and resPack.ack_flag == 1 and resPack.syn_flag == 1):
                    self.sock = sock
                    return True
            except:
                print("retry connect...")
        return False
    def markAck(self,ACK):
        self.sendArray[ACK] = True
        
    def pushToBuffer(self,packet):
        self.sendBuffer.append(packet)
    def moveToNext(self):
        while(self.sendArray[self.head]):
            self.send_pkt(self.end)
            self.head = (self.head + 1) % self.sequenceSize
            self.end = (self.end + 1) %self.sequenceSize
            self.sendArray[self.end] = False
    def decode(self,response):

        string_format = "!HHHH???B"+ (str)(len(response) - 12) + "s"
        pack = struct.unpack(string_format, response)
        seqNum = int(pack[0])
        ackNum = int(pack[1])
        datalen = int(pack[2])
        chksum = int(pack[3])
        ack_flag = int(pack[4])
        syn_flag = int(pack[5])
        fin_flag = int(pack[6])
        rcvw = pack[7]
        data = pack[8]
        packet = Packet(data,seqNum,ackNum,(ack_flag,syn_flag,fin_flag),rcvw)
        packet.setchksum(chksum)
        return packet
    #set timer in this method
    def windowFree(self):
        return self.lastSequence != self.end

    def checkTimeout(self):
        toResend = []
        for i in range(self.head,self.end):
            if (not self.sendArray[i]):
                if self.sendBuffer[i].getTimeOut(time()):
                    toResend.append(self.sendbuffer[i])
        return toResend




SEQUENCE_BIT = 16
TIMEOUT = 2 #seconds


def connect(serHost,serPort,mrws):
    cliWin = Window(SEQUENCE_BIT,serHost,serPort,mrws)
    result = cliWin.cliConnect()
    if (result):
        return result
    else:
        print ("fail to connect to server")
        sys.exit()
def transfer(file,serHost,serPort,mrws):
    return None
def disconnect():
    return None
def clientStart(argv):
    if (len(argv) != 3):
        print("Invalid arguments")
        sys.exit()
    serHost,serPort = argv[1].split(':')
    mrws = int(argv[2])
    connectResult = connect(serHost,int(serPort),mrws)

    while(True):
        command = input("please input command:\n")
        commandList = command.split()
        if (len(commandList) > 1):
            if (commandList[0] == 'transfer' and len(commandList) == 2):
                if (connectResult):
                    transfer(commandList[1],serHost,serPort,mrws)
                else:
                    print "Please set up connection first"
            elif (commandList[0] == 'disconnect' and len(commandList) == 1):
                if (connectResult):
                    disconnect()
                    break
                else:
                    print "Please set up connection first"  
            else:
                print "invalid command\n"


if __name__ == "__main__":
    clientStart(sys.argv)