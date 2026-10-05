import sys,time
from scapy.all import Ether,Raw,sendp
# Non-PTP background/data-plane traffic to contend with PTP at a constrained link.
# argv: iface dur burst_frames gap_ms [frame_bytes]
iface,dur,burst,gap=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])
size=int(sys.argv[5]) if len(sys.argv)>5 else 1400
# ethertype 0x0801 = NOT PTP (0x88F7); carries no PTP semantics, pure congestion load
pkt=Ether(dst="02:00:00:00:00:ff",src="02:00:00:00:00:02",type=0x0801)/Raw(b"\x00"*size)
t=time.time()
while time.time()-t<dur:
    sendp(pkt,iface=iface,count=burst,verbose=0)
    time.sleep(gap/1000.0)
