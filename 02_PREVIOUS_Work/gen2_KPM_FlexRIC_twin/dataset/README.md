# Dataset Folder

This folder is reserved for external datasets and dataset metadata used to improve the AI-native self-healing O-RAN digital twin.

## Current policy

Do not blindly download multi-GB or 450 GB archives into the project. Large Open RAN datasets are useful, but they should be pulled as selected subsets first.

## Useful confirmed source

### Open RAN Commercial Traffic Twinning Dataset

- Source repo: https://github.com/wineslab/open-ran-commercial-traffic-twinning-dataset
- Data landing page: https://repository.library.northeastern.edu/collections/neu:h989sz017
- Paper: https://arxiv.org/abs/2409.16217
- Why useful: contains PHY-, MAC-, and App-layer KPMs, per-UE metrics, base-station metrics, slicing settings, scheduling policies, and protocol logs.
- Best use in this project: train and benchmark anomaly detection, RCA, service-class impact scoring, per-UE views, and slice-aware self-healing logic.

## Local project outputs

The current project-generated replay dataset is:

```text
data/training/authentic_training_dataset.csv
```

The trained self-learning model artifact is:

```text
outputs/models/authentic_self_learning_model.json
```

External datasets should be downloaded here first, then normalized into `data/training/`.
