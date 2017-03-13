import java.net.*;
import java.io.*;
import java.net.DatagramPacket;
import java.util.Scanner;
import java.util.Iterator;
import java.net.SocketException;
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
    }
  }

  private static String findState(boolean synFlag, boolean ackFlag, boolean finFlag, String data) {
    if (synFlag && !ackFlag && !finFlag) {
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


  
}