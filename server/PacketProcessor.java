import java.net.*;
import java.io.*;
import java.net.DatagramPacket;
import java.util.Scanner;
import java.util.Iterator;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.Arrays;
import java.math.BigInteger;

/**
 * @author Yang Yang, Yufeng Wang, Mingjun Xie,　
 * @version 1.0
 * The packet processor implements the function of packing and unpacking the packet waiting to be sent 
 * and received. This file serves as the help function for reldataServer.java
 */
public class PacketProcessor {

    public PacketProcessor() {
      //
    }
    /**
    * @param s, the string input
    * @return if the string is ascii value
    * the function tests whether the string contains purely acsii value.
    **/
    private static boolean isASCII(String s) 
    {
    for (int i = 0; i < s.length(); i++) 
        if (s.charAt(i) > 127) 
            return false;
    return true;
    }
    /**
    * param data, the string input
    * param len, the prescribed length of checksum
    * return the checksum value 
    * This function that makes the checksum for given data input, which is put in the packet header
    **/
    public static int makechecksum(String data,int len){
        int sum = 0;
        for (int i = 0; i < len; i++) {
            char c = data.charAt(i);
            sum = sum +  (int)(c);
            if (sum > 0xFFFF){
                sum = (sum + 1) & (0x0000FFFF);
            }
        }
        return sum;
    }

    /**
    * the helper fucntions for unpacking the byte array
    **/
    public static boolean get1ByteBoolean(byte[] b,int index) {
      boolean flag = b[index] != 0;
      return flag;
    }

    public static int get2Bytes(byte[] b,int index1,int index2) {
      int res = (b[index1] & 0xFF) << 8 | (b[index2] & 0xFF);
      return res;
    }

    public static int getIntSeqNum(byte[] b) {
      return get2Bytes(b, 0, 1);
    }

    public static int getIntAckNum(byte[] b) {
      return get2Bytes(b, 2, 3);
    }

    public static int getDataLength(byte [] b){
      return get2Bytes(b, 4, 5);
    }

    public static int getCheckSum(byte [] b) {
      return get2Bytes(b, 6, 7);
    }

    public static boolean getACKFlag(byte[] b) {
      return get1ByteBoolean(b, 8);
    }

    public static boolean getSYNFlag(byte[] b) {
      return get1ByteBoolean(b, 9);
    }

    public static boolean getFINFlag(byte[] b) {
      return get1ByteBoolean(b, 10);
    }

    public static int getrcvw(byte[] b) {
      int rcvw = b[11] & 0xFF;
      return rcvw;
    }

    /**
    * the helper fucntions for packing the byte array
    **/
    /**
    * param seq_num, the sequence number for the packet header
    * param ack_num, the acknowledgement number for the packet header
    * param data_len, the data length for the data
    * param checksum, the checksum value of the data for comparison in the sneder side
    * param ack_flag, indicating whether the packet is a acknowledgement packet
    * param syn_flag, indicating whether the packet is a connection setup packet    
    * param fin_flag, indicating whether the packet is a connection termination packet    
    * param rcws, the window size from the sender side, if rcws falls to zero, the receiver will pause data transferring
    * param data, actual data to be packed in the packet
    * return the byte-stream of one packet
    * This function that packs parameters into a single packet and returns as the byte-stream data to the receiver
    **/
    public static byte[] pack(int seq_num,int ack_num,int data_len,int checksum,boolean ack_flag,boolean syn_flag,boolean fin_flag,int rcws,String data) throws IOException, NullPointerException{

        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        byte[] seq = intToByte(seq_num, 2);
        byte[] ack = intToByte(ack_num, 2);
        byte[] dataLen = intToByte(data_len, 2);
        byte[] check_sum = intToByte(checksum, 2);

        outputStream.write(seq);
        outputStream.write(ack);
        outputStream.write(dataLen);
        outputStream.write(check_sum);

        byte[] flags = new byte[3];
        flags[0] = (byte)(ack_flag ? 1:0);
        flags[1] = (byte)(syn_flag ? 1:0);
        flags[2] = (byte)(fin_flag ? 1:0);

        outputStream.write(flags);

        byte[] rcw = intToByte(rcws,1);
        outputStream.write(rcw);

        outputStream.write(data.getBytes());
        return outputStream.toByteArray();
    }
    /**
    * param num, rcws window size
    * param byte_size, length for the byte stream
    * return byte stream of windowsize
    * This function is the helper function for pack, creating byte-stream of the receiver window size
    **/
    private static byte[] intToByte(int num,int byte_size) {

      BigInteger bi = BigInteger.valueOf(num);
      byte[] b = bi.toByteArray();

      byte[] bytes = new byte[byte_size];
      int j = byte_size-1;
      for (int i = b.length-1; i >= 0 && j >= 0; i--) {
        bytes[j--] = b[i];
      }
      return bytes;
    }

}