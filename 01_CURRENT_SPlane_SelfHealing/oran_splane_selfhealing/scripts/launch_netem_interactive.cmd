@echo off
wsl -d Ubuntu-22.04 -- bash -lc "cd '/mnt/c/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin/01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing' && bash scripts/run_netem_interactive_wsl.sh 2>&1 | tee results/tier2/netem_interactive.log"
echo.
echo Window will stay open. Press any key to close after reviewing output.
pause >nul
