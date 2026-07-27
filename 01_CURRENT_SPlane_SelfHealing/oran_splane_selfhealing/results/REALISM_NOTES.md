# Realism hardening notes (why the numbers are earned, not perfect)

The first build produced a **1.000** discriminator accuracy, which is a red flag
(overfitting on a too-easy simulator). The simulator/injectors were hardened so the
classifier has to work for its score:

- **Removed label giveaways.** Spoof/replay no longer stamp a "ForgedSync"/"ReplaySync"
  message type — a real attack looks like normal Sync/Announce and must be caught by
  statistics, not a literal label.
- **Overlapping magnitudes.** Attack offset magnitudes now overlap benign-fault
  magnitudes (stealthy attacks exist); per-run severity is randomised.
- **Evasive mimicry.** ~60% of attacks forge a benign-fault signature (fake SyncE
  quality / GNSS-loss / holdover) to evade the categorical flags.
- **Attacks during congestion.** ~55% of attacks add background path-delay, so PDV is
  no longer a clean fault-only tell.
- **Sensor noise.** Telemetry values and flags are read through observation noise, so
  the fault signatures are not perfectly observable (as in a real KPM stream).

**Result after hardening:** H0-vs-H1 accuracy ~0.98–0.99 with genuine confusion errors
(not 1.000), ROC-AUC ~0.999 — consistent with the peer-reviewed TIMESAFE detector (97.5%).
The governed loop likewise now shows realistic imperfection (recovery ~0.95, wrong-action
~0.05) rather than a perfect 1.0/0.0.

**Honest caveat for the viva:** this is a physics-based emulation, not hardware-timestamped
PTP. The number is defensible because faults and attacks genuinely have different physical
signatures; errors concentrate on the evasive/mimicking attacks, which is the hard and
interesting case.
