import java.net.*;
import java.io.*;
<<<<<<< HEAD
<<<<<<< Updated upstream
=======
>>>>>>> master
import java.net.DatagramPacket;
import java.util.Scanner;
import java.util.Iterator;
import java.net.SocketException;
<<<<<<< HEAD
import java.util.ArrayList;
import java.util.Arrays;
import java.math.BigInteger;

public class Server {
  private static int portnumber;
  private static DatagramSocket serversocket;
  private static DatagramPacket received_packet;
  private static PacketProcessor pp = new PacketProcessor();
  private static int sequenceSize = pow(2,16);
  private static int windowSize = sequenceSize/2;
  private static boolean[] sendSeqArray = new boolean[windowSize];
  private static int head = 0;
  private static int end = windowSize;
  private static int lastAck = 0;
  private static ArrayList<Long> timeArray;
  private static ArrayList<DatagramPacket> pktArray;

  private static DatagramPacket creatReplyPacket(int seqNum,int ackNum, boolean ackFlag,boolean synFlag,boolean finFlag,int rcvw,String data ,InetAddress client_addr, int client_port) throws Exception{
=======
import java.util.Arrays;
import java.util.Arraylist;

public class Server {
	int portnumber;
	DatagramSocket serversocket;
	DatagramPacket received_packet;
	PacketProcessor pp = new PacketProcessor();
  int sequenceSize = pow(2,16);
  int windowSize = sequenceSize/2;
  boolean[] sendSeqArray = new boolean[windowSize];
  initializeWindow(sendSeqArray);
  int head = 0;
  int end = windowSize;
  int lastAck = 0;
  ArrayList<long> timeArray;
  ArrayList<DatagramPacket> pktArray;

  private static void initializeWindow(boolean[] array) {
    for (int i = 0; i < array.length; i++) {
      array[i] = false;
    }
  }

	private static DatagramPacket creatReplyPacket(int seqNum,int ackNum, boolean ackFlag,boolean synFlag,boolean finFlag,int rcvw,String data ,InetAddress client_addr, int client_port) throws Exception{
>>>>>>> Stashed changes
    DatagramPacket sent_packet = new DatagramPacket(new byte[1024],1024,client_addr,client_port);
    int dataLen = data.length();
    int checksum = PacketProcessor.makechecksum(data);
    byte[] reply = PacketProcessor.pack(seqNum, ackNum, dataLen, checksum, ackFlag, synFlag, finFlag, rcvw, data);
    sent_packet.setData(reply);
    sent_packet.setLength(reply.length);
    return sent_packet;
  }

  private static void handshake(int seqNum,int ackNum,boolean ackFlag,boolean synFlag,boolean finFlag,int rcvw,String data, InetAddress client_addr, int client_port, DatagramSocket serverSocket) {
  // send an syn&ack packet back to the client
    try {
      System.out.println("ackFlag: " + ackFlag);
      System.out.println("synFlag: " + synFlag);
      System.out.println("finFlag: " + finFlag);
      DatagramPacket reply_packet = creatReplyPacket(seqNum, ackNum, ackFlag, synFlag, finFlag, rcvw, data, client_addr, client_port);
      serverSocket.send(reply_packet);
      System.out.println("Syn&Ack sent! Connection setup.");
    } catch (Exception e) {
      System.out.println("Connection message sent failure.");
    }
  }

  //TODO need to check time instance
  private static Arraylist<Long> checktimeout() {
    Arraylist<Long> tosend = new Arraylist<Long>();
    long curtime = System.currentTimeMillis();
    for (long i : timeArray) {
      if (i - curtime > 2) {
        tosend.add(i);
      }
    }
    return tosend;
  }

  private static void moveToNext() {
    //dunno
    
  }

  public static void waitData() throws Exception {
    serverSocket.receive(received_packet);
    InetAddress client_addr = received_packet.getAddress();
    int client_port = received_packet.getPort();
    byte[] recc = received_packet.getData();
    System.out.println("length of packet" + recc.length);
    byte[] header = Arrays.copyOfRange(recc, 0, 12);
    System.out.println("rawdata:" + recc);
    int seqNum = PacketProcessor.getIntSeqNum(header);
    int ackNum = PacketProcessor.getIntAckNum(header);
    int dataLen = PacketProcessor.getDataLength(header);
    int checksum = PacketProcessor.getCheckSum(header);
    boolean synFlag = PacketProcessor.getSYNFlag(header);
    boolean ackFlag = PacketProcessor.getACKFlag(header);
    boolean finFlag = PacketProcessor.getFINFlag(header);
    int rcvw = PacketProcessor.getrcvw(header);
    System.out.println("rcvw: " + rcvw);
    byte[] data = Arrays.copyOfRange(recc, 12, recc.length);
    String clientdata = new String(data, 0, data.length);
    System.out.println("Received Data: " + clientdata);
    // Find state of the client to decide how to reply the client
    String state = findState(synFlag, ackFlag, finFlag, clientdata);
    switch(state) {
      case "ConnRequest":
          // here the seqNum of reply = acknum of the client
              // the acknum of reply = seqNum + dataLen
          // we want to reply ack = true and syn = true, fin = false;
        handshake(ackNum, 0, true, true, false, rcvw, "MEISHAONVNIHAO", client_addr, client_port, serverSocket);
      case "ConnSetup" :
        continue;
        // don't know what to do yet
      case "TransferData":
          //TODO: convert received_data to sent_data
         sendData(ackNum, 0, true, true, false, rcvw, "MEISHAONVNIHAO", client_addr, client_port, serverSocket);
    }
  }

  private static void sendData(int seqNum,int ackNum,boolean ackFlag,boolean synFlag,boolean finFlag,int rcvw,String data, InetAddress client_addr, int client_port, DatagramSocket serverSocket) {

    DatagramPacket reply_packet = creatReplyPacket(seqNum, ackNum, ackFlag, synFlag, finFlag, rcvw, data, client_addr, client_port);
    pktSeqArray.add(seqNum);
    pktArray.add(reply_packet);
    timeArray.add(System.currentTimeMillis());
    lastSequence = (lastSequence + 1) % sequenceSize;
    try {
      serverSocket.send(reply_packet);
    } catch (IOException e ) {
      System.out.println("IO exeception found");
=======
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
public class Server {
  private static PacketProcessor pp = new PacketProcessor();
  private static int portnumber;
  private static DatagramSocket serverSocket;
  private static DatagramPacket received_packet;
  private static Window recvWindow;
  private static int lastAck = 0;
  private static Long lastAckTime;
  private static Long currentTime;
  /**
   ** Server Constructor
   **/
  public Server(String args[]) {
    //Check command line input length
    if (args.length != 2) {
      System.out.println("Invalid input."
       + " Sample input would be java smsengineUDP <port number> <receive window size>");
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
    if (temp_time == null || cur_pkt == null) {
      return;
    }
    if (curtime - temp_time >= 200) {
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
>>>>>>> master
    }
  }

  private static String findState(boolean synFlag, boolean ackFlag, boolean finFlag, String data) {
    if (synFlag && !ackFlag && !finFlag) {
<<<<<<< HEAD
      return "ConnRequest";
      // after this case all other cases are yy and can be changed as you wish!
    } else if (!synFlag && ackFlag && !finFlag) {
        if (data.length() != 0) {
          return "TransferData";
        } else {
          return "ConnSetup.";
        }
    } else if (finFlag && !synFlag && ackFlag) {
        return "Disconnect";
    } else {
      return "wtf";
    }
  }


  public static void main (String[ ]args) {
    Server server = new Server(args);
     //read and decode data from the client
    while (true) {
      waitData();
    }
  }


  public Server(String args[]) throws IOException {
    if (args.length != 1) {
          System.out.println("Invalid input."
          + " Sample input would be java smsengineUDP <port number> ");
         return;
      }
      //Check the validity of port number input
      try {
          portnumber = Integer.parseInt(args[0]);
      } catch (NumberFormatException e) {
          System.out.println("Invalid port number is given.");
          return;
      }

      if (portnumber <= 1024 || portnumber > 65536) {
          System.out.println("Port number should be between 1024 and 65536.");
        return;
      }
      try {
        serversocket = new DatagramSocket (portnumber);
        System.out.println("sever socket has been created, port number is: " + portnumber);
        System.out.println("listening...");
        byte[] buf = new byte[1024];
        received_packet = new DatagramPacket(buf, buf.length);
    } catch (IOException e) {
      System.out.println("IOException found");
    }
  } 


  
=======
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
      Server server = new Server(args);
      Window recvWindow =  server.getWindow();
      try {
        //initiate the server socket
        boolean running = true;
        while (running) {
          //read and decode data from the client
          System.out.println("Server running...");

          if (recvWindow.isfull()) {
            System.out.println("server receive window is full!!!");
            continue;
          }
          // check if the client site has crashed
          currentTime = System.currentTimeMillis();
          if (recvWindow.hasUnackedPkt()) {
            if (currentTime - lastAckTime > 10) {
              System.out.println("The client site has crashed");
            } 
          } else {
            if (currentTime - lastAckTime > 20) {
              System.out.println("the client site has crashed");
            }
          }

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
          // if (rcvw == 0) {
          //   continue;
          // }

          byte[] data = Arrays.copyOfRange(recc, 12, recc.length);
          String clientdata = new String(data, 0, dataLen > data.length ? data.length: dataLen);
          System.out.println("data.length:" + data.length);
          System.out.println("Received Data: " + clientdata);
          System.out.println("client dataLen:" + clientdata.length());

          // Find state of the client to decide how to reply the client
          String state = findState(synFlag, ackFlag, finFlag, clientdata);
          System.out.println("Current State: " + state);

          switch(state) {
              case "ConnRequest":
                  // here the seqNum of reply = acknum of the client
                  // the acknum of reply = seqNum + dataLen
                  // we want to reply ack = true and syn = true, fin = false;
                  handshake(ackNum, 0, true, true, false,recvWindowSize, "Hello", client_addr, client_port, serverSocket);
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
                  continue;

              case "AckRecvd":
                  // mark acked
                  try {
                    recvWindow.ackpacket(ackNum);
                    recvWindowSize = recvWindow.getfreewindow();
                    long curtime = System.currentTimeMillis();
                    System.out.println("server free window: " + recvWindowSize);
                  } catch (Exception iooe) {
                    System.out.println("Error occurs during ack packet and moving window.");
                  }
                  continue;
              case "Disconnect":
                  handshake(ackNum,0, true, false, true, recvWindowSize, "Bye", client_addr, client_port, serverSocket);
                  continue;
                  // don't know what to do yet
          }
          checktimeout(recvWindow);

        }
        serverSocket.close();
      } catch (NullPointerException e) {
        System.out.println("Server Crash: " + e);
      } catch (Exception e) {
        System.out.println("Server crashes with other errors: " + e);
      }

  }
>>>>>>> master
}