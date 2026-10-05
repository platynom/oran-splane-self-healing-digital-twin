import sys,time,struct
from scapy.all import Ether,Raw,sendp
# argv: iface dur src_id_hex [gap_ms]
iface,dur,src_id = sys.argv[1],int(sys.argv[2]),sys.argv[3]
gap_ms = int(sys.argv[4]) if len(sys.argv)>4 else 125
src_mac = "02:00:00:00:00:"+src_id[-2:]
def malformed(seq):
    # deliberately illegal: versionPTP=3 (must be 2), messageType 0x0F (reserved),
    # messageLength=20 (< header), control=0x63 (>5). Header per IEEE1588 but corrupted.
    h=bytearray(34)
    h[0]=0x0F                 # majorSdoId(0)|messageType 0xF (reserved/undefined)
    h[1]=0x03                 # minorVersion(0)|versionPTP=3  (ILLEGAL, must be 2)
    struct.pack_into(">H",h,2,20)     # messageLength=20 (impossibly short)
    h[4]=24                   # domainNumber 24 (in profile - isolate malformation only)
    h[20:28]=bytes.fromhex(src_id)    # spoof provisioned GM identity
    struct.pack_into(">H",h,28,2)     # sourcePortNumber=2 (separate seq stream)
    struct.pack_into(">H",h,30,seq)
    h[32]=0x63                # controlField=0x63 (>5, illegal)
    h[33]=0x7F
    return bytes(h)+bytes(bytearray(30))
t=time.time(); seq=0
while time.time()-t<dur:
    p=Ether(dst="01:1b:19:00:00:00",src=src_mac,type=0x88F7)/Raw(malformed(seq%65536))
    sendp(p,iface=iface,count=1,verbose=0); seq+=1; time.sleep(gap_ms/1000.0)
