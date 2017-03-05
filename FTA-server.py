import argparse, sys, api, threading, logging, CRPHeader, time, os, builtins, socket, struct
from CRPHeader import CRPHeader

class Server():
    sock = None
    sock_ip4 = None
    sock_ip6 = None
    isConnected = False
    connected = None
    client_address = -1
    window = 1
    window_other = 1
    seq_nbr = 0
    ack_nbr = 0
    last_acked = 0
    logger = None
    thread_ip4 = None
    thread_ip6 = None
    lock = None
    port = -1
    uiThread = None
    serverThread = None

    def __init__(self, port, logger):
        self.port = port
        self.logger = logger
        self.init()
        self.spawn_threads()

    def init(self):
        self.sock = None
        self.sock_ip4 = None
        self.sock_ip6 = None
        self.isConnected = False
        self.client_address = -1
        self.window = 1
        self.window_other = 1
        self.seq_nbr = 0
        self.ack_nbr = 0
        self.last_acked = 0
        self.thread_ip6 = None
        self.thread_ip6 = None


        self.init_socket(self.port)

    # Create UDP socket for the server
    def init_socket(self, port):
        self.sock_ip4 = api.create_socket()
        self.sock_ip6 = api.create_socket(family=socket.AddressFamily.AF_INET6)
        logging.debug('Initializing Server socket.')
        api.bind(self.sock_ip4, '', int(port))
        api.bind(self.sock_ip6, '',  str(int(port) + 1))

    def spawn_threads(self):
        self.connected = threading.Event()
        self.connected.clear()

        self.uiThread = threading.Thread(target = self.UI_run)
        self.serverThread = threading.Thread(target = self.Server_run)
        self.uiThread.setDaemon(True)
        self.serverThread.setDaemon(True)
        self.uiThread.start()
        self.serverThread.start()

        try:
            while(1):
                time.sleep(5)
        except KeyboardInterrupt:
            self.graceful_close()


    def UI_run(self):
        logging.debug('User input thread has spawn.')
        while 1:
            user_input = input("--->")
            array_of_input = user_input.strip().split()
            if array_of_input[0].lower() == "terminate":
                if self.isConnected:
                    api.close_sender_server(self, self.sock, self.client_address)
                    break; #same functionality as os exit
                else:
                    logging.info('Server has successfully terminated.')
                    os._exit(1)
            elif array_of_input[0].lower() == "window":
                if len(array_of_input) != 2:
                    logging.info("Usage: window [size as INT]")
                    continue

                try:
                    array_of_input[1] = int(array_of_input[1])
                except:
                    logging.info("Usage: window [size as INT]")
                    continue


                if int(array_of_input[1]) < 1:
                    logging.info('Invalid window size given.')
                else:
                    win_size = int(array_of_input[1])
                    self.window = win_size
                    logging.info("Window size has been changed to " + str(self.window))
            else:
                logging.info("input of " + array_of_input[0] + " is not an supported operation.")

    def listen(self):
        incoming = False
        #logging.debug('Server Ack Nbr: ' + str(self.ack_nbr) + '; Server Seq Nbr: ' + str(self.seq_nbr))
        self.thread_ip4 = threading.Thread(target = self.listening, args=(self.sock_ip4,))
        self.thread_ip6 = threading.Thread(target = self.listening, args=(self.sock_ip6,))
        self.thread_ip4.start()
        self.thread_ip4.join()
        self.thread_ip6.start()
        self.thread_ip6.join()


    def listening(self, sock, syn_flag = False):

        if (sock == None):
            return

        sock.setblocking(False)
        incoming = api.listen(self, sock)
        syn_flag = incoming[0]

        #Discard any extraneous packets where syn_flag is false
        if (syn_flag) is False:
            return
        sock.setblocking(True)

        sock.settimeout(2)
        self.sock = sock
        self.client_address = incoming[1][1]
        self.isConnected = api.accept(self.sock, self.client_address, self)
        if not self.isConnected:
            return
        self.connected.set()
        sock.settimeout(None)
        print()
        self.ack_nbr = 0
        self.seq_nbr = 0
        self.last_acked = 0
        logging.info('Client with ' + str(self.client_address) + ' has been connected.')
        logging.debug('Server Ack Nbr: ' + str(self.ack_nbr) + '; Server Seq Nbr: ' + str(self.seq_nbr))
        input_line = "--->"
        print(input_line, end="", flush=True)


    def Server_run(self):
        logging.debug('Server active listening thread has spawn')
        while 1:
            if not self.connected.is_set():
                self.listen()
            else:
                incoming = api.receive(self, self.sock, decode=False)
                if incoming is not None:
                    message = incoming[0]
                    crp_header = CRPHeader.bytes_to_header(message[0:api.HEADER_SIZE], api.HEADER_SIZE).split(',')
                    body = message[api.HEADER_SIZE:api.MAX_SEGMENT_SIZE].decode().split(';')

                    if (len(body) <= 1):
                        self.ack_nbr -= 1
                        self.logger.debug("Leftover packet from prev. transmission received. Discarding...")
                        continue
                    request = body[1].strip()
                    logging.debug("Incoming " + request + " request.")

                    # Handle GET Request
                    if request == api.fta.header.get.value:
                        # Send an ack for the initial request
                        api.send_ack(self, message, self.sock, self.client_address)
                        cli_window = int(crp_header[5])
                        filename = body[2].strip()
                        logging.info('GET operation has been received with ' + filename + '.')
                        content = self.check_valid_file(filename)
                        if content is not None:
                            logging.info('File validation was successful.')
                        else:
                            logging.info('File validation was not successful.')
                        api.fta.get_server(message, content, self.sock, self.client_address, self, cli_window)
                        self.seq_nbr = 0
                        self.ack_nbr = 0
                        self.last_acked = 0

                    # Handle POST Request
                    elif request == api.fta.header.post.value:
                        # Send an ack for the initial request
                        api.send_ack(self, message, self.sock, self.client_address)
                        filename = body[2].strip()
                        response = api.fta.post_server(self.sock, self.client_address, self, message)
                        if (response == None):
                            logging.info("Post was unsuccessful.")
                            self.seq_nbr = 0
                            self.ack_nbr = 0
                            self.last_acked = 0
                            continue
                        status = response[0].strip()
                        file_content = response[1]
                        if status == api.fta.err_codes.ok.value:
                            if self.upload_file(filename, file_content) :
                                logging.info("File " + filename + " uploaded successfully.")
                            else:
                                logging.info("File " + filename + " not uploaded successfully.")

                        else:
                            logging.info("Error in file transmission.")
                        self.seq_nbr = 0
                        self.ack_nbr = 0
                        self.last_acked = 0

                    # Handle CLOSE(FIN) Request
                    elif request == api.fta.header.close.value:
                        logging.debug("CLOSE(FIN) request has been received.")
                        self.close(incoming)
                    else:
                        logging.info(request + " is not a supported operation.")

                else:
                    continue

    def graceful_close(self):
        logging.info("Attempting graceful shutdown.")


        if (self.isConnected or self.isConnected == "True"):
            logging.info("Attempting to disconnect from client.")
            api.close_sender_server(self, self.sock, self.client_address)

            #timeout for while loop, unnecessary
            timeout = time.time() +  api.MAX_RETRIES_SAME_PACKET
            while (self.isConnected):
                time.sleep(1)
        logging.info("Shutting down successfully.")
        sys.exit(1)

    def close(self, incoming):
        # Check to see if the incoming packet has ACK and FIN, or just FIN
        received_header = incoming[0]
        received_header = CRPHeader.bytes_to_header(received_header, api.HEADER_SIZE)
        temp = received_header
        received_header = received_header.split(',')
        # ACK and FIN -> send a ACK and terminate
        if (received_header[2] == 'True') and (received_header[4] == 'True'):
            crp_header = CRPHeader()
            crp_header.ack_flag = True
            current_time = time.time()

            ending = current_time + api.MAX_RETRIES
            while time.time() < ending:
                '''send multiple ACKS to client'''
                self.logger.debug("Server sending ACK to client.")
                api.send(self, self.sock, crp_header.pack(), self.client_address, self)
                self.seq_nbr -= 1
                time.sleep(1)

            self.sock.close()
            logging.info('Server has successfully closed.')
            os._exit(1)

        # FIN -> send a FIN and ACK and wait for ACK
        if api.check_and_close_receive(self, temp, self.sock, self.client_address):
            logging.info("Disconnected from client.")
            input_line = "--->"
            self.connected.clear()
            print(input_line, end="", flush=True)
            self.init()

    def check_valid_file(self, filename):
        """Returns file content in bytes, else none if file does not exist"""

        logging.info('Validating the filename: ' + filename)
        try:
            with open(filename, mode='rb') as file:
                content = file.read()
            return content
        except:
            logging.info("File with name " + filename + " was not found.")
            return None

    def upload_file(self, filename, content):

        # This is just for testing purposes
        # NOTE: Remove before submission
        if "tests/" in filename:
            filename = filename[6:]
        try:
            with open('uploads/' + filename, mode='wb') as file:
                file.write(content)
            return True
        except:
            logging.info('Could not upload the file.')
            return False



    # end of class

# create a parser for port number
parser = argparse.ArgumentParser(description="Establish a server.")
parser.add_argument(dest='server_port', help='server port number')
parser.add_argument('-d', dest='debug', const=True, action='store_const', default=False)

# parse command line arguments
args = parser.parse_args()
server_port = args.server_port
if args.debug is True:
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


serv = Server(server_port, logging.getLogger())




