# Usage-limit checkpoint — streaming protocol V2

Fresh usage at checkpoint: short window 95% used (**5% remaining**); weekly window 15% used (85% remaining). The user’s <=5% safeguard stops new substantive work here. This percentage is a shared-account proxy, not an exact token meter.

Completed safely:

* Fixed V1 source-silence event overwrite and regenerated its development evaluation.
* Added V2 independent event composition, reappearance deduplication, source/capture-scoped trimming, bounded pending Sync and feature windows, timestamp regression, sequence reuse, and message/version/length rejection before state mutation.
* Focused streaming tests pass: 7 passed.

Do not treat the four V1 captures as V2 held-out evidence. On resumption above the usage floor, hash/freeze the current V2 code/config, run repeated matched fresh V2 baseline/netem/no-action/source-stop captures, validate every run, then compute run-level uncertainty. Do not start closed-loop action unless that predeclared evaluation supports a separate decision.
