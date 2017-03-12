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
		self.sendSeqArray = [False] * self.sequenceSize
		self.pktArray = [False] * self.sequenceSize
		self.timerArray = [False] * self.sequenceSize 
		self.head = 0
		self.end = self.windowSize
		self.lastSequence = 0

		self.rcvBuffer = [False]*self.sequenceSize
		self.rcvFile = ""
		self.serHost = serHost
		self.serPort = serPort
		self.mrws = mrws


	def cliConnect(self):
		sock = socket(AF_INET,SOCK_DGRAM)
		synPack = Packet('Hello',0,0,(0,1,0),self.mrws)
		synMsg = synPack.pack()
		#print synMsg[12:]
		sock.settimeout(2)
		for i in range(0,3):
			sock.sendto(synMsg,(self.serHost,self.serPort))
			try:
				response,serAdd = sock.recvfrom(2048)
				print "received ack"
				resPack = self.decode(response)
				if (resPack.ack_num == 0 and resPack.ack_flag == 1 and resPack.syn_flag == 1):
					self.sock = sock
					return True
			except:
				print("retry connect...")
		return False
	def disConnect(self):
		finPack = Packet("Bye",0,0,(0,0,1),0)
		finMsg = finPack.pack()
		self.sock.settimeout(2)
		for i in range(0,3):
			sock.sendto(finMsg,(self.serHost,self.serPort))
			try:
				response,serAdd = sock.recvfrom(2048)
				resPack = self.decode(response)
				if (resPack.ack_num == 0 and resPack.fin_flag == 1 and resPack.ack_flag == 1):
					return True
			except:
				print("retry disconnect...")
		return False
	def setRevFile(self,fileName):
		Name,fileType = fileName.split('.')
		self.rcvFile = Name + '-received'+'.'+fileType
		self.rcvWrite = open(self.rcvFile,'w')
	def sendPkt(self,data):
		pkt = Packet(data,self.lastSequence,0,(0,0,0),self.mrws)
		pktMsg = pkt.pack()
		self.pktArray.insert(pkt.seqNum,pkt)
		self.timerArray.insert(pkt.seqNum,time())
		self.lastSequence = (self.lastSequence + 1) % self.sequenceSize
		try:
			self.sock.sendto(pktMsg,(self.serHost,self.serPort))
			
			return pkt.datalen
		except:
			return 0
	def moveToNext(self):
		while(self.sendArray[self.head]):
			#self.send_pkt(self.end)
			self.rcvWrite(self.rcvBuffer[self.head])
			self.head = (self.head + 1) % self.sequenceSize
			self.end = (self.end + 1) %self.sequenceSize
			self.sendArray[self.end] = False
	def rcvMsg(self,ackMsg):
		rcvPkt = self.decode(ackMsg)
		rcvChkSum = rcvPkt.makecheksum(rcvPkt.data)
		if (rcvChkSum != rcvPkt.chksum):
			return 0
		if (rcvPkt.ack_flag):
			sendPkt = self.pktArray[rcvPkt.ack_num]
			if (sendPkt):
				rcvAckPkt = Packet("ack",0,sendPkt.seq_num,(1,0,0),0)
				try:
					self.sock.sendto(rcvAckPkt.pack(),(self.serHost,self.serPort))
				except:
					pass
				if not (self.sendArray[sendPkt.seq_num]):
					self.sendArray[sendPkt.seq_num] = True
					self.rcvBuffer.insert(sendPkt.seq_num,rcvPkt.data)
					self.moveToNext()
					return len(rcvPkt.data)
		return 0
	def finishTransfer(self):
		print "file " + self.rcvFile + "is downloaded"
		self.rcvWrite.close()
		self.sequenceSize = pow(2,sequenceBit)
		self.windowSize = self.sequenceSize/2
		self.sendSeqArray = [False] * self.sequenceSize
		self.pktArray = [False] * self.sequenceSize
		self.timerArray = [False] * self.sequenceSize 
		self.head = 0
		self.end = self.windowSize
		self.lastSequence = 0


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
		for i in range(self.head,self.end):
			if (not self.sendArray[i]):
				if self.pktArray[i].getTimeOut(time()):
					print "resend pkt: " + self.pktArray[i].seq_num
					try:
						self.sock.sendto(self.pktArray[i].pack(),(self.serHost,self.serPort))
					except:
						pass



SEQUENCE_BIT = 16
TIMEOUT = 2 #seconds
DATA_SIZE = 2000
def istext(filename):
    try:
        f = open(filename)
        s = f.read(512)
    except:
        print("invalid file")
        sys.exit()
    text_characters = "".join(map(chr,range(32,127)) + list("\n\r\t\b"))
    null_trans = string.maketrans("","")
    if not s:
        f.close()
        return True
    if "\0" in s:
        return False
    t=s.translate(null_trans,text_characters)
    if float(len(t))/float(len(s))>0.3:
        return False
    f.close()
    return True
def checkFile(fileName):
	if not (istext(fileName)):
		print ("Binary File")
		return False
	try:
		f = open(fileNamem,'r')
	except:
		return False
	f.close()
	return True
def connect(serHost,serPort,mrws):
	cliWin = Window(SEQUENCE_BIT,serHost,serPort,mrws)
	result = cliWin.cliConnect()
	if (result):
		return cliWin
	else:
		print ("fail to connect to server")
		sys.exit()
def transfer(fileName,cliWin):
	f = open(fileName,'rb')
	data = f.read(DATA_SIZE)
	transferred = 0
	received = 0
	cliWin.setRevFile(fileName)
	cliWin.isFinished = False
	cliWin.sock.settimeout(0.01)
	while (data or not cliWin.isFinished):
		if (data and cliWin.windowFree()):
			size = cliWin.sendPkt(data)
			transferred += size
			data = f.read(DATA_SIZE)
		elif (transferred == recevived):
			cliWin.finishTransfer()
			return

		try:
			ackMsg,addr = sock.recvfrom(2048)
			receivedSize = cliWin.recMsg(ackMsg)
			recevived += receivedSize
		except socket.timeout as e:
			pass
		cliWin.checkTimeout()
	return None
def disconnect():
	return cliWin.disConnect()

def clientStart(argv):
	if (len(argv) != 3):
		print("Invalid arguments")
		sys.exit()
	serHost,serPort = argv[1].split(':')
	mrws = int(argv[2])
	cliWin = connect(serHost,int(serPort),mrws)
	
	while(True):
		command = input("please input command:\n")
		commandList = command.split()
		if (len(commandList) > 1):
			if (commandList[0] == 'transfer' and len(commandList) == 2):
				fileName = commandList[1]
				if (checkFile(fileName)):
					transfer(fileName,cliWin)
				else:
					print ("Invlid file name")
			elif (commandList[0] == 'disconnect' and len(commandList) == 1):
					if (disconnect()):
						print "successfully end connection"
						break
					else:
						print "fail to disconnnect, please retry"	
			else:
				print "invalid command\n"



if __name__ == "__main__":
	clientStart(sys.argv)