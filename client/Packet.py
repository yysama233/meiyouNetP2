from time import time
from socket import *
import sys
import string
import struct
class Packet(object):
#######注释注释注释注释#########
	def __init__(self,data,seqNum,ackNum,flags):
		self.seq_num = sequenceNum
		self.Len = dataLen
		self.data = data
		self.chksum = self.makecheksum(data)
		self.seqNum = seqNum
		self.time = time()
		self.ack_fag = flags[0]
		self.syn_flag = fags[1]
		self.fin_flag = flags[2]

	def makecheksum(data):
		sum = 0
		for i in range(len(data)):
			c = data[i]
			sum = sum+ c 
			if (sum > 0xFFFF):
				sum = (sum + 1) & (0x0000FFFF)
		return sum
	def getTimeOut(self,curTime):
		return (self.time - curTime > 2)
	def pack(self):