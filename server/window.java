
import java.util.ArrayList;
import java.net.*;
import java.util.Arrays;
import java.util.*;


public class window {
	ArrayList<Long> timer;
	ArrayList<Boolean> ack;
	ArrayList<DatagramPacket> pkt;
	int end;
	int start;
	int windowsize;
	int unacked;

	public window(int windowsize) {
		this.windowsize = windowsize;
		this.start = 0;
		this.end = 0;
		this.timer = new ArrayList<Long>();
		this.ack = new ArrayList<Boolean>(Arrays.asList(new Boolean[windowsize]));
		Collections.fill(ack, Boolean.FALSE);
		this.pkt = new ArrayList<DatagramPacket>();
		this.unacked = 0;
	}

	//get packet from the window
	public DatagramPacket getpacket(int pktnumber) {
		long millisStart = Calendar.getInstance().getTimeInMillis();
		timer.set(pktnumber, millisStart);
		return pkt.get(pktnumber);
	}

	//add an unacked packet into the window
	public void addpacket(int pktnumber, DatagramPacket packet) {
		ack.set(pktnumber, false);
		pkt.set(pktnumber, packet);
		long millisStart = Calendar.getInstance().getTimeInMillis();
		timer.set(pktnumber, millisStart); 
		this.unacked++;
		this.end++;
		this.end++;
		this.windowsize--;
	}
	//ack a packet in the window
	public void ackpacket(int pktnumber) {
		pkt.set(pktnumber, null);
		ack.set(pktnumber, true);
		timer.set(pktnumber, null);
		this.unacked--;
		this.start++;
		this.windowsize++;
	}

	//check if windowsize if full of unacked?
	public Boolean isfull() {
		return unacked >= windowsize;

	}
	public int getwindowsize() {
		return  windowsize;
	}

	public Long gettimer(int pktnumber) {
		return timer.get(pktnumber);
	}

	public Boolean getack(int pktnumber) {
		return ack.get(pktnumber);
	}


} 
