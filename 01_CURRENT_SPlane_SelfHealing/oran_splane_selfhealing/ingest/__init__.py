"""Real-data ingestion adapters (Tier 2).

Turns real / realistic S-plane timing sources into the same canonical telemetry
schema the pure-Python simulator produces, so the *same* feature extractor,
discriminator, twin, and healing loop run unchanged on real data.

Adapters:
    pcap_ingest      - PTP-over-Ethernet (Ethertype 0x88F7) packet captures.
    linuxptp_ingest  - ptp4l / pmc textual output from a real linuxptp stack.
"""
