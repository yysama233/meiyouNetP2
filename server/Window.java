import java.util.ArrayList;
import java.net.*;
import java.util.Arrays;
import java.util.*;
import java.math.*;

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

    public Window(int windowsize) {
        this.windowsize = windowsize;
        this.start = 0;
        this.end = windowsize;
        this.timer = new Long[sequenceSize];
        this.ack = new boolean[sequenceSize];
        this.pkt = new DatagramPacket[sequenceSize];
        this.unacked = 0;
    }

    public boolean hasUnackedPkt() {
        return this.unacked > 0;
    }

    //get packet from the window
    public DatagramPacket getpacket(int pktnumber) {
        return pkt[pktnumber];
    }

    //add an unacked packet into the window
    public void addpacket(int pktnumber, DatagramPacket packet) {
        long millisStart = System.currentTimeMillis();
        //System.out.println(millisStart);
        this.unacked++; // we have new unacked packet

        if (this.pkt[pktnumber] != null) {
            this.unacked--; //duplicate packet, need to send ack again
        }
        this.ack[pktnumber] = false;
        this.pkt[pktnumber] = packet;
        this.timer[pktnumber] = millisStart;
    }

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
            this.unacked--;
            moveWindow();
            System.out.println("Packet acked!");
        }
    }

    public void moveWindow() {
        int i = this.start;
        System.out.println("move window");
        while (this.ack[i]) {
            System.out.println(i);
            this.ack[this.end] = false;
            this.start = (start + 1) % sequenceSize;
            this.end = (end + 1) % sequenceSize;
            i++;
        }
        System.out.println("Now start: " + this.start + ", end: " + this.end);
    }
    //check if windowsize if full of unacked?
    public boolean isfull() {
        return unacked >= windowsize;
    }

    public void prepareNextTransfer(int newstart) {
        this.timer = new Long[sequenceSize];
        this.ack = new boolean[sequenceSize];
        this.pkt = new DatagramPacket[sequenceSize];
        this.start = newstart;
        this.end = newstart + this.windowsize;
        this.end = this.end % this.sequenceSize;
        this.unacked = 0;
        System.out.println("Clear window. Window now start at " + newstart + " and end at " + this.end);
    }

    public int getwindowsize() {
        return  windowsize;
    }

    public Long gettimer(int pktnumber) {
        return timer[pktnumber];
    }

    public void settimer(int pktnumber, Long time) {
        timer[pktnumber] = time;
    }

    public boolean getack(int pktnumber) {
        return ack[pktnumber];
    }

    public int getfreewindow() {
        return windowsize - unacked;
    }

    public Long[] getTimerArray() {
        return timer;
    }

    public DatagramPacket[] getPktArray() {
        return pkt;
    }

    public void setLastAck(int lastack) {
        this.lastAck = lastack;
        return;
    }

    public int lastack() {
        return this.lastAck;
    }

    public int getSequenceSize() {
        return sequenceSize;
    }


} 