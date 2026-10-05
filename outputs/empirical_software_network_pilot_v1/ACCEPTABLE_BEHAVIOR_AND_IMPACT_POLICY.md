# Testbed Packet-Observation and Software-Impact Policy

## Scope and status

This policy applies only to the present Linux software testbed. It does not define a general O-RAN, telecom, or timing-network policy. Source identities, transport settings, and other configuration values are claims only when they are verified in retained, run-specific configuration evidence.

The archive of the replaced policy is in [documentation_correction_archive_20260913T225000Z](documentation_correction_archive_20260913T225000Z/MANIFEST.md).

## Evidence categories

Keep these categories separate in every record and interpretation.

| Category | Meaning | Permitted conclusion |
|---|---|---|
| Configured condition | A harness setting or expected-condition label. | It records what the harness was intended to apply; it is not a detector input or proof of packet behavior. |
| Packet observation | A statistic or event computed from retained packet timestamps and headers. | It supports only the stated packet observation. |
| Independently measured pre-action impact | Receiver or interface evidence captured before an action, with an independently recorded time relation. | It may support a narrowly stated software impact when its provenance and timing are verified. |
| Action | A commanded operation and its observed direct effects. | It shows that an action was issued or that a commanded interface/port state occurred; it does not prove original harm. |
| Outcome | A post-action receiver or traffic observation. | It may describe a post-action result; causal recovery requires a prospective, independently measured comparison. |

## Detector configuration (frozen for existing S14 material)

The existing detector configuration operates on **eight matched Sync/Follow_Up arrival-gap samples per block**. It records a high block when the configured arrival-gap standard-deviation threshold is exceeded. Its persistence rule is **two high, disjoint blocks within three seconds**. The blocks need not be consecutive; the rule is not an eight-packet rule and does not assert an exact one-second duration.

The `160 us` value is a provisional engineering threshold. It is not a scientifically established harm boundary. Any listed message-rate envelope is a chosen, unvalidated testbed setting, not a network norm or an acceptable-behavior standard outside this testbed.

## Source and state interpretation

The names “Master A,” “Master B,” “primary,” and “secondary” are configured labels until corroborated by run-specific source/configuration evidence. This policy makes no domain-0 identity claim and no general source-authorization claim.

`ptp4l` state strings and interface counters are observations. A commanded link-down or other control operation can produce `FAULTY` and traffic cessation as an **action effect**. Such a state cannot be used as evidence that the preceding packet condition was harmful. A receiver-state or counter observation is an independently measured pre-action impact only when it was captured before the action and its timing/provenance are verified.

## Harm and action policy

Packet observations alone do not establish harmfulness. `HARMFUL` remains `UNKNOWN` unless independent, pre-action impact evidence supports the claimed impact and the evidence can be linked to the packet observation without relying on the action itself. A detector trigger is an observation for control logic, not a harm label.

Existing S14 expected-condition labels remain raw protocol labels, not ground-truth harm labels. No numerical acceptance, harmfulness, false-alarm, sensitivity, or recovery criterion may be added retrospectively to classify already collected S14 material. A future protocol must specify such criteria before collecting independent validation data.

## Explicit limits

This work does not establish physical clock accuracy, hardware conformance, external attack attribution, or a complete O-RAN digital-twin result. It describes only packet-arrival observations and software-testbed receiver/action/outcome evidence within their recorded limits.
