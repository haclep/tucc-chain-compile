#!/usr/bin/env bash
# sync_loop.sh -- copy results to the bucket every N minutes while the
# foundry runs, so a spot preemption loses at most one interval.
#
#   nohup ./sync_loop.sh gs://seneca-foundry 30 > logs/sync.log 2>&1 &
set -u
cd "$(dirname "$0")"
BUCKET=${1:?usage: sync_loop.sh gs://bucket [minutes]}
MIN=${2:-30}
mkdir -p logs
while true; do
  for d in k1_corpus k1b k1c_runs logs; do
    [ -d "$d" ] && gsutil -m -q rsync -r "$d" "$BUCKET/$d"
  done
  echo "$(date -u +%FT%TZ) synced" >> logs/sync.log
  sleep "$(( MIN * 60 ))"
done
