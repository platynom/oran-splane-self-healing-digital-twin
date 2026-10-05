# illegitimate/ — simulated, fabricated or contaminated

Nothing in this folder may be used as evidence in a result, a figure or a claim.

It is retained (not deleted) because:
- the simulator output is still valid for software testing and regression fixtures;
- `timesafe_derived_contaminated/` can be REGENERATED as legitimate once `pcap_ingest.py`
  extracts the real fields instead of padding with constants — the source pcaps are real.

Never join anything here with `legitimate/`: `offset_scaled_log_variance` alone
(4096 here vs 65535 there) separates the two at 100%.
