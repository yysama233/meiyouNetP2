import java.net.*;
import java.io.*;
import java.net.DatagramPacket;
import java.util.Scanner;
import java.util.Iterator;
import java.net.SocketException;
import java.util.List;
import java.util.ArrayList;
import java.util.Arrays;
import java.math.*;


/**
 * @author Yufeng Wang, Mingjun Xie, Yang Yang
 * @version 1.0
 * the UDP Server that reads the data from client, capitalizes all the data and transfers back to client.
 * Call: java reldataServer [Portnumber] to initiate the server
 */
public class reldataServer {
  private static PacketProcessor pp = new PacketProcessor();
  private static int portnumber;
  private static DatagramSocket serverSocket;
  private static DatagramPacket received_packet;
  private static Window recvWindow;
  private static int lastAck = 0;
  private static Long lastRcvTime;
  private static Long currentTime;
  private static int TIMEOUT = 100; // 100ms
  /**
   ** Server Constructor
   **/
  public reldataServer(String args[]) {
    //Check command line input length
    if (args.length != 2) {
      System.out.println("Invalid input."
       + " Sample input would be java Server <port number> <receive window size>");
         return;
    }

    //Check the validity of port number input
    try {
      this.portnumber = Integer.parseInt(args[0]);
    } catch (NumberFormatException e) {
      System.out.println("Invalid port number is given.");
      return;
    }

    try {
      int recvWindowSize = Integer.parseInt(args[1]);
      this.recvWindow = new Window(recvWindowSize);
    } catch (NumberFormatException e) {
      System.out.println("Invalid recvWindowSize is given.");
      return;
    }

    if (portnumber <= 1024 || portnumber > 65536) {
      System.out.println("Port number should be between 1024 and 65536.");
      return;
    }

    try {
      this.serverSocket = new DatagramSocket(portnumber);
      System.out.println("serverSocket is created, waiting for response");
    } catch (SocketException e) {
      System.out.println(e.getMessage());
    }
    currentTime = System.currentTimeMillis();
    lastRcvTime = null;
  }

  /**
  ** get window
  ** @param null
  ** @return this.recvWindow
  ** the function returns a window instance
  **/
  public Window getWindow() {
    return this.recvWindow;
  }
  /**
  * @param size, default window size
  * @return defaulted window
  * the function refreshes the window after disconnection
  **/
  public void refreshWindow(int size) {
    this.recvWindow = new Window(size);
    System.out.println("new window start: " + this.recvWindow.start);
    System.out.println("new window end: " + this.recvWindow.end);
  }
  /**
  ** @param win, window packet buffer
  ** the function checkes any possible time-out packet and resend in case. 
  **/
  //TODO need to check time instance
  private static void checktimeout(Window win) {
    long curtime = System.currentTimeMillis();
    int start = win.start;
    int end = win.end;
    int seqsize = win.getSequenceSize();
    System.out.println("time out checking!!!");
    if (start < end) {
      for (int i = start; i < end; i++) {
        check_resend(win, curtime, i);
      }
    } else {
      for (int i = start; i < seqsize; i++) {
        check_resend(win, curtime, i);
      }

      for (int i = 0; i < end; i++) {
        check_resend(win, curtime, i);
      }
    }
    return;
  }
  /**
  * @param win, window packet buffer
  * @param curtime, current time stamp in checking the timeout cases
  * @param i, specific packet index     
  * the function checkes timeout in specific packet buffer index
  **/
  // helper method for timeout 
  private static void check_resend(Window win,long curtime,int i) {
    Long temp_time = win.gettimer(i);
    DatagramPacket cur_pkt = win.getpacket(i);
    boolean acked = win.getack(i);
    if (acked) {
        System.out.println("pkt acked already: " + i);
    }

    if (temp_time == null || cur_pkt == null) {
      return;
    } else {
        System.out.println("pke not acked yet: " + i);
    }

    if ((curtime - temp_time) >= 2000) {
      System.out.println("Packet Resend: (ackNum)" + i);
      try {
        win.settimer(i, curtime);
        serverSocket.send(cur_pkt);
      } catch (IOException e) {
        System.out.println("IOException exists!");
      } catch (NullPointerException e) {
        System.out.println("Something wrong with packet!");
      } catch (Exception e) {
        System.out.println("Other errors when resending packets.");
      }

    }
    return;
  }
  /**
  ** createreplypacket
  ** @param seq_num, the sequence number for the packet header
  ** @param ack_num, the acknowledgement number for the packet header
  ** @param data_len, the data length for the data
  ** @param checksum, the checksum value of the data for comparison in the sneder side
  ** @param ack_flag, indicating whether the packet is a acknowledgement packet
  ** @param syn_flag, indicating whether the packet is a connection setup packet    
  ** @param fin_flag, indicating whether the packet is a connection termination packet    
  ** @param rcws, the window size from the sender side, if rcws falls to zero, the receiver will pause data transferring
  ** @param data, actual data to be packed in the packet
  ** @param client_addr, the client's IP address
  ** @param client_port, the client's port number
  ** @return the Datagram packet to be sent to the client side
  * This function that packs parameters into a single packet and returns as the byte-stream data to the receiver by calling PacketProcessor
  **/
  private static DatagramPacket createReplyPacket(int seqNum,int ackNum, boolean ackFlag,boolean synFlag,boolean finFlag,int rcvw,String data ,InetAddress client_addr, int client_port) throws IOException, NullPointerException{
      DatagramPacket sent_packet = new DatagramPacket(new byte[1000], 1000, client_addr, client_port);
      int dataLen = data.length();
      System.out.println("-------------------------------Sent--------------------------------");
      System.out.println("seqNum: " + seqNum);
      System.out.println("ackNum: " + ackNum);
      System.out.println("ackFlag: " + ackFlag);
      System.out.println("synFlag: " + synFlag);
      System.out.println("finFlag: " + finFlag);
      System.out.println("dataLen:" + dataLen);
      System.out.println("data: " + data);
      int checksum = PacketProcessor.makechecksum(data,dataLen);
      System.out.println("checksum: " + checksum);
      byte[] reply = PacketProcessor.pack(seqNum, ackNum, dataLen, checksum, ackFlag, synFlag, finFlag, rcvw, data);

      sent_packet.setData(reply);
      sent_packet.setLength(reply.length);
      return sent_packet;
  }

  /**
  ** @param seq_num, the sequence number for the packet header
  ** @param ack_num, the acknowledgement number for the packet header
  ** @param data_len, the data length for the data
  ** @param checksum, the checksum value of the data for comparison in the sneder side
  ** @param ack_flag, indicating whether the packet is a acknowledgement packet
  ** @param syn_flag, indicating whether the packet is a connection setup packet    
  ** @param fin_flag, indicating whether the packet is a connection termination packet    
  ** @param rcws, the window size from the sender side, if rcws falls to zero, the receiver will pause data transferring
  ** @param data, actual data to be packed in the packet
  ** @param client_addr, the client's IP address
  ** @param client_port, the client's port number
  ** @param server_socket, the socket in server that is sending out the packet
  ** @return the Datagram packet to be sent to the client side
  * This function establishes the reliable data transfer with the client by completing the handshake process
  **/

  private static void handshake(int seqNum,int ackNum,boolean ackFlag,boolean synFlag,boolean finFlag,int rcvw,String data, InetAddress client_addr, int client_port, DatagramSocket serverSocket) {
      // send an syn&ack packet back to the client
      try {
          DatagramPacket reply = createReplyPacket(seqNum, ackNum, ackFlag, synFlag, finFlag, rcvw, data, client_addr, client_port);
          serverSocket.send(reply);
          if (ackFlag && finFlag && synFlag) {
            System.out.println("Finish this transfer! Waiting for new message from client.");
          } else if (finFlag) {
            System.out.println("Fin&Ack sent! Connection with client" + client_addr +"shut down.");
          } else {
            System.out.println("Syn&Ack sent! Connection setup.");
          }

      } catch (IOException e) {
        System.out.println("Connection message sent failure." + e);
      } catch (Exception e) {
        System.out.println("Other Connection error" + e);
      }
  }
 /**
  * @param seq_num, the sequence number for the packet header
  * @param ack_num, the acknowledgement number for the packet header
  * @param data_len, the data length for the data
  * @param checksum, the checksum value of the data for comparison in the sneder side
  * @param ack_flag, indicating whether the packet is a acknowledgement packet
  * @param syn_flag, indicating whether the packet is a connection setup packet    
  * @param fin_flag, indicating whether the packet is a connection termination packet    
  * @param rcws, the window size from the sender side, if rcws falls to zero, the receiver will pause data transferring
  * @param data, actual data to be packed in the packet
  * @param client_addr, the client's IP address
  * @param client_port, the client's port number
  * @param server_socket, the socket in server that is sending out the packet
  * @return the Datagram packet to be sent to the client side
  * This function sends out the data in data transfer state
  **/
  private static void sendData(Window win, int seqNum,int ackNum,boolean ackFlag,boolean synFlag,boolean finFlag,int rcvw,String data, InetAddress client_addr, int client_port, DatagramSocket serverSocket) {

    try {
      DatagramPacket reply_packet = createReplyPacket(seqNum, ackNum, ackFlag, synFlag, finFlag, rcvw, data, client_addr, client_port);
      // pktArray.add(reply_packet);
      // timeArray.add(System.currentTimeMillis());
      // lastAck = (lastAck + 1) % sequenceSize;
      serverSocket.send(reply_packet);
      win.addpacket(seqNum, reply_packet);
      System.out.println("data sent");
    } catch (IOException e) {
      System.out.println("Exeception found: data sent failure." + e);
    } catch (NullPointerException e) {
      System.out.println("Something wrong with the packet." + e);
    } catch (Exception e) {
      System.out.println("Other error when sending data." + e);
    }
  }
  /**
  * @param ack_flag, indicating whether the packet is a acknowledgement packet
  * @param syn_flag, indicating whether the packet is a connection setup packet    
  * @param fin_flag, indicating whether the packet is a connection termination packet    
  * @param data, actual data to be packed in the packet
  * @return the state of server
  * This function checks the state of the server.
  **/
  private static String findState(boolean synFlag, boolean ackFlag, boolean finFlag, String data) {
    if (synFlag && !ackFlag && !finFlag) {
        return "ConnRequest";
        // after this case all other cases are yy and can be changed as you wish!
    } else if (!synFlag && ackFlag && !finFlag) {
          return "AckRecvd";
    } else if (finFlag && !synFlag && !ackFlag) {
        return "Disconnect";
    } else if (!finFlag && !synFlag && !ackFlag && data.length() != 0){
        return "TransferData";
    } else if (synFlag && ackFlag && finFlag) {
        return "FinishOneTransfer";
    } else {
        return "wtf";
    }

  }

//////////////////////////////////////////main////////////////////////////////////////////
    public static void main (String[] args)  throws IOException{
      reldataServer server = new reldataServer(args);
      serverSocket.setSoTimeout(TIMEOUT);
      boolean connected = false;
      Window recvWindow = server.getWindow();
      try {
        //initiate the server socket
        boolean running = true;
        while (running) {

          //read and decode data from the client
          System.out.println("Server running...");
          boolean onlyack = false;

          if (recvWindow.isfull()) {
            System.out.println("server receive window is full!!!");
            onlyack = true;
          }

          try {
            byte[] buf = new byte[1000];
            received_packet = new DatagramPacket(buf, buf.length);
            serverSocket.receive(received_packet);
            InetAddress client_addr = received_packet.getAddress();
            int client_port = received_packet.getPort();
            byte[] recc = received_packet.getData();

            System.out.println("-----------------------Received -----------------------");
            System.out.println("length of packet" + recc.length);
            byte[] header = Arrays.copyOfRange(recc, 0, 12);
            System.out.println("rawdata:" + recc);

            int seqNum = PacketProcessor.getIntSeqNum(header);
            int ackNum = PacketProcessor.getIntAckNum(header);
            int dataLen = PacketProcessor.getDataLength(header);
            int checksum = PacketProcessor.getCheckSum(header);

            System.out.println("seqNum: " + seqNum);
            System.out.println("ackNum: " + ackNum);
            System.out.println("dataLen: " + dataLen);
            System.out.println("checksum: " + checksum);

            boolean synFlag = PacketProcessor.getSYNFlag(header);
            boolean ackFlag = PacketProcessor.getACKFlag(header);
            boolean finFlag = PacketProcessor.getFINFlag(header);
            System.out.println("ackFlag: " + ackFlag);
            System.out.println("synFlag: " + synFlag);
            System.out.println("finFlag: " + finFlag);

            int rcvw = PacketProcessor.getrcvw(header);

            System.out.println("client free window: " + rcvw);
            int recvWindowSize = recvWindow.getfreewindow();
            System.out.println("server free window: " + recvWindowSize);
            // if rcvw == 0, then the receiver's window is full of packets
            if (rcvw == 0) {
                checktimeout(recvWindow);
                continue;
            }

            byte[] data = Arrays.copyOfRange(recc, 12, recc.length);
            String clientdata = new String(data, 0, dataLen > data.length ? data.length: dataLen);
            System.out.println("data.length:" + data.length);
            System.out.println("Received Data: " + clientdata);
            System.out.println("client dataLen:" + clientdata.length());

            // Find state of the client to decide how to reply the client
            String state = findState(synFlag, ackFlag, finFlag, clientdata);
            System.out.println("Current State: " + state);

            // check if connected with client, if not connected then we reject any other packet except for connect request
            if (!connected && state != "ConnRequest" && state != "Disconnect") {
                System.out.println("Server not connect with client");
                continue;
            }

            // if the receive window is full, the server only receive ack packets
            if (onlyack && state != "AckRecvd") {
              System.out.println("window full and receive non-ack");
              checktimeout(recvWindow);
              continue;
            }

            switch(state) {
                case "ConnRequest":
                    // here the seqNum of reply = acknum of the client
                    // the acknum of reply = seqNum + dataLen
                    // we want to reply ack = true and syn = true, fin = false;
                    handshake(ackNum, 0, true, true, false, recvWindowSize, "Hello", client_addr, client_port, serverSocket);
                    lastRcvTime = System.currentTimeMillis();
                    connected = true;
                    System.out.println("Connect with client!");
                    break;

                case "TransferData":
                    int server_cs = PacketProcessor.makechecksum(clientdata, clientdata.length());
                    if (server_cs == checksum) {
                      sendData(recvWindow,seqNum, seqNum, true, false, false, recvWindowSize, clientdata.toUpperCase(), client_addr, client_port, serverSocket);
                    } else {
                      System.out.println("server checksum: " + server_cs);
                      System.out.println("client checksum: " + checksum);
                      System.out.println("Checksum error");
                    }

                    // update last packet received
                    recvWindow.setLastAck(seqNum);
                    int lastAck = recvWindow.lastack();
                    System.out.println("Last server sent acked num" + lastAck);
                    lastRcvTime = System.currentTimeMillis();
                    System.out.println("lastrcvtime update:" + lastRcvTime);
                    break;

                case "AckRecvd":
                    // mark acked
                    try {
                      recvWindow.ackpacket(ackNum);
                      recvWindowSize = recvWindow.getfreewindow();
                      System.out.println("server free window: " + recvWindowSize);
                    } catch (Exception iooe) {
                      System.out.println("Error occurs during ack packet and moving window.");
                    }
                    lastRcvTime = System.currentTimeMillis();
                    System.out.println("lastrcvtime update:" + lastRcvTime);
                    break;
                case "FinishOneTransfer":
                    //send ack to mean finished
                    handshake(ackNum, ackNum, true, true, true, recvWindowSize, "Haode", client_addr, client_port, serverSocket);
                    recvWindow.prepareNextTransfer(ackNum);
                    continue;
                case "Disconnect":
                    handshake(ackNum,0, true, false, true, recvWindowSize, "Bye", client_addr, client_port, serverSocket);
                    recvWindowSize = recvWindow.getwindowsize();
                    server.refreshWindow(recvWindowSize);
                    recvWindow = server.getWindow();
                    lastRcvTime = null;
                    connected = false;
                    continue;
            }
            checktimeout(recvWindow);
          } catch (SocketTimeoutException sot) {
              // check if the client site has crashed
              currentTime = System.currentTimeMillis();


              boolean client_crashed = false;
              if (recvWindow.hasUnackedPkt()) {
                if (lastRcvTime != null && currentTime - lastRcvTime > 15000) {
                  System.out.println("The client site has crashed, please restart the client program!");
                  client_crashed = true;
                }
              } else {
                if (lastRcvTime != null && currentTime - lastRcvTime > 40000) {
                  System.out.println("The client site has crashed, please restart the client program!");
                  client_crashed = true;
                }
              }
              // if crashed refresh window
              if (client_crashed) {
                  System.out.println("Refresh window.");
                  int recvWindowSize = recvWindow.getwindowsize();
                  server.refreshWindow(recvWindowSize);
                  recvWindow = server.getWindow();

                  lastRcvTime = null;
                  client_crashed = false;
                  connected = false;
              } else {
                if (connected) {
                    checktimeout(recvWindow);
                }
              }

              continue;
          }
        }
        serverSocket.close();
      } catch (NullPointerException e) {
        System.out.println("Server Crash: " + e);
      } catch (Exception e) {
        System.out.println("Server crashes with other errors: " + e);
      }

  }
}