import java.util.ArrayList;
import java.net.*;
import java.util.Arrays;
import java.util.*;
import java.math.*;
/**
 * @author Yufeng Wang, Mingjun Xie, Yang Yang
 * @version 1.0
 * Window class for the server. The class contains different method of getting details in the window
 * including for example the array of unacked packet, windowsize, add packet in the window, ack packet in
 * in the window, etc. In general this is a helper class like PacketProcessor for server.
 */  
public class Window {
    Long[] timer;
    boolean[] ack;
    DatagramPacket[] pkt;
    int lastAck = 0;
    int end;
    int start;
    int windowsize;
    int unacked;
    int sequenceSize = (int)Math.pow(2,16);
    int senderWindowSize = (int)Math.pow(2,10);
    /**
    * param windowsize, prescribed window size given by the command line
    * the function initialize the window
    **/
    public Window(int windowsize) {
        this.windowsize = windowsize;
        this.start = 0;
        this.end = windowsize;
        this.timer = new Long[sequenceSize];
        this.ack = new boolean[sequenceSize];
        this.pkt = new DatagramPacket[sequenceSize];
        this.unacked = 0;
    }
    //This function checks if the window has unacked packet
    public boolean hasUnackedPkt() {
        return this.unacked > 0;
    }

    //get packet from the window
    public DatagramPacket getpacket(int pktnumber) {
        return pkt[pktnumber];
    }

    //add an unacked packet into the window
    /**
    * param pktnumber, the sequence number of the packet
    * param packet, the packet needed to be added in the buffer to be acked.
    * the function adds the datagram packet in the window buffer, waiting bo be acked from the client
    **/
    public void addpacket(int pktnumber, DatagramPacket packet) {
        long millisStart = System.currentTimeMillis();
        //System.out.println(millisStart);
        if (inrange(pktnumber)) {
            this.unacked++;
        }
        if (this.pkt[pktnumber] != null) {
            this.unacked--; //duplicate packet, need to send ack again
        }
        this.ack[pktnumber] = false;
        this.pkt[pktnumber] = packet;
        this.timer[pktnumber] = millisStart;
    }
    /**
    * param pktnumber, the sequence number of the packet
    * the function acks the datagram packet in the window buffer
    **/
    //ack a packet in the window
    public void ackpacket(int pktnumber) {
        if (this.ack[pktnumber]) {
            System.out.println("Acked already");
            return;
        }
        if (this.pkt[pktnumber] == null) {
            System.out.println("No such packet received.");
            return;
        }
        if (!this.ack[pktnumber]) {
            this.pkt[pktnumber] = null;
            this.ack[pktnumber] = true;
            this.timer[pktnumber] = null;
            moveWindow();
            System.out.println("Packet acked!");
        }
    }
    /**
    * the function helps to move the window to the position of next unacked packet
    **/
    public void moveWindow() {
        int i = this.start;
        System.out.println("move window");
        while (this.ack[i]) {
            this.unacked--;
            System.out.println(i);
            this.ack[this.end] = false;
            this.start = (start + 1) % sequenceSize;
            this.end = (end + 1) % sequenceSize;
            i++;
        }
        System.out.println("Now start: " + this.start + ", end: " + this.end);
    }
    /**
    * the function checks if the window buffer is full
    **/
    public boolean isfull() {
        return unacked >= windowsize;
    }
    /**
    * param newstart, packet sequence number
    * After terminating the connection with server, refresh the window for next round of data transfer
    **/
    public void prepareNextTransfer(int newstart) {
        this.timer = new Long[sequenceSize];
        this.ack = new boolean[sequenceSize];
        this.pkt = new DatagramPacket[sequenceSize];
        newstart++;
        this.start = newstart;
        this.end = newstart + this.windowsize;
        this.end = this.end % this.sequenceSize;
        this.unacked = 0;
        System.out.println("Clear window. Window now start at " + newstart + " and end at " + this.end);
    }
    /**
    * gets the windowsize of the window buffer
    **/
    public int getwindowsize() {
        return  windowsize;
    }
    /**
    * param pktnumber, the packet number of request
    * checks the time stamp of specific packet in the window
    **/
    public Long gettimer(int pktnumber) {
        return timer[pktnumber];
    }
    /**
    * param pktnumber, the packet number of request
    * param time, current time stamp   
    * sets the time stamp of specific packet in the window
    **/
    public void settimer(int pktnumber, Long time) {
        timer[pktnumber] = time;
    }
    /**
    * param pktnumber, the packet number of request
    * gets specific ack status for a packet in the window
    **/
    public boolean getack(int pktnumber) {
        return ack[pktnumber];
    }
    /**
    * return the freewindow size
    **/
    public int getfreewindow() {
        return windowsize - unacked;
    }
    /**
    * return the time array for all packets in the window buffer
    **/
    public Long[] getTimerArray() {
        return timer;
    }
    /**
    * return the packet array for all packets in the window buffer
    **/
    public DatagramPacket[] getPktArray() {
        return pkt;
    }
    /**
    * param lastack, the latest acked pktnumber
    * This function sets the last ack ptknumber
    **/
    public void setLastAck(int lastack) {
        this.lastAck = lastack;
        return;
    }
   /**
    * return lastack, the latest acked pktnumber
    * This function gets the last ack ptknumber
    **/
    public int lastack() {
        return this.lastAck;
    }
    /**
    * return sequencesize
    * This function gets the sequence size of the packet
    **/
    public int getSequenceSize() {
        return sequenceSize;
    }
    /**
    * param pktnumber, the packetnumber from the request
    * return if packet is within the current window
    * This function checks wheter the acked packet received from the client size is still in the winow buffer
    **/
    public boolean inrange(int pktnumber) {
        if (this.start < this.end) {
            if (pktnumber < start || pktnumber > end) {
                return false;
            }
        } else {
            if (pktnumber > end && pktnumber < start) {
                return false;
            }
        }
        return true;
    }


} 