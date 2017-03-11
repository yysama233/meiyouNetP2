import struct

class CRPHeader():
    sequence_number = 0
    ack_number = 0
    ack_flag = False
    syn_flag = False
    fin_flag = False
    window = 1
    checksum = 0

    SEQ_NUM = 0
    ACK_NUM = 1
    ACK_FLAG = 2
    SYN_FLAG =3
    FIN_FLAG = 4
    WINDOW = 5
    CHECKSUM =6

    def constructor(self, tuple_args):
        self.sequence_number = tuple_args[0]
        self.ack_number = tuple_args[1]
        self.ack_flag = tuple_args[2]
        self.syn_flag = tuple_args[3]
        self.fin_flag = tuple_args[4]
        self.window = tuple_args[5]
        self.checksum = tuple_args[6]
        return self


    def to_string(self):
        return str(self.sequence_number) + ',' + str(self.ack_number) + ',' \
               + str(self.ack_flag) + ',' + str(self.syn_flag) + ',' + str(self.fin_flag) + ','\
               + str(self.window) + ',' + str(self.checksum)


    def pack(self):
        return struct.pack("II???II", self.sequence_number, self.ack_number,
                           self.ack_flag, self.syn_flag, self.fin_flag,
                           self.window, self.checksum)

    @staticmethod
    def unpack(bytes):
        return struct.unpack("ii???ii", bytes)


    @staticmethod
    def bytes_to_header(msg, HEADER_SIZE):
        """Given a packet returns the header is the string form"""
        header_tuple = CRPHeader.unpack(msg[0:HEADER_SIZE])
        header = CRPHeader().constructor(header_tuple)
        header = header.to_string()
        return header

