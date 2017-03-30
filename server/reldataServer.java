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
 * @author Yufeng Wang, Mingjun Xie
 * @version 1.0
 * the UDP Server that read the suspicious_words file, receive msg file from client, 
 * calculate the spam score and pass results back to the client
 * Call: java smsengine [Portnumber] [suspicious words] to initiate server
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

  public Window getWindow() {
    return this.recvWindow;
  }

  public void refreshWindow(int size) {
    this.recvWindow = new Window(size);
  }

  //TODO need to check time instance
  private static void checktimeout(Window win) {
    long curtime = System.currentTimeMillis();
    int start = win.start;
    int end = win.end;
    int seqsize = win.getSequenceSize();
    System.out.println("time out checking!!!");
    if (start < end) {
      for (int i = start; i < end && win.getpacket(i) != null; i++) {
        check_resend(win, curtime, i);
      }
    } else {
      for (int i = start; i < seqsize && win.getpacket(i) != null; i++) {
        check_resend(win, curtime, i);
      }

      for (int i = 0; i < end && win.getpacket(i) != null; i++) {
        check_resend(win, curtime, i);
      }
    }
    return;
  }

  // helper method for timeout 
  private static void check_resend(Window win,long curtime,int i) {
    Long temp_time = win.gettimer(i);
    DatagramPacket cur_pkt = win.getpacket(i);
    boolean acked = win.getack(i);

    if (temp_time == null || cur_pkt == null) {
      System.out.println("pkt received");
      return;
    }
    if (curtime - temp_time >= 200 & !acked) {
      System.out.println("Packet Resend: (ackNum)" + i);
      try {
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

  private static void handshake(int seqNum,int ackNum,boolean ackFlag,boolean synFlag,boolean finFlag,int rcvw,String data, InetAddress client_addr, int client_port, DatagramSocket serverSocket) {
      // send an syn&ack packet back to the client
      try {
          DatagramPacket reply = createReplyPacket(seqNum, ackNum, ackFlag, synFlag, finFlag, rcvw, data, client_addr, client_port);
          serverSocket.send(reply);
          if (finFlag) {
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
    } else {
        return "wtf";
    }

  }

//////////////////////////////////////////main////////////////////////////////////////////
    public static void main (String[] args)  throws IOException{
      reldataServer server = new reldataServer(args);
      serverSocket.setSoTimeout(1000);
      Window recvWindow =  server.getWindow();
      boolean connected = false;
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

            System.out.println("rcvw: " + rcvw);
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
            if (!connected & state != "ConnRequest") {
                System.out.println("Server not connect with client");
                continue;
            }
            // if the receive window is full, the server only receive ack packets
            if (onlyack & state != "AckRecvd") {
              System.out.println("window full and receive non-ack");
              checktimeout(recvWindow);
              continue;
            }
            checktimeout(recvWindow);
            switch(state) {
                case "ConnRequest":
                    // here the seqNum of reply = acknum of the client
                    // the acknum of reply = seqNum + dataLen
                    // we want to reply ack = true and syn = true, fin = false;
                    handshake(ackNum, 0, true, true, false,recvWindowSize, "Hello", client_addr, client_port, serverSocket);
                    lastRcvTime = System.currentTimeMillis();
                    connected = true;
                    System.out.println("Connect with client!");
                    continue;
                case "TransferData":
                    int server_cs = PacketProcessor.makechecksum(clientdata, clientdata.length());
                    if (server_cs == checksum) {
                      sendData(recvWindow,seqNum, seqNum, true, false, false, recvWindowSize, clientdata.toUpperCase(), client_addr, client_port, serverSocket);
                    } else {
                      System.out.println("server checksum: " + server_cs);
                      System.out.println("client checksum: " + checksum);
                      System.out.println("Checksum error");
                      return;
                    }

                    // update last packet received
                    recvWindow.setLastAck(seqNum);
                    int lastAck = recvWindow.lastack();
                    System.out.println("Last acked num" + lastAck);
                    lastRcvTime = System.currentTimeMillis();
                    System.out.println("lastrcvtime update:" + lastRcvTime);
                    continue;

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
                    continue;
                case "Disconnect":
                    handshake(ackNum,0, true, false, true, recvWindowSize, "Bye", client_addr, client_port, serverSocket);
                    lastRcvTime = null;
                    connected = false;
                    continue;
            }

          } catch (SocketTimeoutException sot) {
              // check if the client site has crashed
              currentTime = System.currentTimeMillis();
              // System.out.println("current time : " + currentTime);
              // if (lastRcvTime != null) {
              //   System.out.println("last rcv time: " + lastRcvTime);
              // }

              boolean client_crashed = false;
              if (recvWindow.hasUnackedPkt()) {
                if (lastRcvTime != null && currentTime - lastRcvTime > 10000) {
                  System.out.println("The client site has crashed, please restart the client program!");
                  client_crashed = true;
                }
              } else {
                if (lastRcvTime != null && currentTime - lastRcvTime > 30000) {
                  System.out.println("The client site has crashed, please restart the client program!");
                  client_crashed = true;
                }
              }

              if (client_crashed) {
                  System.out.println("Refresh window.");
                  int recvWindowSize = recvWindow.getwindowsize();
                  server.refreshWindow(recvWindowSize);
                  lastRcvTime = null;
                  client_crashed = false;
                  connected = false;
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