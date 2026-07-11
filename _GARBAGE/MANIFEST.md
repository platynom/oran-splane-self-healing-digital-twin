# Garbage Manifest

`_GARBAGE/` is staged for a future single deletion to reclaim C: space. Moving files here alone does not free disk space.

| Original path | New path | Why |
|---|---|---|
| `.project-python` | `_GARBAGE/regenerable/.project-python` | Python environment/cache, regenerable |
| `.venv` | `_GARBAGE/regenerable/.venv` | Python virtual environment, regenerable |
| `node_modules` | `_GARBAGE/regenerable/node_modules` | Node dependency cache/symlink, regenerable |
| `PROBLEM_STATEMENT_SPECIALIZED.md` | `_GARBAGE/old_direction/PROBLEM_STATEMENT_SPECIALIZED.md` | Superseded RIC/KPM direction doc listed by cleanup rules |
| `SPECIALIZATION_Fault_vs_Spoof_Discriminator.md` | `_GARBAGE/old_direction/SPECIALIZATION_Fault_vs_Spoof_Discriminator.md` | Superseded RIC/KPM direction doc listed by cleanup rules |
| `DIRECTION_Try_Before_You_Touch_SelfHealing.md` | `_GARBAGE/old_direction/DIRECTION_Try_Before_You_Touch_SelfHealing.md` | Superseded direction doc listed by cleanup rules |
| `Project_Direction_OnePager.docx` | `_GARBAGE/old_direction/Project_Direction_OnePager.docx` | Superseded direction doc listed by cleanup rules |
| `_local_quarantine` | `_GARBAGE/old_direction/_local_quarantine` | Superseded local quarantine folder listed by cleanup rules |
| `AI_Native_Self_Healing_with_Raghu_dataset_conclusion [Auto-saved].pptx` | `_GARBAGE/duplicates/AI_Native_Self_Healing_with_Raghu_dataset_conclusion [Auto-saved].pptx` | Auto-saved duplicate export |
| `oran_splane_selfhealing/.pytest_cache` | `_GARBAGE/regenerable/.pytest_cache` | Pytest cache, regenerable |
| `oran_splane_selfhealing/pytest-cache-files-6vkf5jih` | `_GARBAGE/regenerable/pytest-cache-files-6vkf5jih` | Pytest temporary cache directory, regenerable |
| `oran_splane_selfhealing/pytest-cache-files-uuj0w_6g` | `_GARBAGE/regenerable/pytest-cache-files-uuj0w_6g` | Pytest temporary cache directory, regenerable |
| `oran_splane_selfhealing/**/__pycache__` | `_GARBAGE/regenerable/oran_splane_selfhealing_*__pycache__` | Python bytecode caches generated during validation |
| `oran_splane_selfhealing/results/.pytest_cache` | `_GARBAGE/regenerable/oran_splane_selfhealing_results_.pytest_cache` | Pytest cache generated during validation |
| `oran_splane_selfhealing/results/pytest_tmp` | `_GARBAGE/regenerable/oran_splane_selfhealing_results_pytest_tmp` | Pytest temporary directory generated during validation |

## Archive Moves

| Original path | New path | Why |
|---|---|---|
| `oran_self_healing` | `archive/oran_self_healing` | Prior large codebase retained outside active direction |
| `oran_twin` | `archive/oran_twin` | Prior large codebase retained outside active direction |
