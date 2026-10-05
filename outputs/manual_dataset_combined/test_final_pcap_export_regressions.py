"""Focused mechanics tests for the streamed PCAP export (not scientific validation)."""
from types import SimpleNamespace
import importlib.util
from pathlib import Path

B=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pcapbuild',B/'build_final_pcap_consolidation.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

assert len(m.PCAP_HEADERS)==39
assert len(m.unavailable_fields('NON_PTP_OR_UNSUPPORTED_ETHERNET'))==24
assert set(m.unavailable_fields('NON_PTP_OR_UNSUPPORTED_ETHERNET'))=={'NOT_APPLICABLE'}
assert len(m.unavailable_fields('TRUNCATED_PTP_HEADER',b'\x0b'))==24
assert set(m.unavailable_fields('TRUNCATED_PTP_HEADER',b'\x0b'))=={'UNKNOWN_UNAVAILABLE'}
def msg(identity=b'12345678',p1=128):
 return SimpleNamespace(grandmaster_identity=identity,grandmaster_priority1=p1,grandmaster_clock_class=248,grandmaster_clock_accuracy=254,offset_scaled_log_variance=1,grandmaster_priority2=128,steps_removed=0,time_source=160)
prior={}; scope=(0,2,24,'sourceport')
assert m.event_for_announce(scope,msg(),prior)[0]=='NONE'
# Same source identity in another domain must not be compared to domain 24.
assert m.event_for_announce((0,2,25,'sourceport'),msg(b'abcdefgh'),prior)[0]=='NONE'
assert m.event_for_announce(scope,msg(b'abcdefgh'),prior)[0]=='advertised_GM_identity_change'
assert m.event_for_announce(scope,msg(b'abcdefgh',p1=1),prior)[0]=='advertised_clock_attribute_change'
origin=m.pcap_definition('PTP originTimestamp ns (derived)')
assert 'message-body' in origin[0] and 'distinct from the classic-PCAP capture-record timestamp' in origin[1]
assert 'packet count' in m.pcap_definition('Packet ordinal (derived)')[0]
assert 'EtherType' in m.pcap_definition('EtherType (derived)')[0]
assert 'flagField' in m.pcap_definition('PTP flags hex (derived)')[0]
assert 'portNumber' in m.pcap_definition('PTP source port (derived)')[0]
assert 'encoded' in m.original_definition('Source')[0].lower()
print('PASS: fallback widths/states and domain-scoped Announce event classification')
