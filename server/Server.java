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
 * @author Yufeng Wang
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
  private final static int sequenceSize = (int)Math.pow(2,16);
  private static int windowSize = sequenceSize/2;
  private static boolean[] sendSeqArray = new boolean[windowSize];
  private static int head = 0;
  private static int end = windowSize;
  private static int lastAck = 0;
  private static ArrayList<Long> timeArray;
  private static ArrayList<DatagramPacket> pktArray;
  private static int recvWindowSize;
  
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
      portnumber = Integer.parseInt(args[0]);
    } catch (NumberFormatException e) {
      System.out.println("Invalid port number is given.");
      return;
    }

    try {
      recvWindowSize = Integer.parseInt(args[1]);
    } catch (NumberFormatException e) {
      System.out.println("Invalid recvWindowSize is given.");
      return;
    }

    if (portnumber <= 1024 || portnumber > 65536) {
      System.out.println("Port number should be between 1024 and 65536.");
      return;
    }

    try {
      serverSocket = new DatagramSocket(portnumber);
      System.out.println("serverSocket is created, waiting for response");
    } catch (SocketException e) {
      System.out.println(e.getMessage());
    }

  }

  //TODO need to check time instance
  private static List<Long> checktimeout() {
    List<Long> tosend = new ArrayList<>();
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
          System.out.println("Syn&Ack sent! Connection setup.");
      } catch (IOException e) {
        System.out.println("Connection message sent failure." + e);
      } catch (Exception e) {
        System.out.println("Other Connection error" + e);
      }
  }

  private static void sendData(int seqNum,int ackNum,boolean ackFlag,boolean synFlag,boolean finFlag,int rcvw,String data, InetAddress client_addr, int client_port, DatagramSocket serverSocket) {

    try {
      DatagramPacket reply_packet = createReplyPacket(seqNum, ackNum, ackFlag, synFlag, finFlag, rcvw, data, client_addr, client_port);
      // pktArray.add(reply_packet);
      // timeArray.add(System.currentTimeMillis());
      // lastAck = (lastAck + 1) % sequenceSize;
      serverSocket.send(reply_packet);
      System.out.println("data sent");
    } catch (IOException e) {
      System.out.println("Exeception found: data sent failure." + e);
    } catch (NullPointerException e) {
      System.out.println("Something wrong with the packet." + e);
    } catch (Exception e) {
      System.out.println("Other error when sending data." + e);
    }
  }

  private static void disconnect_client(InetAddress client_addr, int client_port) {
    //
  }

  private static String findState(boolean synFlag, boolean ackFlag, boolean finFlag, String data) {
    if (synFlag && !ackFlag && !finFlag) {
        return "ConnRequest";
        // after this case all other cases are yy and can be changed as you wish!
    } else if (!synFlag && ackFlag && !finFlag) {
          return "AckRecvd";
    } else if (finFlag && !synFlag && ackFlag) {
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
      try {
        //initiate the server socket
        boolean running = true;
        while (running) {
          //read and decode data from the client
          System.out.println("Server running..." + recvWindowSize);
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

          // if rcvw == 0, then the receiver's window is full of packets
          if (rcvw == 0) {
            continue;
          }

          byte[] data = Arrays.copyOfRange(recc, 12, recc.length);
          //System.out.println(data);
          String clientdata = new String(data,0, data.length);
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
                  handshake(ackNum, 0, true, true, false, recvWindowSize, "Hello", client_addr, client_port, serverSocket);
                  continue;
              case "TransferData":
                  int server_cs = PacketProcessor.makechecksum(clientdata, clientdata.length());
                  if (server_cs == checksum) {
                    sendData(seqNum, seqNum, true, false, false, recvWindowSize, clientdata.toUpperCase(), client_addr, client_port, serverSocket);
                  } else {
                    System.out.println("server checksum: " + server_cs);
                    System.out.println("client checksum: " + checksum);
                    System.out.println("Checksum error");
                  }
                  // need to mark acked
                  continue;
              case "Disconnect":
                  continue;
                  // don't know what to do yet
          }

        }
        serverSocket.close();
      } catch (NullPointerException e) {
        System.out.println("Server Crash: " + e);
      }

  }
}