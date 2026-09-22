#!/usr/bin/env bash
# run_foundry.sh -- one machine, one atlas phase, start to finish. Resumable:
# rerun the same command after any interruption (spot preemption, a crash,
# a reboot) and it continues where it stopped. Dumps already on disk are
# skipped, members with a summary are skipped, members with a checkpoint
# resume.
#
#   PHASE=1 JOBS=54 GATE=1e-16 PLAN=quick BUCKET=gs://seneca-foundry ./run_foundry.sh
#
# Runs from the directory it lives in (the checkout), logs to logs/.
set -u
cd "$(dirname "$0")"
PHASE=${PHASE:-1}
JOBS=${JOBS:-$(( $(nproc) > 2 ? $(nproc) - 2 : 1 ))}
GATE=${GATE:-1e-16}
PLAN=${PLAN:-quick}
SHARDS=${SHARDS:-3}          # gauge processes running side by side; a quick
                             # plan has 24 members, so one process alone
                             # cannot keep 50 cores busy
BUCKET=${BUCKET:-}
DEADLINE=${DEADLINE:-3600}
PY=${PY:-python3}
export K1_GATE="$GATE"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p k1_corpus k1c_runs k1b logs

echo "=== $(date -u +%FT%TZ) foundry phase $PHASE  jobs $JOBS  gate $GATE  plan $PLAN" | tee -a logs/foundry.log

# 1. Hamiltonian dumps (minutes to a few hours for a whole phase).
#    Two BLAS threads per CASSCF; half as many jobs as cores.
CJ=$(( JOBS / 2 > 0 ? JOBS / 2 : 1 ))
$PY k1c_corpus.py atlas.json --phase "$PHASE" -j "$CJ" --threads 2 >> logs/corpus.log 2>&1
echo "corpus: $(ls k1_corpus/*.npz 2>/dev/null | wc -l) dumps on disk" | tee -a logs/foundry.log
[ -s k1_corpus/failures.log ] && echo "corpus problems: $(wc -l < k1_corpus/failures.log) (see k1_corpus/failures.log)" | tee -a logs/foundry.log

# 2. Families: every dump of the phase, smallest sector first, split over
#    SHARDS gauge processes that never share a system, JOBS members in
#    total. Each member is one process; a member that hits DEADLINE
#    seconds checkpoints and is resumed.
PER=$(( JOBS / SHARDS > 0 ? JOBS / SHARDS : 1 ))
for k in $(seq 0 $(( SHARDS - 1 ))); do
  $PY k1c_gauge.py --corpus k1_corpus --phase "$PHASE" --plan "$PLAN" -j "$PER" \
      --gate "$GATE" --deadline "$DEADLINE" --shard "$k/$SHARDS" >> "logs/gauge_$k.log" 2>&1 &
done
wait
echo "families: $(ls k1c_runs/gauge_*.json 2>/dev/null | wc -l) reported, $(ls k1b/*_chain.npz 2>/dev/null | wc -l) certified chains" | tee -a logs/foundry.log

# 3. Copy everything out. Safe to run repeatedly; only changes are sent.
if [ -n "$BUCKET" ]; then
  gsutil -m -q rsync -r k1_corpus "$BUCKET/k1_corpus"
  gsutil -m -q rsync -r k1b       "$BUCKET/k1b"
  gsutil -m -q rsync -r k1c_runs  "$BUCKET/k1c_runs"
  gsutil -m -q rsync -r logs      "$BUCKET/logs"
  echo "synced to $BUCKET" | tee -a logs/foundry.log
fi
echo "=== $(date -u +%FT%TZ) done" | tee -a logs/foundry.log
