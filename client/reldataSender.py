from socket import *
import sys
from string import *
import struct
from time import time
import string
"""
Author: Yang Yang, Mingjun Xie, Yufeng Wang
Version 1.0

Client side of the data transfer, which implements the function such as packet packing, packet unpacking,
packet analysis and send/receive packet. The user is allowed to use command as followed to run the python file

python reldataSender.py [ip adress]:[port number] [windowsize] to establish connection with server

and type in command line

tranform [file to be transferred] to send out the file pack.

"""
class Packet(object):
    def __init__(self,data,seqNum,ackNum,flags,mrws):
        """Function fo initialize the packet

        Args:
            data: data to be included in the packet
            seqNum: sequence number of the packet
            ackNum: ackknowledge number of the packet
            flags: Synflag, AckFlag and Finflag array
            mrws: available window size

        Returns:
            null

        """
        self.seq_num = seqNum
        self.data = data
        self.datalen = len(data)
        self.ack_num = ackNum
        self.ack_flag = flags[0]
        self.syn_flag = flags[1]
        self.fin_flag = flags[2]
        self.mrws = mrws
        self.time = time()
        #self.chksum = self.makecheksum(self.data)
        self.formatString = "!HHHH???B"+ (str)(self.datalen) + "s"
    def makecheksum(self,data,datalen):
        """Function to make the checksum for the packet

        Args:
            data: data to be included in the packet
            datalen: the length of the data

        Returns:
            sum: checksum value of this packet

        """
        sum = 0
        #print "check sum datalen ",datalen
        for i in range(datalen):
            c = data[i]
            sum = sum+ ord(c)
            if (sum > 0xFFFF):
                sum = (sum + 1) & (0x0000FFFF)
        return sum
    def setchksum(self,checksum):
        """Function that sets the checksum for the packet

        Args:
            checksum: checksum

        Returns:
            null

        """
        self.chksum = checksum
    def pack(self):
        """Function that pack the packet

        Args:
            null

        Returns:
            struct: packed packet

        """
        #print "pack mrws: ",self.mrws
        self.chksum = self.makecheksum(self.data,self.datalen)
        return struct.pack(self.formatString,self.seq_num,self.ack_num,self.datalen,self.chksum,self.ack_flag,self.syn_flag,self.fin_flag,self.mrws,self.data)
    
class Window(object):
    def __init__(self,sequenceBit,serHost,serPort,mrws):
        """Function fo initialize the window buffer

        Args:
            sequenceBit: the sequence number of the packet
            serHost: server IP address
            serPort: server Port number
            mrws: window size

        Returns:
            null

        """
        self.sequenceSize = pow(2,sequenceBit)
        #self.windowSize = pow(2,10)
        self.sendArray = [False] * self.sequenceSize
        self.pktArray = [False] * self.sequenceSize
        self.timerArray = [False] * self.sequenceSize 
        self.head = 0
        #self.end = self.windowSize
        self.lastSequence = 0
        self.rcvWindowSize = mrws
        self.rcvBuffer = {}
        self.rcvFile = ""
        self.serHost = serHost
        self.serPort = serPort
        self.mrws = mrws
        self.serverRcvSize = 0
        self.ackked = 0
    def cliConnect(self):
        sock = socket(AF_INET,SOCK_DGRAM)
        synPack = Packet('Hello',0,0,(0,1,0),self.mrws)
        synMsg = synPack.pack()
        #print synMsg[12:]
        sock.settimeout(2)
        for i in range(0,3):
            sock.sendto(synMsg,(self.serHost,self.serPort))
            try:
                response,serAdd = sock.recvfrom(1000)
                print "received ack"
                resPack = self.decode(response)

                if (resPack.ack_num == 0 and resPack.ack_flag == 1 and resPack.syn_flag == 1):
                    self.sock = sock
                    self.serverRcvSize = resPack.mrws
                    self.windowSize = resPack.mrws
                    self.end = self.windowSize
                    return True
            except:
                print("retry connect...")
        return False
    def disConnect(self):
        """Function fo initialize the disconnection with the server

        Args:
            null

        Returns:
            if the disconnecion has been successfully setup

        """
        finPack = Packet("Bye",0,0,(0,0,1),self.rcvWindowSize)
        finMsg = finPack.pack()
        self.sock.settimeout(2)
        while True:
            self.sock.sendto(finMsg,(self.serHost,self.serPort))
            try:
                response,serAdd = self.sock.recvfrom(1000)
                resPack = self.decode(response)
                if (resPack.ack_num == 0 and resPack.fin_flag == 1 and resPack.ack_flag == 1):
                    return True
            except:
                #print("retry disconnect...")
                pass
        return False
    def setRevFile(self,fileName):
        """Function fo set up the file to be written

        Args:
            filename: input file to be sent to the server

        Returns:
            null

        """
        Name,fileType = fileName.split('.')
        self.rcvFile = Name + '-received'+'.'+fileType
        self.rcvWrite = open(self.rcvFile,'w')
    def sendPkt(self,data):
        """Function fo send out the packet to the server

        Args:
            data: data to be included in the packet

        Returns:
            null

        """
        pkt = Packet(data,self.lastSequence,0,(0,0,0),self.rcvWindowSize)
        pkt.time = time()
        pktMsg = pkt.pack()
        self.pktArray.insert(pkt.seq_num,pkt)
        self.timerArray.insert(pkt.seq_num,time())
        self.lastSequence = (self.lastSequence + 1) % self.sequenceSize
        print "seq ",pkt.seq_num

        while True:
            try:
                self.sock.sendto(pktMsg,(self.serHost,self.serPort))
                return pkt.datalen
            except:
                pass
    def moveToNext(self):
        """Function fo move the window to the next unacked packet in the window buffer

        Args:
            null

        Returns:
            null

        """
        while(self.sendArray[self.head]):
           
            print "write to file"
            print "cur head: ", self.head

            temp = self.rcvBuffer[self.head]
            self.rcvWrite.write(temp)
            print "finish write"
           # self.received += len(temp)

            self.head = (self.head + 1) % self.sequenceSize
            self.end = (self.end + 1) %self.sequenceSize
            self.sendArray[self.end] = False
            print "current head and end ", self.head, " ",self.end
            self.sendArray[self.head]
            self.rcvWindowSize = self.rcvWindowSize + 1
            print "move window finished!"
    def rcvMsg(self,ackMsg):
        """Function to acknowledge the packet from the server and move the window

        Args:
            ackMsg: received packet from server

        Returns:
            datareceived: decoded data length from ackMsg

        """
        rcvPkt = self.decode(ackMsg)
        #print "decode finished"
        rcvChkSum = rcvPkt.makecheksum(rcvPkt.data,rcvPkt.datalen)
        if (rcvChkSum != rcvPkt.chksum):
            print rcvChkSum
            print rcvPkt.chksum
            print "check sum error"
            return 0

        print "rcv ack: ",rcvPkt.ack_flag
        datareceived = 0
        if (rcvPkt.ack_flag == 1 and rcvPkt.fin_flag ==0 and rcvPkt.syn_flag == 0):
            sendPkt = self.pktArray[rcvPkt.ack_num]
            self.serverRcvSize = rcvPkt.mrws
            print "rcv pkt rcvw ", rcvPkt.mrws
            if (sendPkt):
                print "sendPkt exist: ", sendPkt.seq_num
                if not (self.sendArray[sendPkt.seq_num]):
                    self.ackked +=1
                    print "new pkt ", self.ackked
                    self.sendArray[sendPkt.seq_num] = True
                    print "set ackked to True", sendPkt.seq_num
                    self.rcvBuffer[sendPkt.seq_num] = rcvPkt.data
                    # here I restrict window size to be larger than 0
                    #if (self.rcvWindowSize > 0) :
                    self.rcvWindowSize = self.rcvWindowSize - 1
                    #else :
                    #    self.rcvWindowSize = 0
                    print("rcv insert at%d"%(sendPkt.seq_num))
                    self.moveToNext()
                    print "head and end after move window ", 
                    print self.head
                    print self.end
                    datareceived = rcvPkt.datalen
                else:
                    print "not new ", self.ackked
                    print "seq ",self.lastSequence
                rcvAckPkt = Packet("ack",0,sendPkt.seq_num,(1,0,0),self.rcvWindowSize)
                
                try:
                    self.sock.sendto(rcvAckPkt.pack(),(self.serHost,self.serPort))
                    print "ack sent ",rcvAckPkt.ack_num
                except:
                    print "pkt send ACK failed"
                    pass
                
        return datareceived
    def finishTransfer(self):
        """Function the terminate the transfer with server and refresh the window to the defaulted value

        Args:
            null

        Returns:
            if the termination is sucessful

        """
        print "file " + self.rcvFile + "is downloaded"
        self.sendArray = [False] * self.sequenceSize
        self.pktArray = [False] * self.sequenceSize
        self.timerArray = [False] * self.sequenceSize
        self.rcvBuffer = {} 
        self.rcvWrite.close()
        self.rcvWindowSize = self.mrws # not sure if this is good
        finTransPack = Packet("Zanshi Bye",self.lastSequence-1,self.lastSequence-1,(1,1,1),self.rcvWindowSize)
        finTranMsg = finTransPack.pack()
        self.sock.settimeout(2)
        
        while True:

            self.sock.sendto(finTranMsg,(self.serHost,self.serPort))
            try:
                response,serAdd = self.sock.recvfrom(1000)
                resPack = self.decode(response)
                if (resPack.syn_flag == 1 and resPack.fin_flag == 1 and resPack.ack_flag == 1):
                    return True
            except:
                pass
                #print("retry finishing tansfer file...")
        print("file transfer finished but connection not correct")
        return False


    def decode(self,response):
        """Function the unpack the packet received from the server size 

        Args:
            null

        Returns:
            if the termination is sucessful

        """
        string_format = "!HHHH???B"+ (str)(len(response) - 12) + "s"
        pack = struct.unpack(string_format, response)
        #print "pack:", pack
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
        #print "ack ",ack_flag
        return packet
    #set timer in this method
    def windowFree(self):
        """Function to check the window is free to receive further packet or not

        Args:
            null

        Returns:
            if the window is still free

        """
        return self.lastSequence < self.end

    def checkTimeout(self,curTime):
        """Function to check the timeout in the time array of unacked packet from window buffer, if the packet is timedout,
           it will be resent immediately, with the new time stamp set up accordingly

        Args:
            curtime: current time stamp to be compared with the pre-allocated time stamp in each packet

        Returns:
            null

        """
        print "Timeout check"
        print "head ", self.head
        if self.head < self.lastSequence:
            for i in range(self.head,self.lastSequence):
                print "check ",i
                if (not self.sendArray[i]):
                    print "timeout,",i
                    if (self.pktArray[i] and (curTime - self.pktArray[i].time) > 2):
                        print "resend pkt: " + str(self.pktArray[i].seq_num)
                        try:
                            
                            self.sock.sendto(self.pktArray[i].pack(),(self.serHost,self.serPort))
                            self.pktArray[i].time = time()
                        except:
                            pass
        else:
            for i in range(self.head,self.sequenceSize):
                if (not self.sendArray[i]):
                    if (self.pktArray[i] and (curTime - self.pktArray[i].time) > 2):
                        print "resend pkt: " + str(self.pktArray[i].seq_num)
                        try:
                            
                            self.sock.sendto(self.pktArray[i].pack(),(self.serHost,self.serPort))
                            self.pktArray[i].time = time()
                        except:
                            pass
            for i in range(0,self.lastSequence+1):
                if (not self.sendArray[i]):
                    if (self.pktArray[i] and (curTime - self.pktArray[i].time) > 2):
                        print "resend pkt: " + str(self.pktArray[i].seq_num)
                        try:
                            
                            self.sock.sendto(self.pktArray[i].pack(),(self.serHost,self.serPort))
                            self.pktArray[i].time = time()
                        except:
                            pass

SEQUENCE_BIT = 16
TIMEOUT = 2 #seconds
DATA_SIZE = 988
lastAckTime = time()
def istext(filename):
    """helper Function of checkfile to check if the input file is a text file with valid acsii values

    Args:
        filename: the filename of the file to be checked

    Returns:
        if the input file is a valid text file

    """
    try:
        f = open(filename)
        s = f.read(512)
    except:
        print("invalid file")
        sys.exit()
    text_characters = "".join(map(chr,range(32,127)) + list("\n\r\t\b"))
    null_trans = string.maketrans("","")
    #empty file is considered text file
    if not s:
        f.close()
        return True
    #file with \0 is usually binary file
    if "\0" in s:
        return False
    t=s.translate(null_trans,text_characters)
    #string with more than 30% binary characters are considered binary file
    if float(len(t))/float(len(s))>0.3:
        return False
    f.close()
    return True
def checkFile(fileName):
    """helper Function of checkfile to check if the input file is a text file with valid acsii values

    Args:
        filename: the filename of the file to be checked

    Returns:
        if the input file is a valid text file

    """
    if not (istext(fileName)):
        print ("Binary File")
        return False
    try:
        f = open(fileName,'r')
    except:

        return False
    f.close()
    return True
def connect(serHost,serPort,mrws):
    """helper Function to start connection

    Args:
        serHost: the server address
        serPost: the servere port number
        mrws: max receive window size

    Returns:
        cliWin: Windows struct

    """
    cliWin = Window(SEQUENCE_BIT,serHost,serPort,mrws)
    result = cliWin.cliConnect()
    if (result):
        return cliWin
    else:
        print ("fail to connect to server")
        sys.exit()
def transfer(fileName,cliWin):
    """helper Function to transfer file

    Args:
        filename: the filename to transfer
        cliWin: client Window

    Returns:
        None

    """
    f = open(fileName,'rb')
    data = f.read(DATA_SIZE)
    transferred = 0
    #cliWin.received = 0
    received = 0
    cliWin.setRevFile(fileName)
    cliWin.isFinished = False
    cliWin.sock.settimeout(0.01)
    lastAckTime = time()
    while (data or (not cliWin.isFinished)):
        if (data and cliWin.windowFree() and cliWin.serverRcvSize > 0):
            print "------------------send---------------------------"
            size = cliWin.sendPkt(data)
            transferred += size
            data = f.read(DATA_SIZE)
            # print "tran",transferred
            # print "received", received
        elif (transferred <= received):
            print "finish all"
            cliWin.finishTransfer()
            return
        else:
            if not data:
                print ("data all sent")
        print "head ",cliWin.head
        print "tail ", cliWin.end 
        print "tran", transferred
        print "received", received
        try:
            ackMsg,addr = cliWin.sock.recvfrom(1000)
            print "-----------------rcv MSG----------------------------"
            lastAckTime = time()
            receivedSize = cliWin.rcvMsg(ackMsg)
            #print "received Size", receivedSize
            received += receivedSize
        except:
            print "time out"
            pass
        curTime = time()
        if curTime - lastAckTime > 15:
            print "Server hasn't responsed for 15s. Server crashed."
            sys.exit()
        print "outmost head and tail"
        print cliWin.head
        print cliWin.end
        cliWin.checkTimeout(curTime)
    return None
def disconnect(cliWin):
    """helper Function to  disconnect

    Args:
        cliWin: client Window

    Returns:
        True: successfully disconnect

    """
    return cliWin.disConnect()

def clientStart(argv):
    """main loop function

    Args:
        argv: commandline input

    Returns:
        None

    """
    if (len(argv) != 3):
        print("Invalid arguments")
        sys.exit()
    serHost,serPort = argv[1].split(':')
    mrws = int(argv[2])
    if mrws > 255:
        print ("please input correct window size")
        sys.exit()
    cliWin = connect(serHost,int(serPort),mrws)
    
    while(True):
        command = raw_input("please input command:")
        commandList = command.split()
        if (len(commandList) >= 1):
            if (commandList[0] == 'transform' and len(commandList) == 2):
                fileName = commandList[1]
                if (checkFile(fileName)):
                    transfer(fileName,cliWin)
                else:
                    print ("Invlid file name")
            elif (commandList[0] == 'disconnect' and len(commandList) == 1):
                    if (disconnect(cliWin)):
                        print "successfully end connection"
                        break
                    else:
                        print "fail to disconnnect, please retry"   
            else:
                print "invalid command\n"

if __name__ == "__main__":
    clientStart(sys.argv)
