#!/bin/bash
# status.sh -- one-word verdict on the foundry run, plus the numbers behind it.
cd "$(dirname "$0")"
echo "--- machine:  $(uptime | sed 's/.*up/up/')"
echo "--- log:"; tail -3 logs/foundry.log 2>/dev/null
echo "--- progress: dumps $(ls k1_corpus/*.npz 2>/dev/null | wc -l)   families $(ls k1c_runs/gauge_*.json 2>/dev/null | wc -l) of ${EXPECT:-313}   chains $(ls k1b/*_chain.npz 2>/dev/null | wc -l)"
echo "--- workers:  $(pgrep -fc k1c_warmstart) solver processes, $(pgrep -fc k1c_gauge) family processes"
echo "--- failures: $(grep -h FAILED logs/gauge_*.log 2>/dev/null | wc -l) member failures; corpus $(sort -u k1_corpus/failures.log 2>/dev/null | wc -l) distinct problems"
echo "--- last sync: $(tail -1 logs/sync.log 2>/dev/null)"
if pgrep -f k1c_gauge >/dev/null; then echo "STATUS: RUNNING";
elif tail -1 logs/foundry.log 2>/dev/null | grep -q done; then
  n=$(ls k1c_runs/gauge_*.json 2>/dev/null | wc -l)
  [ "$n" -ge "${EXPECT:-313}" ] && echo "STATUS: FINISHED" || echo "STATUS: STOPPED EARLY ($n of ${EXPECT:-313}) -- run: python k1c_heal.py, then the launch line"
else echo "STATUS: NOT RUNNING (machine restarted? the startup script should have relaunched; check logs/nohup.log)"; fi
