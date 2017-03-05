import argparse, api, sys, socket, logging, threading, os, CRPHeader

TIMEOUT_S = 2

class client():
    sock = None
    isConnected = False
    server_address = -1
    window = 1
    window_other = 1
    '''reset these after close'''
    seq_nbr = 0
    ack_nbr = 0
    '''family does not change'''
    family = None
    last_acked = 0
    logger = None
    listening_thread = None
    user_input = None
    lock = None

    def __init__(self, address, logger):
        self.logger = logger
        self.user_input = threading.Event()
        self.user_input.clear()
        self.lock = threading.Lock()
        self.spawn_thread()
        # Create UDP socket for the client
        addr_info = self.ip_addr_type((address))
        self.server_address = addr_info[1]
        self.family = addr_info[0]
        self.sock = api.create_socket(family = addr_info[0])
        logging.info('Client socket has been created.')

    def spawn_thread(self):
        self.listening_thread = threading.Thread(target= self.listening)

    def ip_addr_type(self, address):
        """Determines if IPv4/IPv6"""
        info = socket.getaddrinfo(address, int(port))
        family = info[0][0]
        sockaddr = info[0][4]
        if family == socket.AF_INET:
            logging.debug('IPv4 address')
            return family, sockaddr
        else:
            logging.debug('IPv6 address')
            logging.debug((sockaddr[0], sockaddr[1]))
            return family, (sockaddr[0], sockaddr[1] + 1)

    def connect(self, address, port):
        if int(port) < 0 or int(port) > 65535:
            logging.info("Port number is invalid.")
            sys.exit(0)
        self.sock.settimeout(TIMEOUT_S)
        self.isConnected = api.connect(self.sock, self.server_address, self)
        if (self.isConnected):
            self.seq_nbr = 0
            self.ack_nbr = 0
            self.last_acked = 0
            logging.info('Client socket has connected to server with IP: '\
                          + str(self.server_address[0]) + ' port: ' + str(self.server_address[1]))
            logging.debug('Client Ack Nbr: ' + str(self.ack_nbr) + '; Client Seq Nbr: ' + str(self.seq_nbr))
        else:
            logging.info('Client did not successfully connect')

    def get(self, filename):
        response = api.fta.get_client(filename, self.sock, self.server_address, self)
        self.seq_nbr = 0
        self.ack_nbr = 0
        self.last_acked = 0
        if response == None:
            logging.info("GET was unsuccessful")
            return
        status = response[1]
        if status != api.fta.err_codes.bad.value:
            logging.info('Downloaded ' + filename + ' successfully.')

            # This is just for testing purposes
            # NOTE: Remove before submission
            if "tests/" in filename:
                filename = filename[6:]

            filename = "downloads/" + filename
            content = response[0]
            try:
                with open(filename, mode="wb") as file:
                    file.write(content)
            except Exception as e:
                logging.info("Error occurred while downloading file.")
                logging.info(e)
        else:
            logging.info("File with name " + filename + " was not found.")

    # TODO: Handle printing and everything else
    def post(self, filename):
        content = ''

        try:
            with open(filename, mode="rb") as file:
                content = file.read()
        except Exception as e:
            logging.info("Could not find the specified file " + filename)
            logging.info(e)
            return
        result = api.fta.post_client(filename, self.sock, self.server_address, content, self)
        if result is not False:
            logging.info('Posting operation has completed.')
        else:
            logging.info('POST operation failed with ' + filename)
        self.seq_nbr = 0
        self.ack_nbr = 0
        self.last_acked = 0

    def listening(self):
        self.lock.acquire()
        while True and not self.user_input.is_set():
            if self.isConnected:
                try:
                    self.sock.settimeout(TIMEOUT_S)
                    response = self.sock.recv(10 * api.MAX_SEGMENT_SIZE)
                    #Get rid of any extraneous packets from previous transmission
                    temp = response[0:api.HEADER_SIZE]
                    temp_decoded = CRPHeader.CRPHeader.bytes_to_header(response, api.HEADER_SIZE)
                    temp_split = temp_decoded.split(',')
                    incoming_seq_nbr = int(temp_split[0])
                    if incoming_seq_nbr != 0:
                        self.logger.debug("Leftover packet from prev. transmission received(1). Discarding...")
                        continue

                    body = response[api.HEADER_SIZE:api.MAX_SEGMENT_SIZE].decode()
                    body_split = body.split(';')
                    if (len(body_split) <= 1):
                        self.logger.debug("Leftover packet from prev. transmission received(2). Discarding...")
                        continue

                    #handle FIN request from server
                    response = temp_decoded + body
                    if api.check_and_close_receive(self, response, self.sock, self.server_address):
                        print("Server has disconnected/terminated.\n--->", end='',flush=True)
                        data = ''
                        self.sock.close()
                        self.sock = api.create_socket(family = self.family)
                        self.seq_nbr = 0
                        self.ack_nbr = 0
                        self.last_acked = 0
                        self.isConnected = False
                    else:
                        logging.info("Disconnect from server failed.")
                except socket.timeout:
                    continue
            else:
                break
        self.lock.release()


    #end of class



# add command line arguments to the parser
parser = argparse.ArgumentParser(description = "Connects to sensor server and sends information.")
parser.add_argument(dest='hostname', help='hostname')
parser.add_argument(dest='port', help='port')
parser.add_argument('-d', dest='debug', const=True, action='store_const', default=False)


# parse command line arguments
args = parser.parse_args()
hostname = args.hostname
port = args.port
if args.debug is True:
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

crp_header = CRPHeader.CRPHeader()
crp_header= crp_header.pack()
cli = client(hostname, logging.getLogger())


logging.info('Waiting for user input.')
while (1):
    try:
        cli.spawn_thread()
        cli.listening_thread.start()
        user_input = input("--->").strip().split()
        cli.user_input.set()
        cli.lock.acquire()
        command = user_input[0]
        if command == "connect":
            if cli.isConnected:
                logging.info("Client is already connected.")
            else:
                logging.debug('Attempting to connect to the server.')
                try:
                    cli.connect(hostname, port)
                except ConnectionRefusedError:
                    logging.info('Connection was refused. Please check the server.')
                    sys.exit(1)
        elif command == "get":
            if not cli.isConnected:
                logging.info("Client is not connected.")
            elif len(user_input) != 2:
                logging.info("Usage: GET [filename]")
            else:
                filename = user_input[1]
                logging.debug('GET request with ' + filename + ' has started.')
                cli.get(filename)
        elif command == "post":
            if not cli.isConnected:
                logging.info("Client is not connected.")
            elif len(user_input) != 2:
                logging.info("Usage: POST [filename]")
            else:
                filename = user_input[1]
                logging.debug('POST request with ' + filename + ' has started.')
                cli.post(filename)
        elif command == "window":
            if len(user_input) != 2:
                logging.info("Usage: window [size as INT]")
            else:
                isInt = False
                try:
                    user_input[1] = int(user_input[1])
                    isInt = True
                except:
                    logging.info("Usage: window [size as INT]")

                if isInt:
                    if (user_input[1]) < 1:
                        logging.info('Invalid window size given.')
                    else :
                        cli.window = int(user_input[1])
                        logging.info("Client window updated.")

        elif command == "disconnect":
            if not cli.isConnected:
                logging.info("Client is not connected.")
            else:
                if api.close_sender_client(cli, cli.sock, cli.server_address):
                    cli.isConnected = False
                    logging.info('Client has been disconnected')
                else:
                    logging.info("Disconnect failed. Try again")
        elif command == 'terminate':
            if not cli.isConnected:
                logging.info('Client has been terminated')
                sys.exit(1)
            else:
                if api.close_sender_client(cli, cli.sock, cli.server_address):
                    cli.isConnected = False
                    logging.info('Client has been terminated')
                    sys.exit(1)
                else:
                    logging.info("Disconnect failed. Try again")
        else:
            logging.info("Input of " + command + " is not an supported operation.")
        cli.user_input.clear()
        cli.lock.release()
    except KeyboardInterrupt:
        print()
        logging.info("Attempting graceful shutdown.")
        cli.user_input.set()
        cli.lock.acquire()
        if (cli.isConnected):
            if api.close_sender_client(cli, cli.sock, cli.server_address):
                logging.info('Client has been disconnected.')
            else:
                logging.info("Disconnect failed. Server might still be connected.")
        logging.info("Shutting down successfully.")
        os._exit(1)



