
"""
This file represents the API used by both the client and server for creating
a CRP connection and sending/receiving through a CRP connection.
"""

import socket
import sys
import struct
import builtins
import os
import time


import math

from CRPHeader import CRPHeader
from enum import Enum

MAX_RETRIES = 3
MAX_TIME_RECV_CONNECTION = 5
MAX_TIME_RECV_ACK = 7
MAX_RETRIES_SAME_PACKET = 15
MAX_SEGMENT_SIZE = 128

HEADER_SIZE = len(CRPHeader().pack())

# + 1 accounts for the semi-colon that is always appended to the CRP_header
MAX_DATA_SIZE = MAX_SEGMENT_SIZE - (HEADER_SIZE + 1)


def bytes(string):
    """Converts string to bytes using pack"""
    return builtins.bytes(string, 'utf-8')


def create_socket(family = socket.AddressFamily.AF_INET):
    try:
        sock = socket.socket(family, socket.SOCK_DGRAM)
    except socket.error as e:
        print("Socket creation has failed.")
        sys.exit(1)
    return sock

def bind(sock, IPv4address, port):
    try:
        sock.bind((IPv4address, int(port)))
    except socket.error as msg:
        print("Socket binding has failed.")
        sock.close()
        sys.exit(1)

# server listening for incoming calls
def listen(server, sock):
    incoming = receive(server, sock)
    result = incoming[0].split(',')
    syn_flag = (result[3]  ==  "True")
    return (syn_flag, incoming)

# server attempts to accept call
def accept(sock, address, server):
    header = CRPHeader()
    header.ack_number = 1
    header.ack_flag = True
    header.syn_flag = True

    ack = None
    curr_time = time.time()
    timeout = curr_time + MAX_TIME_RECV_CONNECTION

    server.seq_nbr -= 1
    send(server, sock, header.pack(), address)
    while ack is None and time.time() < timeout:
        try:
            ack = receive(server, sock, decode=False)[0]
            temp = CRPHeader.bytes_to_header(ack, HEADER_SIZE).split(',')
            temp = temp[2]
            temp = True if temp is "True" else False
            if not temp:
                raise socket.timeout
            # checksum validation should already be handled in receive
            # if not checking_checksum(ack):
            #     server.ack_nbr -= 1
            #     server.logger.debug("Checksum for ACK not matching.")
            #     continue
        except socket.timeout:
            server.seq_nbr -= 1
            server.logger.debug("Server did not receive ACK. Sending SYN-ACK.")
            send(server, sock, header.pack(), address)
            continue

    if ack is None:
        server.logger.debug("Server did not receive ACK.")
        return False

    server.logger.debug("Server successfully received ACK.")
    ack = CRPHeader.bytes_to_header(ack, HEADER_SIZE).split(',')
    if ack:
        return True
    else:
        return False

def checking_checksum(header):
    checksum_value = compute_checkSum(header, send=False)
    # print("CHECKSUM_VALUE IS " + str(checksum_value))
    # print("IN CHECKING_CHECKSUM: " + str(header))
    # print("unpacking header :" + str(CRPHeader.unpack(header[0:HEADER_SIZE])))

    header = CRPHeader.bytes_to_header(header, HEADER_SIZE)
    #print("computed checksum is " + str(checksum_value))
    #print("expected checksum is" + str(header.split(',')[6]))
    if int(checksum_value) == int(header.split(',')[6]):
        #print('Checksum for receive passed!')
        return True
    else:
        #print('Checksum for receive DID NOT pass!')
        return False
    return False

# client side trying to connect
def connect(sock, address, client):
    header = CRPHeader()
    header.syn_flag = True
    header = header.pack()
    header = compute_checkSum(header, send=True)
    send(client, sock, header, address)
    incoming = None
    curr_time = time.time()
    timeout = curr_time + MAX_TIME_RECV_CONNECTION

    while incoming is None and time.time() < timeout:
        try:
            incoming = receive(client, sock, decode=False)[0]
            # checksum validation should already be handled in receive
            # if not checking_checksum(incoming):
            #     client.ack_nbr -= 1
            #     client.logger.debug("Checksum for SYN-ACK not matching.")
            #     continue

        except socket.timeout:
            client.logger.debug("Client did not receive SYN-ACK, resending SYN.")
            send(client, sock, header, address)
            client.seq_nbr -= 1
            continue

    if incoming is None:
        client.logger.debug("Client timed out on receiving SYN-ACK.")
        return False

    result = CRPHeader.bytes_to_header(incoming, HEADER_SIZE).split(',')
    ack = result[2]
    syn = result[3]
    if ack and syn:
        header = CRPHeader()
        header.ack_flag = True
        header.sequence_number = client.seq_nbr

        curr_time = time.time()
        timeout = curr_time + MAX_TIME_RECV_CONNECTION
        while(time.time() < timeout):
            client.logger.debug("Client sending ACK to the server.")
            send(client, sock, header.pack(), address)
            client.seq_nbr -= 1
            time.sleep(1)
        return True
    return False


def split_into_segments(data, windowSize = 1):
    """ Return value is a list of tuples representing segments (aka packets);
        Each tuple is in the form (crp_header, data), where data is encoded to bytes
        Parameter: data, as a byte array"""

    # prepend length of total DATA transfer (including length and fta_header)
    # see diagram for structure of packet
    num_packets = math.ceil((len(data) + 4 + len(bytes(';'))) / (MAX_DATA_SIZE))

    data = fta.len(data + bytes(';')) + bytes(';') + data
    packet_list = []
    i = 0

    while num_packets is not 0:
        split = data[i:(i + MAX_DATA_SIZE)]
        i += (MAX_DATA_SIZE)
        packet = (CRPHeader(), split)
        packet_list.append(packet)
        num_packets -= 1
    return packet_list


# NOTE: this method is never used
def concat_segments(segment_list):
    """ Parameter: segment_list, list of segments where each segment is just a bytes object"""
    concatenated = ''
    for i in range(0, len(segment_list)):
        concatenated += segment_list[i]
    return concatenated


#
def compute_checkSum(message, send=True):
    """Compute checksum for message passed in as BYTES
    For send, just returns checksum value, for received returns new message as BYTES"""
    original = message

    if (not send):
        #print("In computer checksum message is : " + str(message))
        header_string = CRPHeader.bytes_to_header(message, HEADER_SIZE)
        #print("In computer checksum incoming checksum value is: " + str(header_string.split(',')[6]))

    header_string = CRPHeader.bytes_to_header(message, HEADER_SIZE)
    body = str(message[HEADER_SIZE:MAX_SEGMENT_SIZE])
    message = header_string + body


    checksum_header = CRPHeader()
    header = header_string.split(',')
    header[2] = True if header[2]=='True' else False
    header[3] = True if header[3] == 'True' else False
    header[4] = True if header[4] == 'True' else False
    checksum_header = checksum_header.constructor(((int(header[0]), int(header[1]), header[2], header[3],
                                  header[4], int(header[5]), 0)))

    sum = checksum(checksum_header.to_string() + ';' + body)

    #if (not send):
        #print("EXPECT SUM in CHECKSUM is :" + str(header[6]))
        #print("SUM in CHECKSUM is : " + str(sum))

    if not send:
        return sum
    else:
        checksum_header = CRPHeader()
        checksum_header = checksum_header.constructor((int(header[0]), int(header[1]), header[2], header[3], header[4],
                                     int(header[5]), int(sum)))

        message = checksum_header.pack() + original[HEADER_SIZE:MAX_SEGMENT_SIZE]

        return message



def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        if (i+1 < len(msg)):
            w = ord(msg[i]) + (ord(msg[i+1]) << 8)
            s = carry_around_add(s, w)
        else:
            s = carry_around_add(s, ord(msg[i]))
    return ~s & 0xffff


def send(client_server, sock, data, address, timeout_count=0, print=False):
    print = False
    try:
        """Data should always be BYTES"""
        data = compute_checkSum(data, send=True)
        if (print):
            builtins.print("In send. Message is: " + str(data))
        bytes_sent = b''
        bytes_sent = sock.sendto(data, address)
    except socket.timeout:
        # timeout_count +=1
        # if timeout_count <= MAX_RETRIES:
        #     send(client_server, sock, (data), address, timeout_count=timeout_count)
        # else:
        # NOTE: this should never really happen for UDP
        print("Socket timed out in + send." )
        sys.exit(1)
    client_server.seq_nbr = client_server.seq_nbr + 1

    return bytes_sent

def receive_ack(client_server, sock):
    """Receive an ACK if possible, or raise timeout, if so check if it is the expected ACK (matching numbers)"""
    try:
        msg = receive(client_server, sock, decode=False)[0]
    except socket.timeout:
        #print("not receiving an ack")
        raise socket.timeout

    header = CRPHeader.bytes_to_header(msg, HEADER_SIZE)
    header_split = header.split(',')
    client_server.window_other = header_split[5]
    seq = header_split[0]
    # - 1 because receive prematurely incremented ack in receive
    client_server.logger.debug("RECV_ACK: Incoming seq number: " + seq + " Host ack number: " + str(client_server.ack_nbr - 1))
    if int(seq) == (int(client_server.ack_nbr) - 1):
        # Check if ACK packet
        if header_split[2].strip() == "True":
            return True
    #print("False in rec_ack")
    #else decrement ack number b/c we received the wrong packet
    client_server.ack_nbr -= 1
    return False


def receive(client_server, sock, byteSize=4096, timeout_count=0, decode=True, print=False):
    print = False
    try:
        (msg, address) = sock.recvfrom(byteSize)
        if (print):
            builtins.print("In receive. Message is: " + str(msg))
    except socket.timeout:
        # NOTE: we don't need to do this, this was more relevant to my old homework
        # timeout_count +=1
        # if timeout_count <= MAX_RETRIES:
        #     receive(client_server, sock, timeout_count=timeout_count)
        #else:
        raise socket.timeout
        return

    except OSError:
        # For listening for connections on server side
        return(CRPHeader().to_string(), '')

    if msg is None:
        return None

    if not (checking_checksum(msg)):
        #print("In receive: checksum not matching.")
        return None

    client_server.ack_nbr = client_server.ack_nbr + 1

    if decode:
        header = CRPHeader.bytes_to_header(msg, HEADER_SIZE)
        msg = header + msg[HEADER_SIZE: MAX_SEGMENT_SIZE].decode()
    return msg, address


def send_ack(client_server, msg, sock, address):
    """Check if the packet we just received was the right packet, if so, send ACK, else handle"""
    if msg is None:
        return False

    header = CRPHeader.bytes_to_header(msg, HEADER_SIZE)

    #print("Send_ack: " + header)
    seq = header.split(',')[0]
    ack = header.split(',')[1]
    client_server.logger.debug("SEND_ACK: Incoming seq number: " + seq + " Host ack number: " + str(client_server.ack_nbr - 1))
    if int(seq) == int(client_server.ack_nbr) - 1:
        #sequence number matches current ack, send an ACK
        client_server.last_acked = client_server.ack_nbr - 1
        header = CRPHeader()
        header.ack_flag = True
        header.ack_number = client_server.ack_nbr
        header.sequence_number = client_server.seq_nbr
        header.window = client_server.window
        #print(header.to_string())
        header = header.pack()
        header = compute_checkSum(header, send=True)
        send(client_server, sock, header, address)
        return True
    elif (int(seq) < (int(client_server.ack_nbr) -1)):
        #if the incoming sequence number is LESS than current ack, send an ACK for the already received segment
        client_server.logger.debug("Segment has already been received. Discarding and sending previous ACK...")
        client_server.logger.debug("Sender packet had seq " + seq + " and ack " + ack)
        header = CRPHeader()
        header.ack_flag = True
        header.ack_number = client_server.ack_nbr
        header.sequence_number = int(ack)
        header.window = client_server.window
        header = compute_checkSum(header.pack(), send=True)
        send(client_server, sock, header, address)
        #this was not a true send, it was a retransmit of a previous ack, so decr. seq nbr and ack. nbr since
        #we received a dup. packet
        client_server.seq_nbr -= 1
        client_server.ack_nbr -= 1

        return False
    else:
        #if greater, discard
        client_server.logger.debug("SEND_ACK: Incoming seq number: " + seq + " Host ack number: " + str(client_server.ack_nbr - 1))
        client_server.logger.debug("Received packet was not expected!")
        client_server.ack_nbr -= 1
        return False


def close_sender_client(client_server, sock, address):
    crp_header = CRPHeader()
    crp_header.fin_flag = True
    crp_header.sequence_number = client_server.seq_nbr
    crp_header.ack_number = client_server.ack_nbr
    header =  crp_header.pack() + bytes(';' + fta.header.close.value)

    curr_time = time.time()
    timeout = curr_time + MAX_TIME_RECV_CONNECTION

    client_server.seq_nbr -= 1
    send(client_server, sock, header, address)
    client_server.logger.debug("Client sending FYN.")
    incoming = None
    while incoming is None and time.time() < timeout:
        try:
            incoming = receive(client_server, sock, decode=False)[0]
        except socket.timeout:
            client_server.logger.debug("Client did not receive FYN-ACK, resending FYN.")
            send(client_server, sock, header, address)
            client_server.seq_nbr -= 1
            continue

    if incoming is None:
        client_server.logger.debug("Client timed out on receiving FYN-ACK.")
        return False

    received_header = CRPHeader.bytes_to_header(incoming, HEADER_SIZE).split(',')
    if received_header[2] and received_header[4]:
        header = CRPHeader()
        header.ack_flag = True

        curr_time = time.time()
        timeout = curr_time + MAX_TIME_RECV_CONNECTION
        while(time.time() < timeout):
            client_server.logger.debug("Client sending ACK to the server.")
            send(client_server, sock, header.pack(), address)
            client_server.seq_nbr -= 1
            time.sleep(1)
        return True

    return False


def check_and_close_receive(client_server, response, sock, address):
        if response is not None:
            header = response.split(';')[0]
            if header.split(',')[4] == 'True':
                crp_header = CRPHeader()
                crp_header.fin_flag = True
                crp_header.ack_flag = True
                crp_header.ack_number = client_server.ack_nbr
                crp_header.sequence_number = client_server.seq_nbr
                message = crp_header.pack()
                message = message + bytes(';' + fta.header.close.value)

                current = time.time()
                end = current + MAX_RETRIES
                sock.settimeout(2)
                response = None
                client_server.logger.debug("Host sending FYN-ACK.")
                send(client_server, sock, message, address)
                #seq number will get messed up, but OK b/c close doesn't handle
                while time.time() < end:
                    try:
                        response = receive(client_server, sock, decode=False)[0]
                        if response is not None:
                            response = CRPHeader.bytes_to_header(response, HEADER_SIZE).split(',')
                            if response[2] == "True":
                                sock.settimeout(None)
                                return True
                            else:
                                client_server.logger.debug("Host did not receive ACK, resending FYN-ACK.")
                                send(client_server, sock, message, address)
                                client_server.seq_nbr -= 1
                    except socket.timeout:
                        client_server.logger.debug("Host did not receive ACK, resending FYN-ACK.")
                        send(client_server, sock, message, address)
                        client_server.seq_nbr -= 1

        sock.settimeout(None)
        return False

def close_sender_server(client_server, sock, address):
    crp_header = CRPHeader()
    crp_header.fin_flag = True
    sending = crp_header.pack()
    sending = sending + bytes(';' + fta.header.close.value)

    current_time = time.time()
    ending = current_time + MAX_RETRIES
    while time.time() < ending:
        '''send multiple FINS to client'''
        client_server.logger.debug("Server sending FIN to client.")
        client_server.logger.debug("Server sending FIN to client.")
        send(client_server, sock, sending, address)
        client_server.seq_nbr -= 1
        time.sleep(1)




class fta():
    numBytes = None
    class header(Enum):
        get = "GET"
        post = "POST"
        close = 'CLOSE'

    class err_codes(Enum):
        bad = "BAD_REQUEST"
        ok = "OK"
        error = "ERROR"

    # TODO: implement
    def to_string(self):
        return None

    @staticmethod
    def len(byte_arr):
        """Returns a packed int representing size of bytes object"""
        # + 4 b/c int itself is 4 bytes, and we are prepending length
        return struct.pack("i", len(byte_arr) + 4)


    @staticmethod
    def get_client(filename, sock, address, client):
        print()
        crp_header = CRPHeader()
        fta_header = fta.header.get.value

        crp_header.sequence_number = client.seq_nbr
        crp_header.ack_number = client.ack_nbr
        # print("Client ack number start of get_client is " + str(client.ack_nbr))
        crp_header.window = client.window

        # NOTE: Constraint: file name can not have semicolons

        # Send an initial message to server w/ GET request and filename"
        message = crp_header.pack()+ bytes(';' + fta_header + ';' + filename)
        send(client, sock, message, address, print = True)

        # Loop until we receive an ACK for this GET request, if we don't after N seconds, fail and return
        curr_time = time.time()
        timeout = curr_time + MAX_TIME_RECV_ACK

        ack_received = False

        # Loop until we receive an ACK for this GET request, if we don't after N seconds, fail and return
        curr_time = time.time()
        timeout = curr_time + MAX_TIME_RECV_ACK

        while not ack_received:
            if time.time() > timeout:
                client.logger.info("Max retries for GET REQUEST ACK exceeded. Terminating transmission.")
                return None
            try:
                ack_received = receive_ack(client, sock)
            except:
                #retransmit, so decr seg. number
                client.seq_nbr -= 1
                send(client, sock, message, address, print = True)

        client.logger.info("ACK for GET request received. Starting download....")

        client.logger.debug("Client seq nbr: " + str(client.seq_nbr) +  "Client ack nbr: " + str(client.ack_nbr) )

        # Receive initial packet -> check if its the right one by calling send_ack, if it is proceed, else
        # continue until we receive the right first packet
        print()
        packet = 0

        #NOTE: Refactoring so that bottom loop also does work of first loop

        response = None
        num_retries_same_packet = 0
        while not send_ack(client, response, sock, address):
            client.logger.debug("Expected first packet not yet received. Retrying")
            num_retries_same_packet += 1
            if (num_retries_same_packet > MAX_RETRIES_SAME_PACKET):
                client.logger.info("Max retries for same packet exceeded. Terminating transmission.")
                return None
            try:
                response = receive(client, sock, MAX_SEGMENT_SIZE, decode=False)[0]
            except:
                response = None
                client.logger.debug("Timed out on first packet received. Retrying.....")
            continue

        client.logger.debug("Client seq nbr:" + str(client.seq_nbr) + " Client ack nbr: " + str(client.ack_nbr) )

        start_time = time.time()

        # First 4 bytes of DATA is always length of DATA transfer, rest of packet is actual message
        # Also, first packet will always contain FTA header
        # NOTE: DATA is considered anything after the crp_header
        length = response[HEADER_SIZE + 1: HEADER_SIZE + 5]
        length = struct.unpack("i", length)[0]
        #print("Length is : " + str(length))

        # get actual file content of first packet (even if we don't have MAX_SEGMENT_SIZE bytes
        # this will work)
        # Next 4 bytes always fta_header represented as int
        status = response[HEADER_SIZE + 6: HEADER_SIZE + 10]
        status = struct.unpack("i", status)[0]
        #print("Status is :" + str(status))
        status = fta.err_codes.ok.value if status == 1 else fta.err_codes.bad.value

        content = response[HEADER_SIZE + 11: MAX_SEGMENT_SIZE]
        #print(str(content))

        remaining = length - (len(response) - HEADER_SIZE)

        client.logger.info("Receiving packet " + str(packet) + "(" + str(len(response) - HEADER_SIZE) + "bytes).")
        packet += 1

        # Now we need to receive remaining bytes of DATA
        i = 0
        num_retries_same_packet = 0
        while i < remaining:
            if (num_retries_same_packet > MAX_RETRIES_SAME_PACKET+20):
                client.logger.info("Max retries for same packet exceeded. Terminating transmission.")
                return None

            response = None
            try:
                response = receive(client, sock, MAX_SEGMENT_SIZE, decode=False, print=True)[0]
                #print(response)
            except struct.error as e:
                #print(e)
                client.logger.debug("ERROR UNPACKING!")
            except :
                num_retries_same_packet += 1
                client.logger.debug("Receive timed out. Continuing.....")
                continue
            # Check to see if correct packet expected
            # If not, retry
            if not send_ack(client, response, sock, address):
                #print("true")
                continue
            num_retries_same_packet = 0
            data = response[HEADER_SIZE + 1: MAX_SEGMENT_SIZE]
            i += len(data)
            content += data
            client.logger.info("Receiving packet " + str(packet) + "(" + str(len(data)) + "bytes).")
            packet += 1
            client.logger.debug("Client seq nbr:" + str(client.seq_nbr) + " Client ack nbr: " + str(client.ack_nbr))


        end_time = time.time()
        elapsed = end_time - start_time
        client.logger.info("Elapsed duration of transfer: " + str(elapsed) + " seconds")
        return (content,status)

    @staticmethod
    def get_server(request, file_content, sock, address, server, cli_window, encode = False):
        print()
        fta_header = fta.err_codes.ok.value if (file_content is not None) else fta.err_codes.bad.value
        if file_content is None:
            file_content = b''

        # Set a timeout for the socket so that recv_ACK will timeout
        sock.settimeout(2)

        # For a fixed amount of time, listen for incoming GET requests, meaning the client did not receive
        # the ACK for the get request

        server.logger.debug("Listening for incoming GET requests in case ACK was not received on client. (" +
                            str(MAX_TIME_RECV_ACK) + ") seconds.")
        curr_time = time.time()
        timeout = curr_time + MAX_TIME_RECV_ACK
        while not time.time() > timeout:
            try:
                incoming = receive(server, sock)
                if incoming is not None:
                    #print(incoming)
                    # Should not increment ack in receive because this is actually a re-transmit from the client
                    server.ack_nbr -= 1
                    # This is a resend, so decrement seq. nbr before sending (to match previous) AND after
                    server.logger.debug("DUP GET REQUEST---Server seq nbr: " + str(server.seq_nbr) + " Server ack nbr: " + str(server.ack_nbr))
                    server.seq_nbr -= 1
                    send_ack(server, request, sock, address)

            except socket.timeout:
                continue

        server.logger.info("Max time for (re)sending GET REQUEST ACK exceeded. Starting transmission.")
        server.logger.debug("Server seq nbr: " + str(server.seq_nbr) + " Server ack nbr: " + str(server.ack_nbr) )


        #Represent fta_header with an integer
        fta_header_bytes = struct.pack("i", 1) if fta_header == fta.err_codes.ok.value else struct.pack("i", 0)

        data = fta_header_bytes + bytes(';') + file_content

        data_packet_list = split_into_segments(data)

        num_packets = len(data_packet_list)

        remaining_to_send = num_packets


        # TODO: move this into a separate method since we are calling it again below
        for i in range(0, cli_window):
            if not remaining_to_send > 0:
                break
            if data_packet_list[i][1] == b'':
                continue
            if i is 0:
                server.logger.info("Packet 0 w/ FTA status: " + fta_header)
            crp_header = data_packet_list[i][0]
            #server.logger.debug("Server seq nbr: " + str(server.seq_nbr))
            #server.logger.debug("Server ack nbr: " + str(server.ack_nbr))
            crp_header.sequence_number = server.seq_nbr
            crp_header.ack_number = server.ack_nbr
            #print(crp_header.to_string())
            message = crp_header.pack() + bytes(';') + data_packet_list[i][1]
            server.logger.debug("Server seq nbr:" + str(server.seq_nbr) +  " Server ack nbr: " + str(server.ack_nbr))
            send(server, sock, message, address, print)
            server.logger.info("Sending packet " + str(i) + " (" + str(len(data_packet_list[i][1])) + "bytes).")
            #print(message)
            remaining_to_send -=1
            i += 1

        #NOTE: j keeps track of acks, i is for the packet sent
        j = 0
        num_retries_same_packet = 0

        while j < num_packets:
            #print("J is " + str(j))
            #print("Remaining to send is " + str(remaining_to_send))
            #print("I is " + str(i))
            try:
                old_ack = server.ack_nbr
                if receive_ack(server, sock):
                    server.logger.info("Successfully received ACK for packet " + str(j))
                    server.logger.debug("Server seq nbr:" + str(server.seq_nbr) +
                                        " Server ack nbr: " + str(server.ack_nbr))

                    #TODO: Cumulative acks, fast forward send by how much the ack was incremented

                    if remaining_to_send > 0:
                        if data_packet_list[i][1] == b'':
                            continue
                        if i is 0:
                            server.logger.info("Packet 0 w/ FTA status: " + fta_header)
                        crp_header = data_packet_list[i][0]
                        crp_header.sequence_number = server.seq_nbr
                        crp_header.ack_number = server.ack_nbr
                        message = crp_header.pack() + bytes(';') + data_packet_list[i][1]
                        send(server, sock, message, address, print=True)
                        #print(message)
                        server.logger.info("Sending packet " + str(i) + " (" + str(len(data_packet_list[i][1])) + "bytes).")
                        remaining_to_send -= 1
                        i += 1
                        num_retries_same_packet = 0
                    j += 1

            except socket.timeout:
                server.logger.debug("Did not successfully receive ACK for packet " + str(j))
                if ((i - cli_window) == j) or remaining_to_send == 0:
                    num_retries_same_packet += 1
                    server.logger.debug("NUM RETRIES SAME PACKET " + str(num_retries_same_packet))

                if (num_retries_same_packet > MAX_RETRIES_SAME_PACKET):
                    server.logger.info("Server did not receive ACK for last packet(s). GET success unsure.")
                    sock.settimeout(None)
                    return

                temp = i
                i = j
                server.seq_nbr = server.seq_nbr - ((temp - j))

                #Resend the window
                bound = i + cli_window
                while i < bound:
                    if remaining_to_send > 0:
                        if data_packet_list[i][1] == b'':
                            continue
                        if i is 0:
                            server.logger.info("Packet 0 w/ FTA status: " + fta_header)
                        crp_header = data_packet_list[i][0]
                        server.logger.debug("Server seq nbr: " + str(server.seq_nbr))
                        crp_header.sequence_number = server.seq_nbr
                        crp_header.ack_number = server.ack_nbr

                        message = crp_header.pack() + bytes(';') + data_packet_list[i][1]
                        send(server, sock, message, address, print=True)
                        server.logger.info("Sending packet " + str(i) + " (" + str(len(data_packet_list[i][1])) + "bytes).")
                        i += 1
                    else:
                        break

        if (remaining_to_send == 0 and num_retries_same_packet > MAX_RETRIES_SAME_PACKET):
            server.logger.info("Server did not receive ACK for last packet. GET success unsure.")

        #reset timeout to None to block for incoming requests back in server thread
        sock.settimeout(None)




    @staticmethod
    def post_client(filename, sock, address, content, client):
        print()
        crp_header = CRPHeader()
        fta_header = fta.header.post.value

        crp_header.sequence_number = client.seq_nbr
        crp_header.ack_number = client.ack_nbr
        # print("Client ack number start of get_client is " + str(client.ack_nbr))
        crp_header.window = client.window

        # NOTE: Constraint: file name can not have semicolons

        # Send an initial message to server w/ POST request and filename"
        message = crp_header.pack() + bytes(';' + fta_header + ';' + filename)
        send(client, sock, message, address, print=True)

        # Loop until we receive an ACK for this GET request, if we don't after N seconds, fail and return
        curr_time = time.time()
        timeout = curr_time + MAX_TIME_RECV_ACK

        ack_received = False

        while not ack_received:
            if time.time() > timeout:
                client.logger.info("Max retries for POST REQUEST ACK exceeded. Terminating transmission.")
                return None
            try:
                ack_received = receive_ack(client, sock)
            except:
                # retransmit, so decr seg. number
                client.seq_nbr -= 1
                send(client, sock, message, address, print=True)


        serv_window = int(client.window_other)

        client.logger.info("ACK for POST request received. Starting upload....")

        curr_time = time.time()
        timeout = curr_time + MAX_TIME_RECV_ACK
        client.logger.debug("Waiting for server to finish listening....")
        while(time.time() < timeout):
            time.sleep(1)

        client.logger.debug("Client seq nbr: " + str(client.seq_nbr) +  "Client ack nbr: " + str(client.ack_nbr) )

        # NOTE: below here, copied from get_server

        # Represent fta_header with an integer

        # This means that FTA header is OK
        fta_header_bytes = struct.pack("i", 1)

        data = fta_header_bytes + bytes(';') + content

        data_packet_list = split_into_segments(data)

        num_packets = len(data_packet_list)

        remaining_to_send = num_packets

        # TODO: move this into a separate method since we are calling it again below
        for i in range(0, serv_window):
            if not remaining_to_send > 0:
                break
            if data_packet_list[i][1] == b'':
                continue
            if i is 0:
                client.logger.info("Packet 0 w/ FTA status: " + fta_header)
            crp_header = data_packet_list[i][0]
            # client.logger.debug("Server seq nbr: " + str(client.seq_nbr))
            # client.logger.debug("Server ack nbr: " + str(client.ack_nbr))
            crp_header.sequence_number = client.seq_nbr
            crp_header.ack_number = client.ack_nbr
            # print(crp_header.to_string())
            message = crp_header.pack() + bytes(';') + data_packet_list[i][1]
            client.logger.debug("Client seq nbr:" + str(client.seq_nbr) + " Client ack nbr: " + str(client.ack_nbr))
            send(client, sock, message, address, print)
            client.logger.info("Sending packet " + str(i) + " (" + str(len(data_packet_list[i][1])) + "bytes).")
            # print(message)
            remaining_to_send -= 1
            i += 1

        # NOTE: j keeps track of acks, i is for the packet sent
        j = 0
        num_retries_same_packet = 0

        while j < num_packets:
            # print("J is " + str(j))
            # print("Remaining to send is " + str(remaining_to_send))
            # print("I is " + str(i))
            try:
                old_ack = client.ack_nbr
                if receive_ack(client, sock):
                    client.logger.info("Successfully received ACK for packet " + str(j))
                    client.logger.debug("Client seq nbr:" + str(client.seq_nbr) +
                                        " Client ack nbr: " + str(client.ack_nbr))

                    # TODO: Cumulative acks, fast forward send by how much the ack was incremented

                    if remaining_to_send > 0:
                        if data_packet_list[i][1] == b'':
                            continue
                        if i is 0:
                            client.logger.info("Packet 0 w/ FTA status: " + fta_header)
                        crp_header = data_packet_list[i][0]
                        crp_header.sequence_number = client.seq_nbr
                        crp_header.ack_number = client.ack_nbr
                        message = crp_header.pack() + bytes(';') + data_packet_list[i][1]
                        send(client, sock, message, address, print=True)
                        # print(message)
                        client.logger.info(
                            "Sending packet " + str(i) + " (" + str(len(data_packet_list[i][1])) + "bytes).")
                        remaining_to_send -= 1
                        i += 1
                        num_retries_same_packet = 0
                    j += 1

            except socket.timeout:
                client.logger.debug("Did not successfully receive ACK for packet " + str(j))
                if ((i - serv_window) == j) or remaining_to_send == 0:
                    num_retries_same_packet += 1
                    client.logger.debug("NUM RETRIES SAME PACKET " + str(num_retries_same_packet))

                if (num_retries_same_packet > MAX_RETRIES_SAME_PACKET):
                    client.logger.info("Client did not receive ACK for last packet(s). POST success unsure.")
                    sock.settimeout(None)
                    return

                temp = i
                i = j
                client.seq_nbr = client.seq_nbr - ((temp - j))

                # Resend the window
                bound = i + serv_window
                while i < bound:
                    if remaining_to_send > 0:
                        if data_packet_list[i][1] == b'':
                            continue
                        if i is 0:
                            client.logger.info("Packet 0 w/ FTA status: " + fta_header)
                        crp_header = data_packet_list[i][0]
                        client.logger.debug("Client seq nbr: " + str(client.seq_nbr))
                        crp_header.sequence_number = client.seq_nbr
                        crp_header.ack_number = client.ack_nbr

                        message = crp_header.pack() + bytes(';') + data_packet_list[i][1]
                        send(client, sock, message, address, print=True)
                        client.logger.info(
                            "Sending packet " + str(i) + " (" + str(len(data_packet_list[i][1])) + "bytes).")
                        i += 1
                    else:
                        break

        if (remaining_to_send == 0 and num_retries_same_packet > MAX_RETRIES_SAME_PACKET):
            client.logger.info("Client did not receive ACK for last packet. POST success unsure.")

        # reset timeout to None to block for incoming requests back in client thread
        sock.settimeout(None)

    @staticmethod
    def post_server(sock, address, server, request):
        print()

        # Set a timeout for the socket so that recv_ACK will timeout
        sock.settimeout(2)

        # For a fixed amount of time, listen for incoming POST requests, meaning the client did not receive
        # the ACK for the POST request

        server.logger.debug("Listening for incoming POST requests in case ACK was not received on client. (" +
                            str(MAX_TIME_RECV_ACK) + ") seconds.")
        curr_time = time.time()
        timeout = curr_time + MAX_TIME_RECV_ACK
        while not time.time() > timeout:
            try:
                incoming = receive(server, sock, decode=False)
                if incoming is not None:
                    #print(incoming)
                    # Should not increment ack in receive because this is actually a re-transmit from the client
                    server.ack_nbr -= 1
                    # This is a resend, so decrement seq. nbr before sending (to match previous) AND after
                    server.logger.debug("DUP POST REQUEST---Server seq nbr: " + str(server.seq_nbr) + " Server ack nbr: " + str(server.ack_nbr))
                    server.seq_nbr -= 1
                    send_ack(server, request, sock, address)

            except socket.timeout:
                continue

        server.logger.info("Max time for (re)sending GET REQUEST ACK exceeded. Starting transmission.")
        server.logger.debug("Server seq nbr: " + str(server.seq_nbr) + " Server ack nbr: " + str(server.ack_nbr) )

        # Receive initial packet -> check if its the right one by calling send_ack, if it is proceed, else
        # continue until we receive the right first packet


        print()
        packet = 0

        # NOTE: Refactoring so that bottom loop also does work of first loop

        response = None
        num_retries_same_packet = 0
        while not send_ack(server, response, sock, address):
            server.logger.debug("Expected first packet not yet received. Retrying")
            num_retries_same_packet += 1
            if (num_retries_same_packet > MAX_RETRIES_SAME_PACKET):
                server.logger.info("Max retries for same packet exceeded. Terminating transmission.")
                sock.settimeout(None)
                return None
            try:
                response = receive(server, sock, MAX_SEGMENT_SIZE, decode=False)[0]
            except:
                response = None
                server.logger.debug("Timed out on first packet received. Retrying.....")
            continue

        server.logger.debug("Server seq nbr:" + str(server.seq_nbr) + " Server ack nbr: " + str(server.ack_nbr))

        start_time = time.time()

        # First 4 bytes of DATA is always length of DATA transfer, rest of packet is actual message
        # Also, first packet will always contain FTA header
        # NOTE: DATA is considered anything after the crp_header
        length = response[HEADER_SIZE + 1: HEADER_SIZE + 5]
        length = struct.unpack("i", length)[0]
        #print("Length is : " + str(length))

        # get actual file content of first packet (even if we don't have MAX_SEGMENT_SIZE bytes
        # this will work)
        # Next 4 bytes always fta_header represented as int
        status = response[HEADER_SIZE + 6: HEADER_SIZE + 10]
        status = struct.unpack("i", status)[0]
        #print("Status is :" + str(status))
        status = fta.err_codes.ok.value if status == 1 else fta.err_codes.bad.value

        content = response[HEADER_SIZE + 11: MAX_SEGMENT_SIZE]
        #print(str(content))

        remaining = length - (len(response) - HEADER_SIZE)

        server.logger.info("Receiving packet " + str(packet) + "(" + str(len(response) - HEADER_SIZE) + "bytes).")
        packet += 1

        # Now we need to receive remaining bytes of DATA
        i = 0
        num_retries_same_packet = 0
        while i < remaining:
            if (num_retries_same_packet > MAX_RETRIES_SAME_PACKET+20):
                server.logger.info("Max retries for same packet exceeded. Terminating transmission.")
                sock.settimeout(None)

                return None

            response = None
            try:
                response = receive(server, sock, MAX_SEGMENT_SIZE, decode=False, print=True)[0]
                #print(response)
            except struct.error as e:
                #print(e)
                server.logger.debug("ERROR UNPACKING!")
            except :
                num_retries_same_packet += 1
                server.logger.debug("Receive timed out. Continuing.....")
                continue
            # Check to see if correct packet expected
            # If not, retry
            if not send_ack(server, response, sock, address):
                #print("true")
                continue
            num_retries_same_packet = 0
            data = response[HEADER_SIZE + 1: MAX_SEGMENT_SIZE]
            i += len(data)
            content += data
            server.logger.info("Receiving packet " + str(packet) + "(" + str(len(data)) + "bytes).")
            packet += 1
            server.logger.debug("Server seq nbr:" + str(server.seq_nbr) + " Server ack nbr: " + str(server.ack_nbr))


        end_time = time.time()
        elapsed = end_time - start_time
        server.logger.info("Elapsed duration of transfer: " + str(elapsed) + " seconds")

        #reset timeout to None to block for incoming requests back in server thread
        sock.settimeout(None)

        return (status,content)

