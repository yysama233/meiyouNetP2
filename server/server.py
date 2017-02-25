from socket import *
import sys
def server(argv):
	if (len(argv) != 3):
		print("Invalid input argument")
		sys.exit()
	#get port number
	port = int(argv[1])
	#get max receive window size
	mrws = int(argv[2])
	#start UDP socket
	try:
		serSock = socket(AF_INET, SOCK_DGRAM)
		serSock.bind(("",port))
	except:
		print("Error to create socket")
		sys.exit()
	print("State 1: Server is reay to receive")
if __name__ == '__main__':
    server(sys.argv)