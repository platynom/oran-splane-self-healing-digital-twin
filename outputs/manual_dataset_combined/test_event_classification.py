from types import SimpleNamespace
import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('ec',Path(__file__).with_name('append_event_classification.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def x(i=b'12345678',p=1):return SimpleNamespace(grandmaster_identity=i,grandmaster_priority1=p,grandmaster_clock_class=2,grandmaster_clock_accuracy=3,offset_scaled_log_variance=4,grandmaster_priority2=5,steps_removed=6,time_source=7)
d={};q=(0,2,24,'source')
assert m.classify(d,q,1,x())[0]=='NO_PREVIOUS_OBSERVATION'
assert m.classify(d,q,2,x())[0]=='C0';assert m.classify(d,q,3,x(b'abcdefgh'))[0]=='C1';assert m.classify(d,q,4,x(b'abcdefgh',9))[0]=='C2';assert m.classify(d,q,5,x(b'ABCDEFGH',10))[0]=='C3'
assert m.classify(d,(0,2,25,'source'),1,x())[0]=='NO_PREVIOUS_OBSERVATION'
assert len(m.values('a','o','d',1,1,b'',{}))==19
# Truncated/malformed Announce does not establish or advance a baseline.
bad=bytearray(64);bad[0]=11;bad[1]=2;bad[2:4]=(63).to_bytes(2,'big');bad[20:30]=b'abcdefghij'
state={};v=m.values('a','o','d',1,1,bytes.fromhex('00112233445566778899aabb88f7')+bad,state);assert v[15]=='UNKNOWN' and not state
bad[2:4]=(64).to_bytes(2,'big');bad[1]=1;v=m.values('a','o','d',2,2,bytes.fromhex('00112233445566778899aabb88f7')+bad,state);assert v[15]=='UNKNOWN' and not state
# Different capture/source/transport contexts begin independently.
assert m.classify({},(1,2,24,'source'),1,x())[0]=='NO_PREVIOUS_OBSERVATION'
print('PASS C0-C3, first observation, context boundary, non-PTP width')
