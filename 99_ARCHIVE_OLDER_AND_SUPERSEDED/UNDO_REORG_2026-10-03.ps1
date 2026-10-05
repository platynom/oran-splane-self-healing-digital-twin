# Restores every move made on 2026-10-03. Run from PowerShell inside the project folder:
#   powershell -ExecutionPolicy Bypass -File .\99_ARCHIVE_OLDER_AND_SUPERSEDED\UNDO_REORG_2026-10-03.ps1
Set-Location (Split-Path -Parent $PSScriptRoot)
$p=Split-Path -Parent '_ARCHIVE_2026-09-21'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\earlier_cleanup_2026-09-21' -Destination '_ARCHIVE_2026-09-21'
$p=Split-Path -Parent 'outputs\01a05304-85ec-7bf1-ab63-004ba085fffe'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\build_scratch\dataset_encyclopedia_build_2026-08-31' -Destination 'outputs\01a05304-85ec-7bf1-ab63-004ba085fffe'
$p=Split-Path -Parent '.codex_review'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\build_scratch\codex_review' -Destination '.codex_review'
$p=Split-Path -Parent '.codex-finalizer-v6'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\build_scratch\codex-finalizer-v6' -Destination '.codex-finalizer-v6'
$p=Split-Path -Parent '.codex-finalizer'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\build_scratch\codex-finalizer' -Destination '.codex-finalizer'
$p=Split-Path -Parent '.codex-build-v6'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\build_scratch\codex-build-v6' -Destination '.codex-build-v6'
$p=Split-Path -Parent '.codex_build'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\build_scratch\codex_build' -Destination '.codex_build'
$p=Split-Path -Parent 'RECYCLE_MANIFEST.md'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\agent_handoffs_and_old_plans\RECYCLE_MANIFEST_2026-07-27.md' -Destination 'RECYCLE_MANIFEST.md'
$p=Split-Path -Parent 'REORG_PLAN.md'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\agent_handoffs_and_old_plans\REORG_PLAN_2026-07-24.md' -Destination 'REORG_PLAN.md'
$p=Split-Path -Parent 'HANDOFF_PROMPT.md'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\agent_handoffs_and_old_plans\HANDOFF_PROMPT_2026-09-17.md' -Destination 'HANDOFF_PROMPT.md'
$p=Split-Path -Parent 'ORAN_Data_Provenance_Verification.pdf'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\august_ML_pipeline_results_withdrawn\ORAN_Data_Provenance_Verification_2026-08-22.pdf' -Destination 'ORAN_Data_Provenance_Verification.pdf'
$p=Split-Path -Parent 'TEAM_REPORT.pdf'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\august_ML_pipeline_results_withdrawn\TEAM_REPORT_2026-08-06.pdf' -Destination 'TEAM_REPORT.pdf'
$p=Split-Path -Parent 'TEAM_REPORT.md'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\august_ML_pipeline_results_withdrawn\TEAM_REPORT_2026-08-07.md' -Destination 'TEAM_REPORT.md'
$p=Split-Path -Parent 'ORAN_SPlane_Technical_Report.pdf'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\august_ML_pipeline_results_withdrawn\ORAN_SPlane_Technical_Report_2026-08-07.pdf' -Destination 'ORAN_SPlane_Technical_Report.pdf'
$p=Split-Path -Parent 'ORAN_Project_Results.xlsx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\august_ML_pipeline_results_withdrawn\ORAN_Project_Results_2026-08-16.xlsx' -Destination 'ORAN_Project_Results.xlsx'
$p=Split-Path -Parent 'ORAN_Project_Walkthrough.pdf'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\documents_2026-09-20_superseded_by_09-29\ORAN_Project_Walkthrough_2026-09-17.pdf' -Destination 'ORAN_Project_Walkthrough.pdf'
$p=Split-Path -Parent 'Claude outputs'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\documents_2026-09-20_superseded_by_09-29\Claude_outputs_copy_2026-09-21' -Destination 'Claude outputs'
$p=Split-Path -Parent 'ORAN_SPlane_AUDIT_AND_CORRECTIONS_2026-09-20.pdf'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\documents_2026-09-20_superseded_by_09-29\ORAN_SPlane_AUDIT_AND_CORRECTIONS_2026-09-20.pdf' -Destination 'ORAN_SPlane_AUDIT_AND_CORRECTIONS_2026-09-20.pdf'
$p=Split-Path -Parent 'ORAN_SPlane_Testbed_Configuration_Reference.pdf'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\documents_2026-09-20_superseded_by_09-29\ORAN_SPlane_Testbed_Configuration_Reference.pdf' -Destination 'ORAN_SPlane_Testbed_Configuration_Reference.pdf'
$p=Split-Path -Parent 'ORAN_SPlane_Master_Test_Catalogue.pdf'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\documents_2026-09-20_superseded_by_09-29\ORAN_SPlane_Master_Test_Catalogue.pdf' -Destination 'ORAN_SPlane_Master_Test_Catalogue.pdf'
$p=Split-Path -Parent 'ORAN_SPlane_Parameter_Fault_Matrix_CORRECTED_2026-09-28.xlsx.inspect.ndjson'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\build_scratch\ORAN_SPlane_Parameter_Fault_Matrix_CORRECTED_2026-09-28.xlsx.inspect.ndjson' -Destination 'ORAN_SPlane_Parameter_Fault_Matrix_CORRECTED_2026-09-28.xlsx.inspect.ndjson'
$p=Split-Path -Parent 'ORAN_SPlane_Parameter_Fault_Matrix_CORRECTED_2026-09-28.xlsx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\documents_2026-09-20_superseded_by_09-29\ORAN_SPlane_Parameter_Fault_Matrix_CORRECTED_2026-09-28.xlsx' -Destination 'ORAN_SPlane_Parameter_Fault_Matrix_CORRECTED_2026-09-28.xlsx'
$p=Split-Path -Parent 'ORAN_SPlane_Parameter_Fault_Matrix.xlsx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\documents_2026-09-20_superseded_by_09-29\ORAN_SPlane_Parameter_Fault_Matrix.xlsx' -Destination 'ORAN_SPlane_Parameter_Fault_Matrix.xlsx'
$p=Split-Path -Parent 'ORAN_SPlane_Attack_vs_Benign_Classification.xlsx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\documents_2026-09-20_superseded_by_09-29\ORAN_SPlane_Attack_vs_Benign_Classification.xlsx' -Destination 'ORAN_SPlane_Attack_vs_Benign_Classification.xlsx'
$p=Split-Path -Parent 'ORAN_Fault_Detectability.xlsx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\documents_2026-09-20_superseded_by_09-29\ORAN_Fault_Detectability.xlsx' -Destination 'ORAN_Fault_Detectability.xlsx'
$p=Split-Path -Parent 'ORAN_SPlane_PRISM_Review_1.pptx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\decks_superseded\ORAN_SPlane_PRISM_Review_v1_duplicate.pptx' -Destination 'ORAN_SPlane_PRISM_Review_1.pptx'
$p=Split-Path -Parent 'ORAN_SPlane_PRISM_Review.pptx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\decks_superseded\ORAN_SPlane_PRISM_Review_v1_2026-09-21.pptx' -Destination 'ORAN_SPlane_PRISM_Review.pptx'
$p=Split-Path -Parent 'ORAN_PRISM_Presenter_Guide.pdf'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\decks_superseded\ORAN_PRISM_Presenter_Guide_2026-08-17.pdf' -Destination 'ORAN_PRISM_Presenter_Guide.pdf'
$p=Split-Path -Parent 'ORAN_PRISM_Review.pptx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\decks_superseded\ORAN_PRISM_Review_2026-08-17.pptx' -Destination 'ORAN_PRISM_Review.pptx'
$p=Split-Path -Parent 'V4_DECK_FACT_CHECK_2026-09-28.md'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\verification_records\V4_DECK_FACT_CHECK_2026-09-28.md' -Destination 'V4_DECK_FACT_CHECK_2026-09-28.md'
$p=Split-Path -Parent '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\V5_VERIFICATION_LOG.md'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\verification_records\V5_VERIFICATION_LOG.md' -Destination '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\V5_VERIFICATION_LOG.md'
$p=Split-Path -Parent '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\V5_SELFCHECK.md'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\verification_records\V5_SELFCHECK.md' -Destination '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\V5_SELFCHECK.md'
$p=Split-Path -Parent '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\V5_DISAGREEMENTS.md'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\verification_records\V5_DISAGREEMENTS.md' -Destination '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\V5_DISAGREEMENTS.md'
$p=Split-Path -Parent '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\V5_CHANGELOG.md'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\verification_records\V5_CHANGELOG.md' -Destination '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\V5_CHANGELOG.md'
$p=Split-Path -Parent '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v7_FINAL.pptx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\decks_superseded\ORAN_SPlane_PRISM_Review_v7_FINAL_pre-PowerPoint-resave_0641.pptx' -Destination '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v7_FINAL.pptx'
$p=Split-Path -Parent '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v6.pptx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\decks_superseded\ORAN_SPlane_PRISM_Review_v6.pptx' -Destination '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v6.pptx'
$p=Split-Path -Parent '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v5.pptx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\decks_superseded\ORAN_SPlane_PRISM_Review_v5.pptx' -Destination '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v5.pptx'
$p=Split-Path -Parent '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v4.pptx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\decks_superseded\ORAN_SPlane_PRISM_Review_v4.pptx' -Destination '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v4.pptx'
$p=Split-Path -Parent '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v3.pptx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\decks_superseded\ORAN_SPlane_PRISM_Review_v3.pptx' -Destination '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v3.pptx'
$p=Split-Path -Parent '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v2.pptx'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '99_ARCHIVE_OLDER_AND_SUPERSEDED\decks_superseded\ORAN_SPlane_PRISM_Review_v2.pptx' -Destination '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES\ORAN_SPlane_PRISM_Review_v2.pptx'
$p=Split-Path -Parent 'deliverables'; if($p -and -not (Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p | Out-Null}
Move-Item -LiteralPath '00_LATEST_PRESENTED_DECK_AND_DELIVERABLES' -Destination 'deliverables'
