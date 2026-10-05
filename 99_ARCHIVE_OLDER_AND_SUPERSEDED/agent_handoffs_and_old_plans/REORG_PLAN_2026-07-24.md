# Reorganization Dry-Run Plan

**Goal:** one folder in Documents (this one), internally split into CURRENT vs PREVIOUS. Nothing deleted except confirmed redundant copies and staged garbage (only with your OK).

## Target structure

```
AI-Native Self-Healing O-RAN Network using a Digital Twin/
├── 01_CURRENT_SPlane_SelfHealing/
│   ├── oran_splane_selfhealing/        (active code)
│   ├── deliverables/                   (July review PDFs + decks)
│   ├── planning/                       (direction + handoff docs)
│   └── literature-survey/              (shared research)
├── 02_PREVIOUS_Work/
│   ├── gen1_RRC_PPO/                   (earliest: RRC + PPO RL agent)
│   └── gen2_KPM_FlexRIC_twin/          (KPM/FlexRIC general digital twin)
├── README.md                           (NEW: explains the split)
└── [repo infra stays at root: .git, .gitignore, .vscode, Dockerfile, etc.]
```

## 01_CURRENT_SPlane_SelfHealing/

**Code:** `oran_splane_selfhealing/`

**deliverables/** (July, S-plane): Novelty_and_Contribution.pdf, Part1_Novelty.pdf, Part2_Hardware_Implementation.pdf, References_OnePager.pdf, Review_Questions_and_Solutions.pdf, Step_by_Step_Completed.pdf, System_Explained_Walkthrough.pdf, Project_FullReview_Presentation.pdf/.pptx/_v2.pptx/.inspect.ndjson, ORAN_SPlane_SelfHealing_Presentation.pptx, Project_Proposal_Fronthaul_SelfHealing.pdf

**planning/**: TWO_DIRECTIONS_Worked_Comparison.md, ORAN_BROAD_PROBLEM_SCAN.md, HANDOFF_CODEX_MASTER_PROMPT.md, HANDOFF_CODEX_PPT_PROMPT.md, VOICE_AI_TUTOR_PROMPT.md

**literature-survey/** (moved whole)

## 02_PREVIOUS_Work/

**gen1_RRC_PPO/**: `archive/oran_self_healing/` (the RRC/PPO codebase). The external `Documents\oran_self_healing (1)\` is a subset copy of this — it will be removed, not duplicated (files hash-checked first; anything different is preserved here).

**gen2_KPM_FlexRIC_twin/**: `archive/oran_twin/`, live_backend.py, xapp_runner.py, serve_app.py, run_demo.py, tools/, scripts/, web/, docs/, outputs/, dataset/, assets/, README.md (old), PROJECT_INDEX.md, ENVIRONMENT.md, EXTERNAL_TOOLS_AND_DATASETS.md, voice.txt, Raghu_1.pptx, Raghu_2.pptx, AI_Native_Self_Healing_with_Raghu_opening_slides.pptx, AI_Native_Self_Healing_with_Raghu_dataset_conclusion.pptx

## Stays at root (repo infrastructure)
.git/, .gitignore, .dockerignore, .vscode/, Dockerfile, docker-compose.yml, requirements.txt (+ new README.md)

## Needs your decision
1. **configs/ and data/** — you picked "shared research → CURRENT," but on inspection these are June KPM-twin assets and the current S-plane code does NOT use them (it has its own config/ and dataset/ inside). **Recommendation: put them in gen2_KPM_FlexRIC_twin (PREVIOUS).** Say the word if you'd rather force them into CURRENT.
2. **_GARBAGE/ (796 MB)** — staged-for-deletion caches/duplicates. Leave at root, or delete now to reclaim space?
3. **Stale lock file** `.~lock.Project_FullReview_Presentation.pdf#` — means that PDF is open somewhere. Recommend closing it and deleting the lock.
